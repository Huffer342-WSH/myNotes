---
layout: post
title: 设备树语法概览
date: 2025-03-20 17:06:33
categories: [Linux]
excerpt: 
hide: false
---


 
 
 
 
## 一、设备树基础语法 
设备树（Device Tree）是一种描述硬件资源的树状数据结构，采用文本格式（.dts/.dtsi）和二进制格式（.dtb）。其核心语法规则如下：
 
1. 节点结构  
   节点由名称、地址、属性和子节点组成，基本格式为：  
   `[label:] node-name@unit-address { properties; child-nodes; };`  
   - label：节点别名，方便引用（如`&uart1`）。
   - unit-address：设备地址（如寄存器基地址）。
 
2. 属性格式  
   属性为键值对，值可以是字符串、数组、布尔值等，例如：  
   ```json
   compatible = "vendor,model";  // 字符串列表 
   reg = <0x02020000 0x4000>;    // 32位无符号整数数组 
   status = "disabled";          // 布尔/状态标识 
   ```
 
3. 层级嵌套  
   节点可包含子节点，形成树状结构。例如，SoC外设控制器下挂接具体设备。
 
```dts
/ {
    model = "Example Board v1.0";      // 开发板型号 
    compatible = "vendor,example-soc"; // 兼容的SoC型号 
    #address-cells = <1>;              // 子节点地址用1个32位单元表示 
    #size-cells = <1>;                 // 子节点长度用1个32位单元表示 
 
    // 内存描述 
    memory@80000000 {
        device_type = "memory";
        reg = <0x80000000 0x40000000>; // 起始地址0x80000000，大小1GB 
    };
 
    // CPU节点 
    cpus {
        #address-cells = <1>;
        #size-cells = <0>;
        cpu@0 {
            compatible = "arm,cortex-a9";
            device_type = "cpu";
            reg = <0>;                // CPU编号 
        };
    };
 
    // SoC外设总线 
    soc {
        compatible = "simple-bus";
        #address-cells = <1>;
        #size-cells = <1>;
        ranges;                       // 地址映射到父节点地址空间 
 
        // GPIO控制器 
        gpio_controller: gpio@10000000 {
            compatible = "vendor,soc-gpio";
            reg = <0x10000000 0x1000>; // 寄存器基地址和长度 
            #gpio-cells = <2>;         // 每个GPIO描述占用2个cell（引脚编号+标志）
            gpio-controller;           // 声明为GPIO控制器 
        };
 
        // I2C控制器 
        i2c@20000000 {
            compatible = "vendor,soc-i2c";
            reg = <0x20000000 0x1000>;
            #address-cells = <1>;
            #size-cells = <0>;
            interrupts = <15 IRQ_TYPE_LEVEL_HIGH>; // 中断号和触发方式 
 
            // I2C连接的RTC设备 
            rtc@51 {
                compatible = "nxp,pcf8563";
                reg = <0x51>;          // I2C设备地址 
                interrupt-parent = <&gpio_controller>;
                interrupts = <3 IRQ_TYPE_EDGE_FALLING>; // GPIO3，下降沿触发 
            };
        };
    };
 
    // 特殊节点 
    aliases {
        serial0 = "/soc/serial@30000000"; // 串口别名 
    };
 
    chosen {
        bootargs = "console=ttyS0,115200 root=/dev/mmcblk0p2"; // 内核启动参数 
    };
};
```
---
 
## 二、属性的不同形式 
1. 字符串：用于描述兼容性、模型名称等，如 `compatible = "fsl,imx6ul-evk-wm8960"`。
2. 32位整数数组：表示地址、长度等，如 `reg = <0x02280000 0x4000>` 表示寄存器基地址和长度。
3. 布尔值：通过存在性表示（如 `interrupt-controller;` 表示该节点是中断控制器）。
4. 混合类型：如 `interrupts = <0 66 IRQ_TYPE_LEVEL_HIGH>`，包含中断号和触发方式。
 
---
 
## 三、常用标准属性 

