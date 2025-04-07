---
layout: post
title: Linux内核启动流程
date: 2025-04-07 15:07:52
categories: [Linux]
excerpt: 
hide: false
---


ARM 平台下的 Linux 内核启动流程大致分为 **Bootloader 阶段** 和 **内核启动阶段（汇编和 C 语言部分）**，最终进入 **用户空间**。


## 一、Bootloader 阶段（以 U-Boot 为例）

U-Boot的主要功能如下：

- 初始化基础硬件（如时钟、电源、串口等）
- 加载 Linux 内核镜像（通常是 zImage/uImage/Image）
- 设置内核启动参数（命令行、设备树等）
- 跳转到内核入口地址执行

### Bootloader 启动内核：

```c
void (*kernel_entry)(int zero, int arch, void *params);
kernel_entry = (void *)kernel_load_address;
kernel_entry(0, mach_type, atags_or_fdt); // 通常传入的 3 个参数
```

---

## 二、Linux 内核汇编部分启动流程（arch/arm/boot/compressed/head.S）

### 1. 解压入口（zImage 情况）
内核的 zImage 其实是一个自解压的压缩包，执行时先运行解压代码（`arch/arm/boot/compressed/head.S`），解压后的内核代码放到指定地址后，跳转到内核真实入口。

```asm
// head.S 中最后执行：
bl decompress_kernel
b start_kernel
```

---

## 三、Linux 内核真正的入口（arch/arm/kernel/head.S）

解压后的内核真正入口为 `arch/arm/kernel/head.S` 中的 `_stext`，通常位于 `head.o` 中，内核执行从这里开始。

Linux内核执行前要求:
```
/*
 * Kernel startup entry point.
 * ---------------------------
 *
 * This is normally called from the decompressor code.  The requirements
 * are: MMU = off, D-cache = off, I-cache = dont care, r0 = 0,
 * r1 = machine nr, r2 = atags or dtb pointer.
 *
...
 */
```
- 关闭 MMU。
- 关闭 D-cache。
- I-Cache 无所谓。
- r0=0。
- r1=machine nr(也就是机器 ID)。
- r2=atags 或者设备树(dtb)首地址。


### 2. `_stext` 到 `start_kernel`
`_stext` -> `stext` -> `start_kernel`

```asm
ENTRY(stext)
    safe_svcmode_maskall r9  // 确保CPU处于SVC模式，且所有中断被屏蔽
    bl	__lookup_processor_type // 检查当前系统是否支持此 CPU
    bl __create_page_tables  // 创建初始页表
    bl __enable_mmu          // 开启 MMU

__enable_mmu:
    b	__turn_mmu_on   // 

__turn_mmu_on:
    执行 r13 里面保存的__mmap_switched 函数

```

- 设置堆栈指针
- 设置 CPU 模式（SVC 模式）
- 建立初始页表
- 开启 MMU
- 跳转到 `start_kernel`（位于 `init/main.c`）

---

## 四、Linux C 语言初始化流程（init/main.c）

### 3. `start_kernel()`

这是 C 语言部分的核心入口，主要完成：

```c
asmlinkage __visible void __init start_kernel(void)
{
    // 初始化架构相关代码（setup_arch）
    // 初始化定时器、内存管理、页表
    // 初始化中断
    // 初始化内核线程支持
    // 调用 rest_init()
}
```

---

### 4. `rest_init()`

该函数进入内核线程模式，创建 init 进程。

```c
static noinline void __ref rest_init(void)
{
    kernel_thread(kernel_init, NULL, CLONE_FS);
    kernel_thread(kthreadd, NULL, CLONE_FS);
    ...
    cpu_startup_entry(CPUHP_ONLINE); // 启动 idle 循环
}
```

- 创建内核线程 `kernel_init`
- 创建内核线程 `kthreadd`， 负责内核线程的关联
- 主 CPU 进入 `cpu_idle` 循环等待

---

### 5. `kernel_init()`

这是内核线程，由 rest_init 创建。它会继续初始化用户空间相关内容。

```c
static int __ref kernel_init(void *unused)
{
    kernel_init_freeable();
    ...
    // 尝试执行用户初始化程序，任意一个成功就退出
	if (ramdisk_execute_command) {
		ret = run_init_process(ramdisk_execute_command);
		if (!ret)
			return 0;
		pr_err("Failed to execute %s (error %d)\n",
		       ramdisk_execute_command, ret);
	}

	if (execute_command) {
		ret = run_init_process(execute_command);
		if (!ret)
			return 0;
		panic("Requested init %s failed (error %d).",
		      execute_command, ret);
	}
	if (!try_to_run_init_process("/sbin/init") ||
	    !try_to_run_init_process("/etc/init") ||
	    !try_to_run_init_process("/bin/init") ||
	    !try_to_run_init_process("/bin/sh"))
		return 0;

	panic("No working init found.  Try passing init= option to kernel. "
	      "See Linux Documentation/admin-guide/init.rst for guidance.");
}
```

- kernel_init_freeable()中完成设备驱动初始化、创建/dev/console、挂载根文件系统等.kernel_init_freeable执行完后就已经进入用户模式了
- 尝试加载用户空间第一个进程：`/sbin/init` , `/sbin/init`往往是一个链接，在zynq上指向`/sbin/init -> /sbin/init.sysvinit`，ubuntu上指向`/sbin/init -> /lib/systemd/systemd`

---

## 五、进入用户空间

### 6. 用户态 init 进程（PID 1）

- 至此，内核启动完成
- 系统正式进入 **用户空间**
- `init` 进程负责启动其他服务（如 systemd、init、busybox 等）


## 其他

**驱动初始化的位置**
