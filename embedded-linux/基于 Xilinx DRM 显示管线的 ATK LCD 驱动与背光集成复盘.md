---
layout: post
title:  基于 Xilinx DRM 显示管线的 ATK LCD 驱动与背光集成复盘
date: 2025-04-02 16:12:22
categories: [Linux]
excerpt:
hide: false
---

## 1. 项目概述

提交 `f8a827267b34794a70ddcc657c218943b4f6518a` 的核心目标，是在 Zynq 平台上补齐一条可落地的 LCD 显示链路，让系统不只是“有显示相关 IP”，而是真正能够通过 Linux DRM 框架把图像送到 ATK LCD 屏，并把背光、像素时钟、屏参适配一起打通。

这次提交新增和调整的内容比较集中，但本质上不是单点驱动开发，而是一次完整的板级显示集成：

1. 新增 LCD DRM 输出驱动 [`drivers/gpu/drm/xlnx/xlnx_atk_lcd.c`](/home/user/workspace/drvlearn-linux-xlnx-5.4/drivers/gpu/drm/xlnx/xlnx_atk_lcd.c)。
2. 新增 AXI PWM 控制器驱动 [`drivers/pwm/pwm-dglnt.c`](/home/user/workspace/drvlearn-linux-xlnx-5.4/drivers/pwm/pwm-dglnt.c)，用于控制 LCD 背光。
3. 在设备树中补齐 `pl-disp`、VTC、clock wizard、PWM、LCD ID GPIO、display-timings 之间的连接关系 [`arch/arm/boot/dts/zynq-phosphor-7010-user.dtsi`](/home/user/workspace/drvlearn-linux-xlnx-5.4/arch/arm/boot/dts/zynq-phosphor-7010-user.dtsi)。
4. 在 Kconfig、Makefile 和 defconfig 中把相关模块配置串起来。
5. 调整 clock wizard 驱动 [`drivers/clk/clk-xlnx-clock-wizard.c`](/home/user/workspace/drvlearn-linux-xlnx-5.4/drivers/clk/clk-xlnx-clock-wizard.c)，保证 LCD 像素时钟可以被动态设置。

如果只看新增的 `xlnx_atk_lcd.c`，会觉得这只是一个 DRM encoder/connector 驱动；但结合设备树和时钟、PWM 代码一起看，就能发现这次提交真正完成的是“显示链路闭环”。

## 2. 这个提交做了什么

从系统视角看，这次提交建立的是下面这条显示路径：

```text
用户空间 / fbdev / DRM framebuffer
        ->
Xilinx DRM master
        ->
xlnx,pl-disp 负责 CRTC/plane 和 DMA 取帧
        ->
VTC 生成时序
        ->
atk,atk_dpi 作为 encoder/connector 输出 RGB LCD
        ->
LCD 屏

同时：
- clock wizard 提供 lcd_pclk
- Digilent AXI PWM 提供背光 PWM
- lcdID GPIO 决定使用哪组 display timing
```

这条链路里，前级显示数据流主要由 Xilinx DRM 框架和 `xlnx,pl-disp` 承担，本次新增的 LCD 驱动更多是“把屏端接上去”，并根据实际硬件补齐两个关键外设：

1. 像素时钟。
2. 背光控制。

这也是工程里很典型的一类问题：画面输出不只取决于 framebuffer 是否正常，还受到时钟、时序、背光、板级连线和设备树拓扑的共同影响。

## 3. 整体架构：这条 DRM 显示链路是怎样搭起来的

### 3.1 在 Xilinx DRM 体系里，各模块分别扮演什么角色

这次提交并没有自己从零实现一个完整 DRM master，而是接入已有的 Xilinx DRM 管线。

其中前级显示控制由 [`drivers/gpu/drm/xlnx/xlnx_pl_disp.c`](/home/user/workspace/drvlearn-linux-xlnx-5.4/drivers/gpu/drm/xlnx/xlnx_pl_disp.c) 提供。它在 probe 阶段会：

1. 申请 DMA channel。
2. 获取 VTC bridge。
3. `component_add()` 注册自己。
4. 通过 `xlnx_drm_pipeline_init()` 创建逻辑 master 设备。

