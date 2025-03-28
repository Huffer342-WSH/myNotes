---
layout: post
title: Linux驱动开发概览
date: 2025-03-20 20:14:29
categories: [Linux]
excerpt: 
hide: false
---
 
# Linux驱动开发方法概览：从寄存器操作到框架集成 

 
## 一、原始寄存器级驱动开发 
### 1.1 核心原理与实现 
直接通过代码操作硬件寄存器，适用于无标准框架支持的早期开发或简单外设。开发者需手动映射物理地址到虚拟地址空间（如`ioremap`），并实现字符设备驱动的完整生命周期管理。典型步骤包括：
1. 使用`register_chrdev`注册字符设备 
2. 实现`file_operations`接口（open/read/write/ioctl）
3. 通过`ioremap`映射物理寄存器地址 
4. 手动处理中断（`request_irq`）
 
```c 
static int __init mydriver_init(void) {
    base_addr = ioremap(REG_BASE, REG_SIZE);
    request_irq(IRQ_NUM, irq_handler, IRQF_SHARED, "mydriver", dev);
}
```
 
### 1.2 适用场景与局限 
- 优势：完全掌控硬件时序，适合裸机移植场景 
- 劣势：代码与硬件强耦合，维护困难，不支持动态配置
 
---
 
## 二、设备树驱动开发 
### 2.1 设备树工作机制 
通过DTS（Device Tree Source）描述硬件拓扑，实现硬件配置与驱动代码的解耦。内核启动时解析DTB文件，根据`compatible`属性匹配驱动。典型设备树节点包含：
- 寄存器地址映射（`reg`属性）
- 中断号配置（`interrupts`属性）
- GPIO引脚定义（`gpios`属性）
 
```dts 
gpio_leds {
    compatible = "gpio-leds";
    led1 {
        label = "sys_led";
        gpios = <&gpio0 15 GPIO_ACTIVE_HIGH>;
    };
};
```
 
### 2.2 驱动开发要点 
- 使用`of_property_read_u32`等API解析设备树属性 
- 通过`platform_get_resource`获取内存/中断资源 
- 结合`platform_driver`结构体注册驱动
 
---
 
## 三、Platform框架开发 

### 3.1 传统Device/Driver模式 
- 架构组成：
  - `platform_device`：显式定义硬件资源 
  - `platform_driver`：实现驱动核心逻辑 
  - 总线通过`id_table`或名称匹配设备
 
开发流程：
1. 静态注册`platform_device`
2. 实现驱动`probe()`/`remove()`方法 
3. 通过`platform_get_resource`获取资源 
 
### 3.2 设备树集成模式 
- 设备树节点自动生成`platform_device`
- 驱动通过`of_match_table`匹配`compatible`属性 
- 资源获取方式与纯设备树驱动相同
 
| 模式         | 硬件描述位置 | 动态加载能力 |
|--------------|--------------|--------------|
| 传统Device   | 内核代码     | 弱           |
| 设备树集成   | DTS文件      | 强           |
 
---

## 四、总线子系统开发（I2C/SPI）

### 4.1 总线层级与框架结构 
I2C/SPI总线子系统处于硬件寄存器操作与高层框架之间的中间层，直接处理总线时序协议，为设备驱动提供标准访问接口。其分层架构包含：
- 主机控制器驱动（Host Controller）：管理物理总线控制器（如GPIO模拟I2C或专用I2C IP核），实现时序生成和信号解析  
- 设备驱动（Client Driver）：对接具体外设（如EEPROM、传感器），封装设备特定操作（寄存器读写）
 
开发范式特征：  
1. 协议实现：需精确处理总线时序（如I2C的START/STOP信号，SPI的CPOL/CPHA时钟模式）  
2. 双工机制：I2C半双工（分时复用SDA），SPI全双工（独立MOSI/MISO线）  
3. 地址匹配：I2C通过7/10位地址识别设备，SPI通过片选信号（CS）选择设备
 
### 4.2 I2C子系统开发流程 
4.2.1 驱动实现步骤 
1. 定义设备地址：在设备树中声明`compatible`属性及7位地址  
```dts 
eeprom@50 {
    compatible = "atmel,24c02";
    reg = <0x50>; // 7位地址左移1位后为0xA0 
};
```
2. 实现驱动结构体：注册`i2c_driver`并绑定probe/remove方法  
```c 
static struct i2c_driver eeprom_driver = {
    .driver = {.name = "24c02"},
    .probe = eeprom_probe,
    .remove = eeprom_remove,
    .id_table = eeprom_ids,
};
```
3. 数据传输：使用`i2c_transfer`或封装接口（`i2c_smbus_read_byte_data`）  
```c 
i2c_smbus_write_byte_data(client, reg_addr, value); // 写入寄存器 
```
 
