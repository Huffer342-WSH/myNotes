---
layout: post
title: 求职笔记 . MCU. 链接脚本
date: 2025-03-28 15:21:32
categories: [求职笔记]
excerpt: 
hide: false
---
 
## 链接脚本的作用

链接脚本（Linker Script）的作用解析  
链接脚本是编译链接阶段的核心配置文件，用于指导链接器（如 GNU `ld`）如何组织目标文件（`.o`）的代码和数据，生成最终的可执行文件或固件映像。其核心作用可分为以下五大方面：
 
---
 
1. 定义内存布局（Memory Regions）  
链接脚本通过划分物理存储区域，明确代码和数据的存放位置，例如：  
- 嵌入式系统：  
  - `FLASH` 存储代码（`.text`）和只读数据（`.rodata`）。  
  - `RAM` 存储变量（`.data`、`.bss`）和运行时堆栈。  
- 示例代码：  
  ```ld 
  MEMORY {
      FLASH (rx) : ORIGIN = 0x08000000, LENGTH = 256K 
      RAM (rwx)  : ORIGIN = 0x20000000, LENGTH = 64K 
  }
  ```
 
---
 
2. 控制段（Sections）的合并与分配  
- 段合并：将多个目标文件的同名段（如 `.text`、`.data`）合并为单一连续块。  
- 段分配：指定段所属的内存区域，例如：  
  ```ld 
  SECTIONS {
      .text : { *(.text*) } > FLASH   /* 代码段存入 FLASH */
      .data : { *(.data*) } > RAM AT> FLASH  /* 初始值在 FLASH，运行时在 RAM */
  }
  ```
 
---
 
3. 符号地址与入口点定义  
- 符号定义：生成全局符号供程序使用，例如代码起始地址 `_etext`：  
  ```ld 
  _etext = .;   /* 定义 .text 段的结束地址 */
  ```  
  在 C 代码中可通过 `extern char _etext;` 访问。  
- 入口点设置：指定程序启动地址（如复位向量 `Reset_Handler`）：  
  ```ld 
  ENTRY(Reset_Handler)
  ```
 
---
 
4. 优化存储布局与性能  
- 对齐优化：通过 `ALIGN` 指令对齐段地址，提升内存访问效率。  
  ```ld 
  .bss : {
      . = ALIGN(4);  /* 4 字节对齐 */
      *(.bss*)
  } > RAM 
  ```  
- 填充与压缩：通过 `FILL` 或 `OVERLAY` 减少存储空间浪费。
 
---
 
5. 支持硬件特性与启动流程  
- 中断向量表定位：确保向量表位于设备要求的固定地址（如 Cortex-M 的 `0x00000000`）。  
  ```ld 
  .isr_vector : {
      KEEP(*(.isr_vector))  /* 强制保留向量表 */
  } > FLASH 
  ```  
- 启动代码配置：初始化数据段（`.data`）和清零 BSS 段（`.bss`），需与启动文件（`startup_*.s`）配合。
 

## 实例分析

