---
layout: post
title: Linux内核识别设备的方式
date: 2025-04-03 12:57:44
categories: [Linux]
excerpt: 
hide: false
---


在操作系统启动之前吗，由负责启动内核的bootloader将设备信息传递给操作系统。

传递信息的方式有两种：

- **设备树（Device Tree）**：

  静态，预编译设备树文件


- **高级配置和电源接口（ACPI,Advanced Configuration and Power Interface）**：
  
  动态，启动阶段由固件生成




## 一、ACPI机制（高级配置与电源接口）
1. 核心概念与作用 
ACPI（Advanced Configuration and Power Interface）是操作系统与硬件之间的抽象层，提供统一的电源管理、设备配置和热插拔接口。其核心目标包括：
- 电源管理：支持S0（工作）至S5（完全关机）等多种电源状态切换。
- 硬件抽象：通过AML（ACPI Machine Language）代码屏蔽硬件差异，允许操作系统通过标准接口控制设备。
- 热插拔支持：动态管理PCIe、USB等总线上的设备插拔事件。
 
2. 核心组件与实现 
- AML解释器：Linux内核集成ACPICA解释器，用于执行BIOS提供的AML代码，实现硬件无关操作。
- ACPI表管理：解析DSDT（差异系统描述表）、FADT（固定ACPI描述表）等数据结构，获取处理器拓扑、NUMA配置等系统信息。
- 事件处理：通过GPE（通用事件）和SCI（系统控制中断）机制响应电源按钮、温度告警等事件。
 
3. Linux中的关键应用 
- 驱动匹配：设备驱动通过`.acpi_match_table`声明支持的ACPI设备ID。
- sysfs接口：在`/sys/firmware/acpi`目录下展示命名空间和设备状态信息。
- 电源策略：通过`/sys/power/state`文件控制休眠模式，整合CPU频率调节（如Cpufreq）实现能效优化。
 
---
 
## 二、设备树（Device Tree）机制 

1. 设计背景与核心功能 
设备树（DTS）是为解决ARM平台硬件描述冗余问题引入的机制，通过结构化数据（而非代码）描述CPU、内存、外设等硬件资源。主要优势包括：
- 硬件与驱动解耦：驱动代码无需包含板级细节，提升内核可移植性。
- 动态配置：Bootloader（uboot等）传递DTB（设备树二进制）文件，内核按需加载设备信息。
 
2. 设备树结构与语法 
- 节点与属性：
  - 节点格式：`label: node-name@address`（如`i2c1: i2c@021a0000`）。
  - 关键属性：`compatible`（驱动匹配）、`reg`（寄存器地址）、`interrupts`（中断号）等。
- 层级组织：根节点包含CPU、内存等子节点，外设挂载在总线节点下（如I2C、SPI）。
 
3. Linux内核中的处理流程 
1. 解析DTB：内核通过`of_*`系列API（如`of_get_property`）读取设备树信息。
2. 设备注册：自动生成`platform_device`结构体，与驱动的`.of_match_table`匹配。
3. 资源获取：驱动通过`gpiod_get()`、`irq_of_parse_and_map()`等接口获取GPIO、中断等参数。
 
---
 
## 三、ACPI与设备树的对比 
| 维度         | ACPI                         | 设备树（DTS）              |
| ------------ | ---------------------------- | -------------------------- |
| 适用架构     | x86/服务器主导，依赖UEFI固件 | ARM/嵌入式主导，独立于固件 |
| 设计目标     | 统一电源管理与硬件配置       | 硬件描述与驱动解耦         |
| 数据来源     | BIOS提供的ACPI表             | 开发者编写的DTS/DTSI文件   |
| 驱动匹配方式 | `.acpi_match_table`          | `.of_match_table`          |