### 4.3 SPI子系统开发要点 
4.3.1 协议配置 

需在设备树指定时钟模式（CPOL/CPHA）、速率等参数  
```dts 
flash@0 {
    compatible = "winbond,w25q128";
    spi-max-frequency = <50000000>;
    spi-cpol; // 时钟极性配置 
    spi-cpha; // 时钟相位配置 
};
```
4.3.2 数据传输机制 

使用`spi_sync`实现全双工通信，通过`spi_message`组织传输链表  
```c 
struct spi_transfer t = {
    .tx_buf = tx_buffer,
    .rx_buf = rx_buffer,
    .len = 4,
};
spi_message_init(&m);
spi_message_add_tail(&t, &m);
spi_sync(spi, &m); // 同步传输 
```
 
---
 
 
## 五、用户态接口标准化的子系统
 
一些常用的设备比如鼠标、触摸屏、显示器等设备，内核给用户端的应用程序提供统一的调用接口。
该类设备的上层接口已经固定，开发驱动时需要实现上层需要的指定功能。
 
### Input子系统 
- 用户接口：`/dev/input/eventX`（事件设备文件）
- 驱动实现：
  - 定义`struct input_dev`结构体 
  - 通过`input_allocate_device()`创建设备对象 
  - 设置事件类型位图（`EV_KEY`/`EV_REL`等）
  - 调用`input_register_device()`注册设备 
  - 通过`input_report_xxx()`系列函数上报事件 
```c 
input_dev = input_allocate_device();
set_bit(EV_KEY, input_dev->evbit); // 声明支持按键事件 
input_set_capability(input_dev, EV_KEY, KEY_ESC); // 定义具体按键 
input_register_device(input_dev);
```
 
### DRM/KMS子系统 
- 用户接口：通过`/dev/dri/cardX`提供DRI接口
- 驱动实现：
  - 实现`drm_driver`结构体（含`gem_prime_mmap`等回调）
  - 定义显示模式配置（`drm_mode_config`）
  - 支持原子提交（Atomic Commit）和平面混合（Plane Blending）
 
---

### V4L2视频子系统 

- 用户接口：`/dev/videoX`（视频设备节点）
- 驱动实现：
  - 实现`v4l2_file_operations`和`v4l2_ioctl_ops`
  - 配置视频缓冲队列（`vb2_queue`）
  - 支持MPlane内存分配（用于多平面格式）
 
### ALSA音频子系统 

- 用户接口：`/dev/snd/pcmCXpX`（PCM设备文件）
- 驱动实现：
  - 定义`snd_pcm_ops`结构体（含`hw_params`/`trigger`回调）
  - 通过`snd_pcm_new()`创建PCM实例 
  - 实现DMA缓冲区管理 
 

 
### MTD子系统 

MTD(memory technology device)是用于访问memory设备（比如NOR Flash、NAND Flash）的Linux的子系统
- 用户接口：通过`/dev/mtdX`提供原始闪存访问
- 驱动实现：
  - 实现`mtd_info`结构体（含`_read`/`_write`方法）
  - 支持坏块管理和ECC校验 
 

### 块设备子系统 

- 用户接口：`/dev/sdX`（块设备文件）
- 驱动实现：
  - 定义`gendisk`结构体 
  - 实现`block_device_operations`操作集 
  - 管理请求队列（`request_queue`）
  
### 网络设备子系统 

- 用户接口：通过`socket()`系统调用访问
- 驱动实现：
  - 定义`net_device`结构体 
  - 实现`net_device_ops`操作集（含`ndo_start_xmit`等）
  - 支持NAPI收包机制 
 
### USB Gadget子系统 

- 用户接口：通过`configfs`配置设备角色
- 驱动实现：
  - 实现`usb_gadget_driver`结构体 
  - 定义端点描述符（`usb_endpoint_descriptor`）
 

### IIO子系统 

IIO(Industrial I/O)主要用于数字量和模拟量转换的IO接口设备
- 用户接口：`/sys/bus/iio/devices/iio:deviceX`（sysfs接口）
- 驱动实现：
  - 定义`iio_chan_spec`通道描述符 
  - 实现`iio_info`结构体（含`read_raw`回调）
  - 支持硬件触发模式 
 
---