对应代码路径大致如下：

```c
ret = component_add(dev, &xlnx_pl_disp_component_ops);
...
xlnx_pl_disp->master = xlnx_drm_pipeline_init(pdev);
```

也就是说，`xlnx,pl-disp` 负责 CRTC/plane 这部分“出图核心”，而这次新增的 `atk,atk_dpi` 负责输出端的 encoder/connector。两者不是替代关系，而是上下游关系。

### 3.2 `atk,atk_dpi` 如何并入 DRM pipeline

新增驱动 [`drivers/gpu/drm/xlnx/xlnx_atk_lcd.c`](/home/user/workspace/drvlearn-linux-xlnx-5.4/drivers/gpu/drm/xlnx/xlnx_atk_lcd.c) 同样使用了 component framework：

```c
static const struct component_ops atk_dpi_component_ops = {
	.bind = atk_dpi_bind,
	.unbind = atk_dpi_unbind,
};
```

probe 时先完成板级资源初始化，随后 `component_add()`；等逻辑 master 统一绑定时，再在 `atk_dpi_bind()` 中把 encoder 和 connector 注册到 DRM 设备中。

这意味着驱动初始化分成两层：

1. `probe()` 阶段先把本设备依赖的时钟、PWM、屏参准备好。
2. `bind()` 阶段再把自己作为 DRM 输出对象挂到整条显示管线里。

这种模式非常适合多 IP 组成的显示系统，因为单个设备初始化完成，并不代表整条显示管线已经就绪。

### 3.3 设备树如何描述这条连接关系

这次设备树的关键节点集中在 [`arch/arm/boot/dts/zynq-phosphor-7010-user.dtsi`](/home/user/workspace/drvlearn-linux-xlnx-5.4/arch/arm/boot/dts/zynq-phosphor-7010-user.dtsi)。

前级显示节点：

```dts
drm_pl_disp_lcd {
	compatible = "xlnx,pl-disp";
	dmas = <&lcd_out_v_frmbuf_rd_0 0>;
	dma-names = "dma0";
	xlnx,vformat = "BG24";
	xlnx,bridge = <&lcd_out_lcd_vtc>;
	...
};
```

LCD 输出节点：

```dts
atk_lcd_drm{
	compatible = "atk,atk_dpi";
	clocks = <&clk_wiz_0 0>;
	clock-names = "lcd_pclk";
	pwms = <&lcd_out_lcd_pl_pwm 0 5000000>;
	lcdID = <...>;
	...
};
```

两者通过 OF graph 中的 `endpoint` 互连：

```dts
pl_disp_crtc_lcd:endpoint {
	remote-endpoint = <&lcd_encoder>;
};

lcd_encoder: endpoint {
	remote-endpoint = <&pl_disp_crtc_lcd>;
};
```

这也是 `atk_dpi_bind()` 里可以调用 `drm_of_find_possible_crtcs()` 的基础。驱动并不是手工指定“我接哪个 CRTC”，而是根据设备树 graph 拓扑自动找到上游输出源。

## 4. 关键实现一：ATK LCD DRM 驱动如何把屏接进 DRM

### 4.1 私有数据结构保存了哪些核心资源

驱动的主体结构体很简洁：

```c
struct atk_dpi {
	struct device *dev;
	struct drm_encoder encoder;
	struct drm_connector connector;
	struct videomode *vm;
	struct clk *pclk;
};
```

这里面最关键的资源有四类：

1. `encoder`：向 DRM 描述“如何把像素数据送到输出接口”。
2. `connector`：向 DRM 描述“外部接了一个什么显示终端”。
3. `vm`：从设备树解析出的屏幕时序。
4. `pclk`：LCD 像素时钟。

这类驱动的职责并不是搬运 framebuffer，而是把“显示模式”和“输出链路控制”接入 DRM。

### 4.2 `probe()` 阶段真正完成了哪些工作

`atk_dpi_probe()` 的逻辑很有代表性，基本体现了板级显示驱动的初始化顺序：

