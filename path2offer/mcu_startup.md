---
layout: post
title: 求职笔记 . MCU . Cortex-M启动脚本分析
date: 2025-03-28 15:11:07
categories: [求职笔记]
excerpt: startup_gd32f3x0.s启动脚本分析
hide: false
---

以下代代码是`startup_gd32f3x0.s`的text.Reset_Handler代码段

```asm
    .section	.text.Reset_Handler
	.weak	Reset_Handler
	.type	Reset_Handler, %function
Reset_Handler:
  ldr   sp, =_estack    /* Atollic update: set stack pointer */
  
/* Call the clock system initialization function.*/
    bl  SystemInit

/* Copy the data segment initializers from flash to SRAM */
  ldr r0, =_sdata
  ldr r1, =_edata
  ldr r2, =_sidata
  movs r3, #0
  b LoopCopyDataInit

CopyDataInit:
  ldr r4, [r2, r3]
  str r4, [r0, r3]
  adds r3, r3, #4

LoopCopyDataInit:
  adds r4, r0, r3
  cmp r4, r1
  bcc CopyDataInit
  
/* Zero fill the bss segment. */
  ldr r2, =_sbss
  ldr r4, =_ebss
  movs r3, #0
  b LoopFillZerobss

FillZerobss:
  str  r3, [r2]
  adds r2, r2, #4

LoopFillZerobss:
  cmp r2, r4
  bcc FillZerobss

/* Call static constructors */
    bl __libc_init_array
/* Call the application's entry point.*/
	bl	main

LoopForever:
    b LoopForever
```

这段代码是Cortex - M微控制器的启动脚本代码，用于完成系统启动时的一系列初始化工作，最终调用应用程序的入口点`main`函数。以下是对代码各部分的详细分析： 
 
1. 代码段和函数声明 
```asm 
.section	.text.Reset_Handler 
.weak	Reset_Handler 
.type	Reset_Handler, %function 
Reset_Handler: 
``` 
- `.section .text.Reset_Handler`：指定接下来的代码属于`.text.Reset_Handler`代码段，通常用于存储复位处理程序。 
- `.weak Reset_Handler`：将`Reset_Handler`声明为弱符号。这意味着如果在其他地方定义了同名的强符号，链接器会使用强符号。 
- `.type Reset_Handler, %function`：声明`Reset_Handler`为一个函数。 
- `Reset_Handler:`：定义复位处理程序的入口标签。 
 
2. 设置栈指针 
```asm 
ldr   sp, =_estack    /* Atollic update: set stack pointer */ 
``` 
- `ldr sp, =_estack`：将栈顶地址`_estack`加载到栈指针`sp`中。栈指针是微控制器运行时非常重要的寄存器，用于管理函数调用和局部变量的存储。 
 
3. 调用系统时钟初始化函数 
```asm 
/* Call the clock system initialization function.*/ 
bl  SystemInit 
``` 
- `bl SystemInit`：调用`SystemInit`函数，该函数通常用于初始化系统时钟。正确的时钟配置对于微控制器的正常运行至关重要，它会影响到外设的工作频率和定时。 
 
4. 复制数据段初始化值到SRAM 
```asm 
/* Copy the data segment initializers from flash to SRAM */ 
ldr r0, =_sdata 
ldr r1, =_edata 
ldr r2, =_sidata 
movs r3, #0 
b LoopCopyDataInit 
 
CopyDataInit: 
  ldr r4, [r2, r3] 
  str r4, [r0, r3] 
  adds r3, r3, #4 
 
LoopCopyDataInit: 
  adds r4, r0, r3 
  cmp r4, r1 
  bcc CopyDataInit 
``` 
- `_sdata`：数据段在SRAM中的起始地址。 
- `_edata`：数据段在SRAM中的结束地址。 
- `_sidata`：数据段在闪存中的起始地址。 
- 这段代码通过循环将数据段的初始化值从闪存复制到SRAM中。每次复制4个字节（一个字），直到复制完整个数据段。 
 
5. 清零bss段 
```asm 
/* Zero fill the bss segment. */ 
ldr r2, =_sbss 
ldr r4, =_ebss 
movs r3, #0 
b LoopFillZerobss 
 
FillZerobss: 
  str  r3, [r2] 
  adds r2, r2, #4 
 
LoopFillZerobss: 
  cmp r2, r4 
  bcc FillZerobss 
``` 
- `_sbss`：bss段在SRAM中的起始地址。 
- `_ebss`：bss段在SRAM中的结束地址。 
- 这段代码通过循环将bss段的内存清零。bss段用于存储未初始化的全局变量和静态变量，清零操作确保这些变量在程序开始时的值为零。 
 
6. 调用静态构造函数 
```asm 
/* Call static constructors */ 
bl __libc_init_array 
``` 
- `bl __libc_init_array`：调用`__libc_init_array`函数，该函数用于执行静态构造函数。静态构造函数通常用于初始化全局对象。 
 
7. 调用应用程序入口点 
```asm 
/* Call the application's entry point.*/ 
bl	main 
``` 
- `bl main`：调用应用程序的入口点`main`函数，开始执行应用程序的主要逻辑。 
 
8. 无限循环 
```asm 
LoopForever: 
    b LoopForever 
``` 
- 如果`main`函数返回，程序会进入这个无限循环，避免程序失控。 
 
综上所述，这段启动脚本代码完成了栈指针设置、时钟初始化、数据段复制、bss段清零、静态构造函数调用等初始化工作，最终启动应用程序。
