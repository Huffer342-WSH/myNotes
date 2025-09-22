---
layout: post
title: Linux中断
date: 2025-09-22 10:34:25
categories: [Linux]
excerpt: 简单介绍Linux中断系统如何使用以及工作原理
hide: false
---


## 概述

很多资料将中断处理分为上半部和下半部，一般上半部是指在硬中断中执行的，下半部是指通过各种方式延迟执行的。
-  上半部保证该中断服务函数的实时性
- 下半部则缩短硬中断的时间，确保了其他中断的实时性

在早期的2.5版本之前Linux中是提供了`bottom half`来处理下半部的。在当前版本有以下方法来处理下半部

### 方法对比

| 特性           | **软中断（Softirq）**            | **任务队列（Tasklet）**             | **工作队列（Workqueue）**                  | **线程化中断（Threaded IRQ）**              |
| :------------- | :------------------------------- | :---------------------------------- | :----------------------------------------- | :------------------------------------------ |
| **执行上下文** | 软中断上下文或 `ksoftirqd` 线程  | 软中断上下文或 `ksoftirqd` 线程     | **内核线程上下文**                         | **专门的内核中断线程上下文**                |
| **可休眠**     | **否**                           | **否**                              | **是**                                     | **是**                                      |
| **并发性**     | 同类型软中断可并发运行于多核     | **单核内串行，不同任务队列可并发**  | **多个工作项可并行执行**（依赖于工作队列） | **多个中断线程可并行执行**（依赖于 CPU 核） |
| **调度方式**   | 内核核心代码触发                 | 中断上半部调用 `tasklet_schedule()` | 中断上半部调用 `schedule_work()`           | 在 `request_threaded_irq` 中自动管理        |
| **适用场景**   | 核心内核子系统（如网络、定时器） | 驱动中需要快速、非休眠的下半部处理  | 耗时、需要休眠或不需要原子性的下半部任务   | 驱动中更现代、更安全的下半部处理方式        |
| **易用性**     | **低**（开发者通常不直接使用）   | **中等**                            | **高**                                     | **高**                                      |

### 选择建议

- **软中断**：通常**不直接使用**，留给内核核心子系统。
- **任务队列**：如果你的下半部任务**必须非常快**且**不能休眠**，并且不希望处理多核并发问题，任务队列是合适的选择。
- **工作队列**：如果你的任务**不紧急**，且可能**耗时较长**或需要**休眠**，那么工作队列是最好的选择。
- **线程化中断**：这是一种**通用的、现代的**中断处理方案。如果你正在开发一个新的驱动程序，并且没有特别严苛的低延迟要求，**优先考虑使用线程化中断**。它将处理的复杂性从驱动中移交给了内核，使你的代码更清晰、更健壮。


## 详解

### 注册中断服务函数

相关函数声明在`include/linux/interrupt.h`中

这里介绍两个常用的函数：`request_threaded_irq` 和 `devm_request_threaded_irq`

两种函数都是用于在 Linux 内核中注册一个**线程化中断处理程序**，`devm_request_threaded_irq` 是 `request_threaded_irq` 的一个**托管（Managed）**版本，在设备卸载时自动释放资源。

---

### `request_threaded_irq`


* **功能**：这个函数用来为指定的 IRQ 号 (`irq`) 注册一个中断处理程序。它将中断处理分为两个部分：**上半部 (`handler`)** 和**下半部 (`thread_fn`)**。
* **参数**：
    * `irq`：要注册的**中断号**。
    * `handler`：**中断上半部**函数。它运行在**中断上下文**，必须快速执行且不能睡眠。如果它返回 `IRQ_WAKE_THREAD`，则会唤醒下半部线程。如果 `handler` 为 `NULL`，则整个中断处理都由下半部线程完成。
    * `thread_fn`：**中断下半部**函数。它运行在**内核线程上下文**，可以执行耗时操作，也可以睡眠。
    * `flags`：用于控制中断行为的标志，如 `IRQF_SHARED`（共享中断）或 `IRQF_ONESHOT`（仅在 `handler` 返回 `IRQ_WAKE_THREAD` 时才运行 `thread_fn`）。
    * `name`：设备名称，用于 `/proc/interrupts` 中的显示。
    * `dev`：一个唯一的标识符，用于共享中断时区分设备。