1. 分配 `atk_dpi` 私有结构。
2. 获取 `lcd_pclk` 时钟。
3. 调用 `atkencoder_init_dt()` 解析 LCD ID 和 display timing。
4. 设置像素时钟频率并使能。
5. 获取 PWM 并打开背光。
6. `component_add()`，等待进入 DRM bind 阶段。

这一段很值得注意，因为它说明该驱动并不是等 modeset 时才第一次准备硬件，而是在 probe 阶段就先把最基础的出屏条件准备好了。

对应代码主干如下：

```c
dpi->pclk = devm_clk_get(dev, "lcd_pclk");
...
ret = atkencoder_init_dt(dpi);
...
clk_set_rate(dpi->pclk, dpi->vm->pixelclock);
ret = clk_prepare_enable(dpi->pclk);
...
pwm = devm_pwm_get(dev, NULL);
...
pwm_config(pwm, 5000000, 5000000);
pwm_enable(pwm);
...
ret = component_add(dev, &atk_dpi_component_ops);
```

这里能看出作者的工程取向非常明确：先保证屏能亮，再把它规范地接到 DRM 里。

### 4.3 `bind()` 阶段如何注册 encoder/connector

在 `atk_dpi_bind()` 中，驱动完成了标准 DRM 输出对象注册：

```c
drm_encoder_init(drm_dev, encoder, &atk_dpi_encoder_funcs,
		 DRM_MODE_ENCODER_DPI, NULL);
drm_encoder_helper_add(encoder, &atk_dpi_encoder_helper_funcs);

ret = drm_connector_init(drm_dev, &dpi->connector,
			 &atk_dpi_connector_funcs,
			 DRM_MODE_CONNECTOR_DPI);
...
drm_connector_helper_add(&dpi->connector,
			 &atk_dpi_connector_helper_funcs);
drm_connector_register(&dpi->connector);
drm_connector_attach_encoder(&dpi->connector, encoder);
```

这里使用的对象类型很贴合这块屏的接口形式：

1. encoder 类型是 `DRM_MODE_ENCODER_DPI`。
2. connector 类型是 `DRM_MODE_CONNECTOR_DPI`。

同时，驱动会遍历当前节点下的 `ports`，通过 `drm_of_find_possible_crtcs()` 推导上游 CRTC：

```c
encoder->possible_crtcs |= drm_of_find_possible_crtcs(drm_dev, port);
```

这一步的意义在于把“设备树连线关系”转成“DRM 对象可连接关系”。

### 4.4 模式设置时，驱动做了什么

驱动的 connector helper 里提供了 `get_modes` 和 `mode_valid`：

1. `lcd_get_modes()`：把 `videomode` 转成 `drm_display_mode`，并标记为 `PREFERRED`。
2. `lcd_mode_valid()`：当前实现直接返回 `MODE_OK`，表示默认接受这组模式。

核心代码如下：

```c
drm_display_mode_from_videomode(dpi->vm, mode);
drm_mode_set_name(mode);
mode->type = DRM_MODE_TYPE_DRIVER | DRM_MODE_TYPE_PREFERRED;
drm_mode_probed_add(connector, mode);
```

encoder helper 则负责在 modeset 时真正配置时钟：

```c
pclk_rate = mode->clock * 1000;
ret = clk_set_rate(dpi->pclk, pclk_rate);
```

在 `enable()` / `disable()` 中，驱动只做一件事：控制像素时钟开关。

这说明该驱动采取的是一种很轻量的输出端实现思路：

1. 模式信息来自设备树。
2. 模式切换的实质动作是像素时钟切换。
3. 时序波形由前级 VTC 等模块负责。

## 5. 关键实现二：LCD ID 与多屏时序适配

### 5.1 为什么这里要做 LCD ID 识别

这次驱动没有把屏幕参数写死，而是通过三根 GPIO 读取 LCD 硬件 ID，再映射到不同的 timing 配置。这个策略很实用，因为同一块板卡可能接不同尺寸、不同分辨率的 ATK LCD 模组。

驱动里定义了几种屏型号：

```c
enum ATK_LCD_TYPE {
	ATK4342 = 0,
	ATK4384 = 4,
	ATK7084 = 1,
	ATK7016 = 2,
	ATK1018 = 5,
};
```

