---
layout: post
title: Input子系统下 按键输入驱动
date: 2025-03-30 15:10:49
categories: [Linux]
excerpt: 
hide: index
---
 
 
 
Linux Input 子系统是内核中管理输入设备（如键盘、鼠标、触摸屏等）的核心框架，其通过统一接口简化驱动开发，并为用户空间提供标准化事件处理机制。以下是其核心要点：
 
---
 
## 一、系统架构分层 
Input 子系统采用三层结构设计：
1. 驱动层（Input Driver）  
   直接操作硬件设备，负责将物理输入转换为标准事件（如按键按下、坐标变化），通过 `input_dev` 结构体描述设备特性，需开发者编写具体硬件操作代码。
   
2. 核心层（Input Core）  
   承上启下，提供设备注册接口（如 `input_register_device()`）和事件分发机制。核心层维护全局设备链表，实现驱动层与事件处理层的动态匹配。
 
3. 事件处理层（Input Handler）  
   对接用户空间，生成 `/dev/input/eventX` 设备节点，将事件封装为 `input_event` 结构体供应用程序读取。例如 `evdev` 处理通用事件，`mousedev` 处理鼠标事件。
 
---
 
## 二、关键数据结构与 API 
1. `input_dev` 结构体  
   描述输入设备属性，需配置以下字段：
   - `evbit`：支持的事件类型（如 `EV_KEY` 按键事件、`EV_ABS` 绝对坐标事件）。
   - `keybit`：具体按键编码（如 `KEY_0`、`BTN_LEFT`）。
 
2. 事件上报函数  
   - `input_report_key()`：上报按键事件。
   - `input_report_abs()`：上报绝对坐标（如触摸屏）。
   - `input_sync()`：同步事件，标志一次完整事件上报。
 
3. 用户空间事件结构体  
   ```c 
   struct input_event {
       struct timeval time;  // 时间戳 
       __u16 type;          // 事件类型（如 EV_KEY）
       __u16 code;          // 事件编码（如 KEY_0）
       __s32 value;         // 事件值（如 1 表示按下）
   };
   ```
 
---
 