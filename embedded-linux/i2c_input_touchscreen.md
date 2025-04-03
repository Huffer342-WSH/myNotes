---
layout: post
title: FT5426触摸屏驱动 —— 基于I2C和Input框架
date: 2025-04-01 20:39:05
categories: [Linux]
excerpt: 
hide: false
---

## 芯片简述

FT5426是一款支持TypeB类型多点触控的电容式触摸控制器

> - Type A：适用于触摸点不能被区分或者追踪
> - Type B：适用于有硬件追踪并能区分触摸点的触摸设备

该芯片需要关注的接口有两个：
- I2C接口，用于配置和获取数据
- 中断引脚，可配置为轮询模式或者触发模式，一般使用**触发模式**
  - 轮询模式： 存在触摸时持续拉低。
  - 触发模式： 持续按下时，在完成有效数据传输后会再次产生中断脉冲；中断频率由数据读取频率决定。

## 驱动程序设计

触摸屏事件的触发流程为：
**触摸 -> 触发INT -> 进入中断 -> I2C读取数据：*i2c_transfer()* -> 汇报事件*input_event()* -> 退出中断**

我们需要编写的代码大致如下：

- probe
  + 复位FT5426
  + 初始化FT5426
  + 注册中断服务函数(isr)
  + 注册input设备
- remove
  + 注销input设备
  + >使用`devm_`注册的设备不需要手动注销
- isr
  + 读取FT5426寄存器
  + 汇报事件

## 设备树

若`ft5426`挂载在`i2c1`总线下，则在`i2c1`下创建节点

```dts
&i2c1 {
	clock-frequency = <100000>;
	edt-ft5x06@38 {
		compatible = "edt,edt-ft5426";
		reg = <0x38>;

		interrupt-parent = <&gpio0>;
		interrupts = <60 0x2>;

		reset-gpio = <&gpio0 59 GPIO_ACTIVE_LOW>;
		interrupt-gpio = <&gpio0 60 GPIO_ACTIVE_LOW>;
	};
};
```

- `compatible = "edt,edt-ft5426"`: 匹配驱动
- `reg = <0x38>`：指定I2C设备的从机地址（7位或10位地址）
- `interrupts = <60 0x2>`：中断号
- `reset-gpio = <&gpio0 59 GPIO_ACTIVE_LOW>`：复位引脚
