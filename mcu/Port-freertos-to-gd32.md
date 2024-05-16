---
layout: post
title: GD32移植FreeRTOS
date: 2024-05-28 19:38:03
excerpt: GD32移植FreeRTOS
categories: [单片机]
---

## 模板

[GD32_FreeRTOS_templete](https://github.com/Huffer342-WSH/GD32_FreeRTOS_templete)

## 下载源码
FreeRTOS源码：[FreeRTOS v202210.01-LTS](https://github.com/FreeRTOS/FreeRTOS-LTS/releases/download/202210.01-LTS/FreeRTOSv202210.01-LTS.zip)

## 复制文件
官方教程:[创建一个新的 FreeRTOS 项目](https://www.freertos.org/zh-cn-cmn-s/Creating-a-new-FreeRTOS-project.html)

一般需要复制的文件如下：
```
FreeRTOS
  │  CMakeLists.txt
  │
  └─Source
      │  CMakeLists.txt
      │  croutine.c
      │  event_groups.c
      │  GitHub-FreeRTOS-Kernel-Home.url
      │  History.txt
      │  LICENSE.md
      │  list.c
      │  manifest.yml
      │  queue.c
      │  Quick_Start_Guide.url
      │  README.md
      │  sbom.spdx
      │  stream_buffer.c
      │  tasks.c
      │  timers.c
      │
      ├─include
      │      atomic.h
      │      croutine.h
      │      deprecated_definitions.h
      │      event_groups.h
      │      FreeRTOS.h
      │      list.h
      │      message_buffer.h
      │      mpu_prototypes.h
      │      mpu_wrappers.h
      │      portable.h
      │      projdefs.h
      │      queue.h
      │      semphr.h
      │      StackMacros.h
      │      stack_macros.h
      │      stdint.readme
      │      stream_buffer.h
      │      task.h
      │      timers.h
      │
      └─portable
          │  CMakeLists.txt
          │
          ├─[compiler] // 编译器类型
          │  └─[architecture] // 处理器架构
          │          port.c
          │          portmacro.h
          │
          └─MemMang
                 heap_4.c

```

## 编写FreeRTOSConfig.h 

FreeRTOS有三个关键的中断函数
- SysTick_Handler： 时钟驱动，用于节拍计数，定时任务调度，延迟等
- SVC_Handler： 用于初始化FreeRTOS并启动第一个任务。
- PendSV_Handler： 用于在任务调度过程中执行任务上下文切换，确保正确的任务在正确的时间运行。

三个函数在```port.c```中分别以```xPortSysTickHandler```、```vPortSVCHandler```、```xPortPendSVHandler```命名。
也就是说这三个函数默认是要手动调用的，但是可以在```FreeRTOSConfig.h```中用宏重命名三个函数，直接用中断向量表中的名字命名，就不需要手动调用了（当然你也可以去改中断向量表）。官方的原文如下 [FreeRTOS常见问题：我的应用程序没有运行，可能出了什么问题？](https://www.freertos.org/zh-cn-cmn-s/FAQHelp.html)

>针对 ARM Cortex-M 用户的特别提示： ARM Cortex-M3、ARM Cortex-M4 和 ARM Cortex-M4F 端口要求 FreeRTOS 处理程序 安装在 SysTick、 PendSV 和 SVCCall 中断向量上。 可以 将 FreeRTOS 定义的 xPortSysTickHandler()， xPortPendSVHandler() 和 vPortSVCHandler() 函数直接填入向量表的对应位置，或者如果 中断向量表与 CMSIS 相容，可以将以下三行 添加到 FreeRTOSConfig.h，用于将 FreeRTOS 函数名称映射到 其对应的 CMSIS 名称。
>
>#define vPortSVCHandler SVC_Handler
>#define xPortPendSVHandler PendSV_Handler
>#define xPortSysTickHandler SysTick_Handler
>	
>以这种方式使用 #defines 的前提是， 您的开发工具提供的默认处理程序 被定义为弱符号。 如果默认处理程序没有被定义为弱符号， 则需要将其注释掉或删除。

## 其他

### 关于系统时钟
起初我以为要自己配置Systick，但是后来发现FreeRTOS会自动配置Systick。

在vTaskStartScheduler() -> xPortStartScheduler() -> vPortSetupTimerInterrupt() 中会按照FreeRTOSConfig中配置时钟配置systick。

不过如果不想用systick作为系统时钟源，则需要重写```void vPortSetupTimerInterrupt( void )```,并且在定时器中断中调用```xPortSysTickHandler()```