在 `atkencoder_init_dt()` 中，驱动依次读取 `lcdID` 对应的三根 GPIO：

```c
lcd_id |= (gpio_get_value_cansleep(gpios[i]) << i);
```

随后再根据 `lcd_id` 决定使用哪一组 display timing。

### 5.2 设备树里的 `display-timings` 如何落到实际模式

设备树中预定义了四组时序：

1. `timing0`：480x272。
2. `timing1`：800x480。
3. `timing2`：1024x600。
4. `timing3`：1280x800。

驱动通过 `of_get_videomode()` 按索引取出目标模式：

```c
ret = of_get_videomode(dn, vm, display_timing);
```

这里的设计很板级工程化。驱动本身不需要知道每个字段如何手工拼接，它只负责：

1. 读硬件 ID。
2. 选 timing 索引。
3. 把 timing 交给 DRM mode 层。

这样既避免把大量屏参硬编码在 C 文件里，也方便后续通过 DTS 调整时序。

### 5.3 这段实现里体现出的项目经验

有几个细节很像真实项目里常见的处理方式：

1. 如果读不到 GPIO 或 GPIO 申请失败，会回退到 `ATK7084`，即默认 7 寸 800x480。
2. `ATK4384` 和 `ATK7084` 共用同一组 800x480 时序。
3. 读取完 ID 后，又把这几根引脚切成输出低电平。

这说明作者面对的不是一个“理论上只有一块屏”的纯净环境，而是一个实际存在多屏兼容、连线约束和默认回退策略的开发板场景。

当然，这里也埋着一些后续可优化点，例如 `lcd_id` 使用了全局变量导出，封装性一般；GPIO 模式切换的原因如果没有配套硬件文档，后续维护者理解成本会比较高。

## 6. 关键实现三：背光 PWM 为什么要单独补一个驱动

### 6.1 仅有 DRM 出图，并不等于用户能看到画面

LCD 点亮这件事，常常包含两个层面：

1. 数字视频链路正常，时序和像素数据都在跑。
2. 背光真的打开了。

如果背光没有打开，板子从现象上看依然是“黑屏”。所以本次提交除了 LCD DRM 驱动之外，还新增了 [`drivers/pwm/pwm-dglnt.c`](/home/user/workspace/drvlearn-linux-xlnx-5.4/drivers/pwm/pwm-dglnt.c)，专门驱动 Digilent AXI PWM IP。

### 6.2 PWM 控制器驱动的实现思路

这个 PWM 驱动实现的是一个典型的 PWM provider。核心结构体如下：

```c
struct dglnt_pwm_dev {
	struct device *dev;
	struct pwm_chip chip;
	struct clk *pwm_clk;
	void __iomem *base;
	unsigned int period_min_ns;
};
```

它做的事情比较直接：

1. 通过 `platform_get_resource()` 和 `devm_ioremap_resource()` 取得寄存器基地址。
2. 获取输入时钟 `pwm`。
3. 根据时钟频率计算最小周期 `period_min_ns`。
4. 注册 `pwm_chip`。
5. 在 `.config/.enable/.disable` 中把 period、duty 和使能位写到 AXI PWM 寄存器。

比如 `dglnt_pwm_config()` 的核心就是把纳秒单位的周期和占空比，换算成寄存器计数值：

```c
period = period_ns / dglnt_pwm->period_min_ns;
duty = duty_ns / dglnt_pwm->period_min_ns;

dglnt_pwm_writel(dglnt_pwm, PWM_AXI_PERIOD_REG_OFFSET, period);
dglnt_pwm_writel(dglnt_pwm, PWM_AXI_DUTY_REG_OFFSET + (4 * pwm->hwpwm),
		 duty);
```

这类驱动的重点不在复杂算法，而在把“PWM 子系统抽象”准确映射到具体硬件寄存器。

### 6.3 LCD 驱动如何消费 PWM

在 LCD DRM 驱动中，背光控制很简单：

```c
pwm = devm_pwm_get(dev, NULL);
...
pwm_config(pwm, 5000000, 5000000);
pwm_enable(pwm);
```

