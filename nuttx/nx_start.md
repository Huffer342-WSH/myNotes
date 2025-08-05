---
layout: post
title: nuttx启动流程
date: 2025-08-05 15:09:06
categories: [nuttx]
excerpt:
hide: false
---

## arm_head.S

arm_head.S中的__start() 是CPU启动入口，内容如下

### 1. 多核处理（CONFIG_NCPUS > 1时）
- 获取CPU索引（MPIDR寄存器）
- CPU0继续启动流程，其他CPU等待CPU0的信号
- 通过忙等待或WFE指令等待启动标志

### 2. 基础设置
- 设置CPU为SYS模式，禁用IRQ和FIQ
- 确保MMU和缓存被禁用

### 3. 页表初始化
- 清除16KB的L1页表
- 如果需要，为页表本身创建特殊映射
- 为.text区域创建映射，.LCtextinfo之后的数组保存了待映射断的信息


### 4. 缓存和TLB操作
- 初始化CPU寄存器TPIDRPRW
- 无效化整个TLB、分支预测数组和I-cache

### 5. MMU配置
- 设置页表基址寄存器(TTBR0/TTBR1)
- 配置TTBCR使用TTBR0
- 设置域访问控制(DACR)
- 精细配置系统控制寄存器(SCTLR)：
  - 启用/禁用MMU、缓存、对齐检查等
  - 设置大小端
  - 向量表位置等

### 6. 启用MMU
- 写入SCTLR启用MMU
- 执行必要的同步指令
- 跳转到虚拟地址空间的.Lvstart

### 7. 虚拟地址空间启动(.Lvstart)
- 移除临时映射（如果存在）
- 设置栈指针并清零帧指针
- `arm_data_initialize()`初始化.bss和.data段（如果在SRAM中）
- `arm_boot()`执行平台特定的初始化
- `nx_start()`跳转到操作系统入口点


## arm_boot()

`arm_boot()`在各个板子下都有自己的实现，大多用于完成CPU级别的初始化，比如MMU、CACHE、SMP等

在Kconfig中通过`ARCH_CHIP_xxx`指定CPU平台，从而编译制定代码，也可以使用自定义配置:
```
CONFIG_ARCH_CHIP_ARM_CUSTOM=y
CONFIG_ARCH_CHIP_CUSTOM=y
CONFIG_ARCH_CHIP_CUSTOM_DIR="../path/to/source"
CONFIG_ARCH_CHIP_CUSTOM_DIR_RELPATH=y
CONFIG_ARCH_CHIP_CUSTOM_NAME="custom_chip"
```

下文以`goldfish`为例

---
**`arm_boot()`**
- **`up_perf_init()`**
- **`goldfish_setupmappings()`**: 设置FLASH、IO、PCIE、DDR的映射
- **`arm_fpuconfig()`**: 配置FPU
- **`arm_psci_init()`**: 配置PSCI，一种电源管理接口
- **`fdt_register()`**: 指定设备树位置
- ... 初始化串口


## `nx_start()` 函数分析

`nx_start()` 是 NuttX 操作系统初始化的核心函数，负责完成 RTOS 的启动和初始化。以下是其主要执行流程：

### 1. 基础初始化阶段

- **`tasklist_initialize()`**:
  - 初始化 `g_tasklisttable[NUM_TASK_STATES]` 结构体数组
  - 每个数组元素对应一种任务状态，包含指向相应任务链表的指针和属性标志
  - 例如：
    - `TSTATE_TASK_READYTORUN` 指向就绪队列 `g_readytorun`
    - `TSTATE_TASK_RUNNING` 指向运行队列
    - `TSTATE_WAIT_SEM` 指向信号量等待队列

- **`drivers_early_initialize()`**:
  - 初始化系统启动阶段必需的底层驱动
  - 通常包括串口、时钟等基础外设

### 2. 核心子系统初始化

- **`nxsem_initialize()`**:
  - 初始化信号量子系统
  - 为后续其他子系统提供同步机制支持

- **内存管理系统初始化**:
  - **`kumm_initialize()`** (可选):
    - 初始化用户空间堆内存
    - 调用 `up_allocate_heap()` 获取用户堆的起始地址和大小
    - 内部调用 `mm_initialize_pool()` 初始化内存池

  - **`kmm_initialize()`** (默认启用):
    - 初始化内核空间堆内存
    - 调用 `up_allocate_kheap()` 获取内核堆信息
    - 同样使用 `mm_initialize_pool()` 初始化内存池

  - **`mm_pginitialize()`** (可选):
    - 初始化页分配器
    - 调用 `up_allocate_pgheap()` 获取页堆信息
    - 使用伙伴分配器管理物理页

- **`idle_group_initialize()`**:
  - 为每个CPU初始化空闲任务(Idle Task)
  - 设置PID为0
  - 初始化任务控制块(TCB)
  - 配置任务本地存储(TLS)

### 3. 其他子系统初始化

- **文件系统**:
  - `fs_initialize()` - 初始化虚拟文件系统

- **中断系统**:
  - `irq_initialize()` - 设置中断处理框架

- **时钟系统**:
  - `clock_initialize()` - 初始化系统时钟
  - `timer_initialize()` - 初始化POSIX定时器(如果启用)

- **信号系统**:
  - `nxsig_initialize()` - 初始化信号处理机制

- **网络系统** (如果启用):
  - `net_initialize()` - 初始化网络协议栈

- **二进制格式**:
  - `binfmt_initialize()` - 初始化可执行文件加载器

### 4. 硬件初始化

- **`up_initialize()`**:
  - 架构特定的硬件初始化
  - 设置中断服务例程
  - 启动系统时钟等

- **`drivers_initialize()`**:
  - 初始化标准设备驱动

- **`board_early_initialize()`** (可选):
  - 板级特定早期初始化

### 5. 多任务启动

- **SMP支持** (如果启用):
  - `nx_smp_start()` - 启动其他CPU核心

- **系统启动**:
  - `nx_bringup()` - 创建初始任务并启动系统
    - `nx_create_initthread()` - 会
      - `nx_start_application()`

### 6. 进入空闲循环

- **`up_idle()`**:
  - 处理器特定的空闲状态处理
  - 通常实现为低功耗等待指令