```ld

/* Entry Point */
ENTRY(Reset_Handler)

/* Highest address of the user mode stack */
_estack = ORIGIN(RAM) + LENGTH(RAM); /* end of "RAM" Ram type memory */

_Min_Heap_Size = 0x0; /* required amount of heap */
_Min_Stack_Size = 256; /* required amount of stack */

/* Memories definition */
MEMORY
{
  RAM    (xrw)    : ORIGIN = 0x20000000,   LENGTH = 16K
  FLASH    (rx)    : ORIGIN = 0x8000000,   LENGTH = 128K
}

/* Define output sections */
SECTIONS
{
  /* The startup code goes first into FLASH */
  .isr_vector (READONLY):
  {
    . = ALIGN(4);
    KEEP(*(.isr_vector)) /* Startup code */
    . = ALIGN(4);
  } >FLASH

  /* The program code and other data goes into FLASH */
  .text (READONLY):
  {
    . = ALIGN(4);
    *(.text)           /* .text sections (code) */
    *(.text*)          /* .text* sections (code) */
    *(.glue_7)         /* glue arm to thumb code */
    *(.glue_7t)        /* glue thumb to arm code */
    *(.eh_frame)

    KEEP (*(.init))
    KEEP (*(.fini))

    . = ALIGN(4);
    _etext = .;        /* define a global symbols at end of code */
  } >FLASH

  /* Constant data goes into FLASH */
  .rodata (READONLY):
  {
    . = ALIGN(4);
    *(.rodata)         /* .rodata sections (constants, strings, etc.) */
    *(.rodata*)        /* .rodata* sections (constants, strings, etc.) */
    . = ALIGN(4);
  } >FLASH

  .ARM.extab   (READONLY): { *(.ARM.extab* .gnu.linkonce.armextab.*) } >FLASH
  .ARM (READONLY): {
    __exidx_start = .;
    *(.ARM.exidx*)
    __exidx_end = .;
  } >FLASH

  .preinit_array    (READONLY)  :
  {
    PROVIDE_HIDDEN (__preinit_array_start = .);
    KEEP (*(.preinit_array*))
    PROVIDE_HIDDEN (__preinit_array_end = .);
  } >FLASH
  .init_array(READONLY)  :
  {
    PROVIDE_HIDDEN (__init_array_start = .);
    KEEP (*(SORT(.init_array.*)))
    KEEP (*(.init_array*))
    PROVIDE_HIDDEN (__init_array_end = .);
  } >FLASH
  .fini_array (READONLY) :
  {
    PROVIDE_HIDDEN (__fini_array_start = .);
    KEEP (*(SORT(.fini_array.*)))
    KEEP (*(.fini_array*))
    PROVIDE_HIDDEN (__fini_array_end = .);
  } >FLASH

  /* used by the startup to initialize data */
  _sidata = LOADADDR(.data);

  /* Initialized data sections goes into RAM, load LMA copy after code */
  .data : 
  {
    . = ALIGN(4);
    _sdata = .;        /* create a global symbol at data start */
    *(.data)           /* .data sections */
    *(.data*)          /* .data* sections */

    . = ALIGN(4);
    _edata = .;        /* define a global symbol at data end */
  } >RAM AT> FLASH

  
  /* Uninitialized data section */
  . = ALIGN(4);
  .bss :
  {
    /* This is used by the startup in order to initialize the .bss secion */
    _sbss = .;         /* define a global symbol at bss start */
    __bss_start__ = _sbss;
    *(.bss)
    *(.bss*)
    *(COMMON)

    . = ALIGN(4);
    _ebss = .;         /* define a global symbol at bss end */
    __bss_end__ = _ebss;
  } >RAM

  /* User_heap_stack section, used to check that there is enough RAM left */
  ._user_heap_stack :
  {
    . = ALIGN(8);
    PROVIDE ( end = . );
    PROVIDE ( _end = . );
    . = . + _Min_Heap_Size;
    . = . + _Min_Stack_Size;
    . = ALIGN(8);
  } >RAM

  

  /* Remove information from the standard libraries */
  /DISCARD/ :
  {
    libc.a ( * )
    libm.a ( * )
    libgcc.a ( * )
  }

  .ARM.attributes 0 : { *(.ARM.attributes) }
}

```
以下是针对 `gd32f350.ld` 链接脚本的逐段分析，按代码顺序解释其作用：

---

### **1. 入口点定义**
```ld
ENTRY(Reset_Handler)
```
- **作用**：指定程序的入口点为 `Reset_Handler`，这是芯片复位后执行的第一条指令（通常位于启动文件 `startup_*.s` 中）。

---

### **2. 栈顶地址定义**
```ld
_estack = ORIGIN(RAM) + LENGTH(RAM); /* end of "RAM" */
```
- **作用**：定义用户模式栈的初始栈顶地址为 RAM 的末尾（最高地址）。栈从高地址向低地址增长。

---

### **3. 堆栈最小大小**
```ld
_Min_Heap_Size = 0x0;   /* 堆的最小大小（未启用堆） */
_Min_Stack_Size = 256;   /* 栈的最小大小（256字节） */
```
- **说明**：堆未启用（`0x0`），栈保留 256 字节空间，供中断和函数调用使用。

---

### **4. 存储器区域定义**
```ld
MEMORY {
  RAM    (xrw) : ORIGIN = 0x20000000, LENGTH = 16K
  FLASH  (rx)  : ORIGIN = 0x8000000,  LENGTH = 128K
}
```
- **RAM**：起始地址 `0x20000000`，长度 16KB，可执行（`x`）、可读（`r`）、可写（`w`）。
- **FLASH**：起始地址 `0x08000000`（注意 `0x8000000` 可能为笔误，通常 Cortex-M 的 FLASH 基址为 `0x08000000`），长度 128KB，可读（`r`）、可执行（`x`）。

---

### **5. 段（SECTIONS）分配**
#### **5.1 中断向量表**
```ld
.isr_vector (READONLY) {
  . = ALIGN(4);
  KEEP(*(.isr_vector)) /* 中断向量表 */
  . = ALIGN(4);
} >FLASH
```
- **作用**：将 `.isr_vector` 段（中断向量表）放置在 FLASH 的起始位置，强制 4 字节对齐。
- `KEEP`：确保该段不被链接器优化删除。

---

#### **5.2 程序代码段**
```ld
.text (READONLY) {
  . = ALIGN(4);
  *(.text)        /* 代码段 */
  *(.text*)       /* 其他代码段（如内联函数） */
  *(.glue_7)      /* ARM/Thumb 代码粘合 */
  *(.glue_7t)
  *(.eh_frame)    /* 异常处理框架（C++） */
  KEEP(*(.init))  /* 初始化代码 */
  KEEP(*(.fini))  /* 终止代码 */
  . = ALIGN(4);
  _etext = .;     /* 代码段结束地址 */
} >FLASH
```
- **作用**：存放所有代码（`.text`）、ARM/Thumb 粘合代码、C++ 异常处理框架等。
- `_etext`：符号标记代码段结束，用于后续数据初始化。