* **资源管理**：使用此函数注册的中断**必须**由开发者在适当的时机（如设备移除或驱动卸载时）**手动调用 `free_irq()` 来释放**。如果忘记释放，将导致资源泄漏。

---

### `devm_request_threaded_irq`

该函数基于`request_threaded_irq`再次封装。`devm_` 前缀表示它利用了**设备资源管理（Device Resource Management）**子系统。

* **功能**：与 `request_threaded_irq` 功能完全相同，但它将中断资源的生命周期与一个特定的设备（`struct device *dev`）绑定在一起。
* **参数**：
    * `dev`：一个指向 `struct device` 的指针。中断资源将与该设备的生命周期关联。
    * 其余参数与 `request_threaded_irq` 完全相同。
* **资源管理**：这个函数最大的优势在于**自动资源管理**。当与 `dev` 关联的设备被移除或其驱动程序被卸载时，内核会自动调用相应的**释放函数（`devm_free_irq`）**来释放中断资源。开发者**不需要手动调用 `free_irq()`**。

### 总结与选择

| 特性         | `request_threaded_irq`                                       | `devm_request_threaded_irq`                             |
| :----------- | :----------------------------------------------------------- | :------------------------------------------------------ |
| **资源管理** | **手动**管理（必须手动调用 `free_irq`）                      | **自动**管理（与设备生命周期绑定）                      |
| **适用场景** | 传统驱动或在非设备上下文（如子系统初始化）中注册中断时使用。 | **推荐在现代设备驱动中使用**，特别是在 `probe` 函数中。 |
| **健壮性**   | 如果忘记释放资源，可能导致**内存泄漏**和**系统不稳定**。     | 能够有效防止资源泄漏，使驱动代码更健壮和简洁。          |

在编写设备驱动时一般使用`devm_request_threaded_irq`就行。



### 中断执行方式

中断服务函数的执行路径可以概括为：触发中断 -> 查找中断描述结构体 -> 执行注册的handle并唤醒线程执行thread_fn(可选)

1. **`arch/../kernel/irq.c`**:

    架构层代码，将中断号irq传递到下一层
    ```c
    vector_irq()
    |-> asm_do_IRQ()
        |-> handle_IRQ()
            |-> __handle_domain_irq()
    ```

2. **`kernel/irq/irqdesc.c`**:

    该部分的函数负责找到中断号irq对应的中断描述符desc
    ```c
    __handle_domain_irq()
    |-> generic_handle_irq()
        |-> desc = irq_to_desc(irq)
        |-> generic_handle_irq_desc(desc)
            |-> desc->handle_irq(desc)
                |-> handle_irq_event(desc)

    ```

    - `struct irq_desc *irq_to_desc(unsigned int irq)`函数查找中断号`irq`对应的中断描述符`desc`
    - `void generic_handle_irq_desc(struct irq_desc *desc)`
        ```c
        static inline void generic_handle_irq_desc(struct irq_desc *desc)
        {
	        desc->handle_irq(desc);
        }
        ```

        这里执行的`handle_irq`是注册到irq_desc结构体的回调函数，在`kernel/chip.c`中定义了一些默认的回调函数，如：
        ```c
        void handle_edge_irq(struct irq_desc *desc);
        void handle_fasteoi_irq(struct irq_desc *desc);
        ...
        ```

3. **`kernel/irq/handle.c`**

    该文件中包含中断的核心处理代码，根据获取到的中断描述结构体desc进行下一步处理
    在该函数中会遍历链表`desc->action`，其中每一个action中包含了`request_threaded_irq(...,handler,thread_fn,...)`注册的中断服务函数，
    - 中断上半部`handler`由`action->handler()`立马执行
    - 中断下半部`thread_fn`则由`__irq_wake_thread`唤醒后在其他线程延迟执行

    ```c
    handle_irq_event(desc)
    |-> handle_irq_event_percpu(desc)
        |-> __handle_irq_event_percpu()
            |-> for(action: desc->action)
                {
                    action->handler()
                    __irq_wake_thread()
                }

    ```