这里把占空比和周期都配置成 `5000000ns`，等价于 100% 占空比，目标就是先把背光稳定打开。这个选择非常符合 bring-up 阶段思路：先让现象稳定出现，再谈亮度控制策略。

不过从长期维护角度看，这部分仍然偏“够用型”：

1. 直接在 LCD 驱动里操作 PWM，而不是对接更完整的背光框架。
2. 使用的是较早期的 PWM API 风格。
3. `devm_pwm_get()` 后又 `pwm_free()`，资源管理风格不够统一。

## 7. 关键实现四：Clock Wizard 改动为什么对 LCD 很关键

如果只看 LCD 驱动，会看到它在 modeset 时调用：

```c
clk_set_rate(dpi->pclk, pclk_rate);
```

问题在于，这句代码要真正生效，前提是底层 `lcd_pclk` 提供者确实支持动态设置频率。本次提交对 [`drivers/clk/clk-xlnx-clock-wizard.c`](/home/user/workspace/drvlearn-linux-xlnx-5.4/drivers/clk/clk-xlnx-clock-wizard.c) 的修改，正是为了打通这件事。

从提交内容看，clock wizard 驱动做了几类与本项目直接相关的增强：

1. 兼容属性改为读取 `xlnx,speed-grade`、`xlnx,nr-outputs` 等更符合当前设备树写法的字段。
2. 允许按输出数量注册 clock output。
3. 补齐内部 multiplier/divider 时钟组织方式。
4. 让输出时钟注册、`clk_set_rate()` 和 provider 发布流程更完整。

设备树里对应的 clock 节点是：

```dts
&clk_wiz_0 {
	compatible = "xlnx,clocking-wizard";
	xlnx,nr-outputs = <1>;
};
```

LCD 驱动通过：

```dts
clocks = <&clk_wiz_0 0>;
clock-names = "lcd_pclk";
```

拿到这个时钟句柄后，就能在 mode set 阶段把像素时钟切到目标频率。对于 RGB/LCD 这类接口来说，像素时钟是否准确往往直接决定屏是否能稳定显示。

换句话说，这次 clock wizard 改动虽然不在 DRM 目录下，但它其实是 LCD 驱动能工作的前提条件之一。

## 8. 相关内核知识点

### 8.1 DRM/KMS 子系统里，这次涉及到哪些常见对象

这次提交主要涉及 DRM/KMS 子系统中的以下对象：

1. `drm_device`：整条显示管线对应的核心 DRM 设备。
2. `drm_crtc`：扫描输出控制器，负责模式生效、扫描和显示时序联动。
3. `drm_plane`：图层/帧缓冲图像源。
4. `drm_encoder`：把像素数据编码或适配到某种输出接口。
5. `drm_connector`：表示一个外部显示连接终端。
6. `drm_display_mode`：显示模式描述。

在这次工程里：

1. `xlnx,pl-disp` 更偏向提供 `CRTC + plane`。
2. `atk,atk_dpi` 更偏向提供 `encoder + connector`。

这是一种比较标准的 DRM 职责拆分。

### 8.2 这些对象通常如何初始化

在这类 SoC/FPGA 混合显示系统里，初始化一般不是单个驱动一步完成，而是多设备协同：

1. 前级显示控制器驱动先 probe。
2. 各个输出或 bridge 子设备分别 probe。
3. 它们通过 `component_add()` 注册自己。
4. 逻辑 master 根据 OF graph 拓扑在 bind 阶段把各组件拼成完整 pipeline。
5. 各子设备分别调用 `drm_encoder_init()`、`drm_connector_init()`、CRTC/plane 注册接口完成对象创建。

这也是为什么在 Xilinx DRM 代码里，经常能看到 component framework 与 DRM 初始化交织出现。

### 8.3 驱动通常如何向 DRM 子系统上报“数据或事件”

DRM 和 input 子系统很不一样。它不是通过“上报按键事件”工作的，而是通过以下方式参与系统运行：

1. 注册 mode object，例如 CRTC、plane、encoder、connector。
2. 提供可用显示模式。
3. 在 modeset / atomic 流程中配置硬件。
4. 在 enable/disable、page flip、vblank 等流程里推进显示状态变化。

本次新增的 LCD 驱动主要参与的是：