---

#### **5.3 只读数据段**
```ld
.rodata (READONLY) {
  . = ALIGN(4);
  *(.rodata)      /* 只读数据（如常量字符串） */
  *(.rodata*)     /* 其他只读数据 */
  . = ALIGN(4);
} >FLASH
```
- **作用**：存放只读常量数据，如全局常量、字符串等。

---

#### **5.4 ARM 异常处理段**
```ld
.ARM.extab (READONLY) { *(.ARM.extab* .gnu.linkonce.armextab.*) } >FLASH
.ARM (READONLY) {
  __exidx_start = .;
  *(.ARM.exidx*)
  __exidx_end = .;
} >FLASH
```
- **作用**：
  - `.ARM.extab`：存放异常展开信息（用于 C++ 异常）。
  - `.ARM.exidx`：存放异常索引表，`__exidx_start` 和 `__exidx_end` 标记其范围。

---

#### **5.5 初始化/终止函数数组**
```ld
.preinit_array (READONLY) {
  PROVIDE_HIDDEN(__preinit_array_start = .);
  KEEP(*(.preinit_array*))
  PROVIDE_HIDDEN(__preinit_array_end = .);
} >FLASH

.init_array (READONLY) {
  PROVIDE_HIDDEN(__init_array_start = .);
  KEEP(*(SORT(.init_array.*)))
  KEEP(*(.init_array*))
  PROVIDE_HIDDEN(__init_array_end = .);
} >FLASH

.fini_array (READONLY) {
  PROVIDE_HIDDEN(__fini_array_start = .);
  KEEP(*(SORT(.fini_array.*)))
  KEEP(*(.fini_array*))
  PROVIDE_HIDDEN(__fini_array_end = .);
} >FLASH
```
- **作用**：存放全局构造函数（`.init_array`）和析构函数（`.fini_array`）的指针数组。
- `PROVIDE_HIDDEN`：生成隐藏符号，避免与其他同名符号冲突。

---

#### **5.6 初始化数据段**
```ld
_sidata = LOADADDR(.data); /* .data 的加载地址（FLASH） */

.data {
  . = ALIGN(4);
  _sdata = .;        /* 数据段起始地址（RAM） */
  *(.data)           /* 已初始化全局变量 */
  *(.data*)
  . = ALIGN(4);
  _edata = .;        /* 数据段结束地址（RAM） */
} >RAM AT> FLASH
```
- **作用**：已初始化的全局变量存储在 RAM 中，但其初始值保存在 FLASH 中。
- `>RAM AT> FLASH`：运行时地址（VMA）在 RAM，加载地址（LMA）在 FLASH。
- 启动代码需将 `_sidata`（FLASH 中的初始值）复制到 `_sdata`（RAM 中的目标地址）。

---

#### **5.7 未初始化数据段（BSS）**
```ld
.bss {
  _sbss = .;         /* BSS 段起始地址 */
  __bss_start__ = _sbss;
  *(.bss)            /* 未初始化全局变量 */
  *(.bss*)
  *(COMMON)          /* 未初始化的全局变量（C 语言） */
  . = ALIGN(4);
  _ebss = .;         /* BSS 段结束地址 */
  __bss_end__ = _ebss;
} >RAM
```
- **作用**：未初始化的全局变量和静态变量在此段分配，启动代码需将 `_sbss` 到 `_ebss` 的内存清零。

---

#### **5.8 用户堆栈区域**
```ld
._user_heap_stack {
  . = ALIGN(8);
  PROVIDE(end = .);      /* 堆起始地址 */
  PROVIDE(_end = .);
  . += _Min_Heap_Size;   /* 保留堆空间（此处为 0） */
  . += _Min_Stack_Size;  /* 保留栈空间（256字节） */
  . = ALIGN(8);
} >RAM
```
- **作用**：在 RAM 末尾保留堆和栈空间。由于 `_Min_Heap_Size = 0`，此处仅保留 256 字节栈空间。

---

#### **5.9 丢弃标准库段**
```ld
/DISCARD/ {
  libc.a (*)
  libm.a (*)
  libgcc.a (*)
}
```
- **作用**：禁止链接标准库（`libc`、`libm`、`libgcc`），通常用于减少代码体积或自定义库实现。

---

#### **5.10 ARM 属性段**
```ld
.ARM.attributes 0 : { *(.ARM.attributes) }
```
- **作用**：存放 ARM 架构相关属性信息（非运行必需，通常用于调试）。

---

### **总结**
此链接脚本为 GD32F350 微控制器定制，主要功能包括：
1. 将中断向量表和代码段放置在 FLASH 起始位置。
2. 已初始化数据（`.data`）从 FLASH 加载到 RAM。
3. 未初始化数据（`.bss`）在 RAM 中分配并清零。
4. 在 RAM 末尾保留栈空间。
5. 禁用标准库以减少体积。

启动代码需完成以下任务：
- 复制 `.data` 段从 FLASH 到 RAM。
- 清零 `.bss` 段。
- 初始化堆栈指针为 `_estack`。