### compatible  
   核心驱动匹配属性，格式为 `<厂商>,<驱动名>`，如 `compatible = "davicom,dm9000"`。常常用于platform总线模型下
Linux内核通过platform总线模型实现设备与驱动的匹配。

   当驱动使用`module_platform_driver`宏注册时，其本质是注册了一个`platform_driver`结构体，其中包含`of_match_table`字段。设备树节点的`compatible`属性会与驱动中的`of_match_table`进行匹配,
    例如xilinx的gpio驱动和axi-gpio设备树：

```c
static struct platform_driver xilinx_gpio_driver = {
    .probe = xgpio_of_probe,
    .remove = xgpio_remove,
    .driver = {
	    .name = "xilinx-gpio",
	    .of_match_table = xgpio_of_match,
	    .pm = &xgpio_dev_pm_ops,
    },
};
module_platform_driver(xilinx_gpio_driver);
```

```dts
//axi-gpio设备树节点
axi_gpio_0: gpio@41210000 {
		#gpio-cells = <3>;
		clock-names = "s_axi_aclk";
		clocks = <&clkc 15>;
		compatible = "xlnx,axi-gpio-2.0", "xlnx,xps-gpio-1.00.a";
		gpio-controller ;
		reg = <0x41210000 0x10000>;
		xlnx,all-inputs = <0x0>;
		xlnx,all-inputs-2 = <0x0>;
		xlnx,all-outputs = <0x1>;
		xlnx,all-outputs-2 = <0x0>;
		xlnx,dout-default = <0x00000000>;
		xlnx,dout-default-2 = <0x00000000>;
		xlnx,gpio-width = <0x2>;
		xlnx,gpio2-width = <0x20>;
		xlnx,interrupt-present = <0x0>;
		xlnx,is-dual = <0x0>;
		xlnx,tri-default = <0xFFFFFFFF>;
		xlnx,tri-default-2 = <0xFFFFFFFF>;
	};
```


 
### #address-cells / #size-cells  
   定义子节点地址和长度的字长（32位单元数）。例如：  
   ```c 
   #address-cells = <1>;  // 地址占1个单元 
   #size-cells = <0>;     // 无长度信息 
   ```
 
### reg  
   描述设备地址空间，如 `reg = <0x4600 0x100>` 表示起始地址0x4600，长度0x100。
 
### interrupts  
   定义中断号和触发方式，需配合 `interrupt-parent` 指定中断控制器。
 
### status  
   设备状态，如 `okay`（启用）、`disabled`（禁用）。
 
---
 
## 四、特殊节点 
1. aliases  
   定义节点别名，简化引用路径。例如：  
   ```c 
   aliases {
       serial0 = &uart1;  // 通过别名访问节点 
   };
   ```
 
2. chosen  
   传递启动参数（如内核命令行），通常由Bootloader填充：  
   ```c 
   chosen {
       bootargs = "console=ttymxc0,115200";
   };
   ```
 
3. memory  
   描述物理内存布局，支持多段内存区域：  
   ```c 
   memory@0 {
       device_type = "memory";
       reg = <0x80000000 0x20000000>;  // 起始地址和长度 
   };
   ```
 
---
 
## 五、查找节点的OF函数 
Linux内核提供以下常用OF（Open Firmware）函数查找设备树节点：
 
1. 路径/名称查找  
   - `of_find_node_by_path("/soc/i2c@021a0000")`：通过完整路径查找节点。
   - `of_find_node_by_name(NULL, "gpio_spi")`：通过节点名查找。
 
2. 属性匹配  
   - `of_find_compatible_node(NULL, NULL, "vendor,model")`：根据compatible属性查找。
 
3. 父子节点操作  
   - `of_get_parent(node)`：获取父节点。
   - `of_get_next_child(parent, prev)`：遍历子节点。
 
4. 属性值提取  
   - `of_property_read_u32(node, "reg", &value)`：读取32位整数属性。
   - `of_property_read_string(node, "status", &str)`：读取字符串属性。
 
---