1. 提供显示模式。
2. 响应 modeset。
3. 控制像素时钟开关。

它本身并不负责帧数据搬运，也不负责产生 framebuffer。

### 8.4 PWM 子系统里相关对象的常见类型、初始化方式和数据上报方式

这次提交还涉及 PWM 子系统。这里相关对象主要有两类：

1. `pwm_chip`：PWM 控制器驱动向内核注册的 provider。
2. `pwm_device`：某一路 PWM 通道实例，供消费者驱动使用。

典型初始化流程是：

1. PWM 控制器驱动 probe。
2. 映射寄存器、获取时钟、填充 `pwm_chip`。
3. 调用 `pwmchip_add()` 注册 provider。
4. 消费者驱动通过 `pwm_get()` / `devm_pwm_get()` 取得通道。

PWM 不像 input 那样“上报事件”，更准确地说，它向子系统提供的是一组控制操作：

1. 配置周期和占空比。
2. 使能或关闭输出。

对于背光场景，上层驱动通常就是通过这些控制接口来调亮度或直接开关背光。

## 9. 调试与适配时的关注点

这类显示 bring-up 工作，最怕的是“代码看起来都对，但屏幕就是黑的”。结合本次实现，调试时我会优先关注下面几个点。

### 9.1 先确认 OF graph 是否接对

如果 `remote-endpoint` 没接对，`drm_of_find_possible_crtcs()` 就可能找不到上游 CRTC，最终导致 encoder 无法挂进正确的 DRM 管线。这个问题从代码上不一定明显，但会直接影响 bind 结果。

### 9.2 再确认像素时钟是否真的输出到了目标频率

RGB/LCD 屏的容错通常不高。若 `clk_set_rate()` 没生效，或者 clock wizard 侧没有正确重配，常见现象包括：

1. 屏幕完全无显示。
2. 图像抖动、偏移、花屏。
3. 某些分辨率能亮，另一些不能亮。

因此这次 clock wizard 改动要和 LCD 驱动一起看，不能只盯 DRM 代码。

### 9.3 `display-timings` 必须和屏参匹配

设备树里的这些字段：

1. `clock-frequency`
2. `hactive`
3. `vactive`
4. `hfront-porch`
5. `hback-porch`
6. `hsync-len`
7. `vfront-porch`
8. `vback-porch`
9. `vsync-len`

都直接决定屏的时序表现。这里最忌讳“分辨率对了就觉得没问题”，因为很多 LCD 黑屏问题本质上是 porch 或 sync 参数不对。

### 9.4 背光要单独验证

如果 DRM pipeline 正常、时钟也正常，但背光没开，表面现象还是黑屏。所以 bring-up 时最好把“背光”单独当成一个检查项：

1. PWM 寄存器有没有被写到。
2. PWM 输出是否到达背光电路。
3. 背光使能极性是否正确。

### 9.5 LCD ID 回退机制既方便，也可能掩盖问题

当前实现里，一旦 ID GPIO 获取失败，会回退到默认 800x480 配置。这在开发初期很实用，因为能尽量保证系统先出图；但到了适配阶段，也容易掩盖硬件接线错误或 GPIO 属性写错的问题。

如果屏幕型号不对、画面不稳定，除了查 timing，也要先确认是否真的读到了预期的 `lcd_id`。

## 10. 还有哪些可优化点

这次提交已经把 LCD 显示链路跑通了，但如果继续往工程化和可维护性推进，仍有不少地方可以优化。

### 10.1 LCD 驱动的资源管理还能更统一

当前代码中已经大量使用 `devm_` 接口，但也存在：

1. `devm_pwm_get()` 后又调用 `pwm_free()`。
2. `devm_kzalloc()` 分配的对象在错误路径上又手工 `devm_kfree()`。

这不会立刻造成功能问题，但会让资源生命周期显得不够统一。

### 10.2 背光建议接入更规范的背光框架

目前背光是直接在 LCD 驱动中用 PWM 打开，适合 bring-up，但如果后续希望支持：

1. 亮度调节。
2. 电源管理联动。
3. 用户空间标准接口。

那么更合理的方向是接入 backlight 子系统，而不是把背光操作散落在输出驱动里。

