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

## 四、子系统开发

参考[《Kernel subsystem documentation
》](https://docs.kernel.org/subsystem-apis.html)

Linux对常用的功能都搭建了子框架，一般都使用分层结构，开发者通过注册一系列回调函数实现功能。

且子系统也是在platform框架下的，一般都是在`probe()`/`remove()`完成对子系统的`注册/注销`
