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

## 驱动设计

触摸屏事件的触发流程为：

```mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```

````txt
```mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```
````

> **触摸 -> 触发INT -> 进入中断 -> I2C读取数据：*i2c_transfer()* -> 汇报事件*input_event()* -> 退出中断**

```mermaid
graph TD;
    A-->B;
    A-->C;
    B-->D;
    C-->D;
```

```mermaid
graph TD;
    A[触摸事件发生] --> B{触发INT中断信号};
    B --> C[进入中断服务程序];
    C --> D[调用i2c_transfer读取数据];
    D --> E[解析坐标数据];
    E --> F[上报input_event事件];
    F --> G[清除INT状态标志];
    G --> H[退出中断];
```