### 10.3 模式校验和热插拔检测逻辑较简化

当前：

1. `atk_dpi_detect()` 直接返回 `connector_status_connected`。
2. `lcd_mode_valid()` 直接返回 `MODE_OK`。

这对于固定屏场景完全够用，但如果以后接入更多可选屏型，或者想让模式约束更严格，这两块都值得增强。

### 10.4 板级信息与策略可以进一步解耦

例如：

1. `lcd_id` 用全局变量导出。
2. 屏型号到 timing 索引的映射写在驱动里。
3. GPIO 读完再切输出的板级约束没有配套注释解释。

这些都能工作，但更长期的维护方式应该是把更多“板级策略”移到更清晰的 DTS 或数据表中。

### 10.5 提交中仍有可疑配置项值得复查

新增 defconfig 中出现了：

```text
CONFIG_GPIO_XILINX=yFA
```

这看起来更像一次误写或编辑残留。它不影响本文主线，但从提交整理角度看，属于值得单独回头清理的细节。

## 11. 常见问题

### 11.1 为什么这里选择 DRM，而不是传统 framebuffer 驱动

因为这套显示链路本身就是围绕 Xilinx DRM pipeline 组织的，前级 `pl-disp`、VTC、输出端 encoder/connector 已经天然适合用 DRM/KMS 模型描述。相比传统 fbdev，DRM 更适合表达多对象显示管线、mode setting 和后续扩展。

### 11.2 `xlnx,pl-disp` 和 `atk,atk_dpi` 分别负责什么

`xlnx,pl-disp` 负责从内存取帧、承担 CRTC/plane 角色；`atk,atk_dpi` 负责把这路显示输出接到具体 LCD 屏上，承担 encoder/connector 角色。前者偏“图像源与扫描控制”，后者偏“面向面板的输出端适配”。

### 11.3 为什么 LCD 驱动里还要自己控制像素时钟

因为对 RGB/LCD 这类并行接口来说，像素时钟本身就是显示模式的一部分。分辨率和 porch 参数确定后，像素时钟也必须切到匹配频率，否则屏幕很可能无法稳定显示。

### 11.4 为什么背光要单独做成 PWM 驱动

因为背光控制和 DRM 图像输出不是一回事。LCD 面板即使已经收到正确图像，如果背光没开，外部仍然只能看到黑屏。把 PWM 控制器做成标准 PWM provider，也便于后续被其他驱动复用。

### 11.5 LCD ID 机制解决了什么问题

它解决的是“同一套软件适配多种屏”的问题。驱动不必为每块屏单独写一份代码，而是通过硬件 ID 选择对应的 timing 配置，从而降低多屏兼容成本。

### 11.6 黑屏时优先查什么

经验上建议按下面顺序排查：

1. DRM pipeline 是否成功 bind。
2. endpoint 拓扑是否正确。
3. `lcd_pclk` 是否真正输出。
4. `display-timings` 是否匹配屏手册。
5. 背光是否打开。
6. LCD ID 是否读对，是否误用了默认回退模式。

### 11.7 这套方案后续扩展到别的 RGB 屏，通常要改哪些地方

通常优先改三类内容：

1. 设备树中的 `display-timings`。
2. `lcdID` 到 timing 的映射关系。
3. 必要时调整背光 PWM、时钟频率范围和 GPIO 极性。

如果输出接口形式没变，DRM 主体代码本身往往不需要大改。

## 12. 小结

这次提交最有价值的地方，不是单独写了一个 `xlnx_atk_lcd.c`，而是把 Zynq 平台上的 LCD 显示输出真正跑成了一条完整工程链路：前级 `pl-disp` 负责出图，VTC 负责时序，clock wizard 负责像素时钟，ATK LCD 驱动负责接入 DRM 输出端，PWM 驱动负责背光，设备树则把这一切描述成可绑定、可配置的系统拓扑。

从项目复盘角度看，这类工作最能体现嵌入式 Linux 驱动开发的真实难点：问题往往不在某一行代码，而在多子系统、多硬件资源和多层配置之间是否真正闭环。这个提交的意义，正是在于把这条闭环补上了。
