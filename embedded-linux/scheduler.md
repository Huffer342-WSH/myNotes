---
layout: post
title: Linux调度器介绍
date: 2025-09-23 11:08:26
categories: [Linux]
excerpt:
hide: false
---


Linux内核提供可以下调度算法

```c
#define SCHED_OTHER		0
#define SCHED_FIFO		1
#define SCHED_RR		2
#define SCHED_BATCH		3
#define SCHED_ISO		4
#define SCHED_IDLE		5
#define SCHED_DEADLINE  6
```

---

### Linux 内核调度策略概览
以下是关于Linux内核调度方式的介绍。

### Linux 调度方式概览

| 调度方式           | 类别          | 特点                                                                                          | 适用场景                                               |
| :----------------- | :------------ | :-------------------------------------------------------------------------------------------- | :----------------------------------------------------- |
| **SCHED_OTHER**    | 普通/分时     | 默认策略，旨在公平分配CPU时间。在旧版本使用CFS，新版本采用EEVDF。                             | 绝大多数非实时应用，如日常桌面应用、服务器任务等。     |
| **SCHED_FIFO**     | 实时          | 先进先出，具有最高优先级。一旦运行，除非被更高优先级的任务抢占或主动放弃，否则会一直占用CPU。 | 对时间敏感度极高的任务，如硬实时系统。                 |
| **SCHED_RR**       | 实时          | 基于SCHED_FIFO的改进版，在同等优先级下采用时间片轮转。                                        | 多个实时任务需要轮流执行，且每个任务都应得到CPU时间。  |
| **SCHED_BATCH**    | 普通          | 类似SCHED_OTHER，但会延长任务运行时间片，减少上下文切换。                                     | 非交互式、CPU密集型后台任务，如科学计算、数据处理等。  |
| **SCHED_IDLE**     | 普通          | 最低优先级，只有当系统完全空闲时才运行。                                                      | 系统维护、垃圾回收等完全不重要的后台任务。             |
| **SCHED_DEADLINE** | 实时          | 基于任务的截止时间进行调度，最早截止时间的任务优先运行。                                      | 对时间要求非常严格且有明确截止时间限制的任务。         |
| **SCHED_ISO**      | 已废弃/非主流 | 曾是为交互性任务（如游戏、视频）设计的策略，但并未被合并到主线内核中。                        | 仅在一些打了补丁的特定内核版本中存在，通常不推荐使用。 |

---

### 详细介绍

1.  **SCHED_OTHER (SCHED_NORMAL)**
    这是 Linux 内核默认的调度策略，适用于绝大多数非实时任务。它的目标是确保所有任务都能公平地获得CPU时间，以提供良好的系统响应性。
    * **老版本：** 在Linux 2.6.23到6.5版本中，**SCHED_OTHER** 策略由**完全公平调度器（Completely Fair Scheduler, CFS）**实现。CFS通过虚拟运行时（vruntime）来跟踪每个任务的CPU使用情况，确保所有任务的vruntime值尽可能接近，从而实现“完全公平”。
    * **新版本：** 从Linux 6.6版本开始，内核开始将**SCHED_OTHER**策略逐步过渡到**最早合格虚拟截止期限优先调度器（Earliest Eligible Virtual Deadline First, EEVDF）**。EEVDF是CFS的演进版本，它引入了虚拟截止期限的概念，可以更好地处理延迟敏感型任务，提高系统的整体响应能力。

2.  **SCHED_FIFO (First In, First Out)**
    SCHED_FIFO 是一种实时调度策略，它不使用时间片。一旦一个 SCHED_FIFO 任务被调度运行，它将持续执行，直到以下情况之一发生：
    * 任务被更高优先级的实时任务抢占。
    * 任务主动放弃 CPU（例如调用 `sched_yield()`）。
    * 任务进入等待状态（如等待 I/O）。
    **SCHED_FIFO** 任务的静态优先级范围为1到99，任何实时任务的优先级都高于普通任务。

3.  **SCHED_RR (Round-Robin)**
    SCHED_RR 和 SCHED_FIFO 相似，要区别在于对于相同优先级的任务，SCHED_RR 会采用时间片轮转的方式进行调度。当一个任务的时间片用完后，它会被放到队列末尾，等待下一次被调度。这确保了相同优先级的多个实时任务都能得到公平的执行机会，避免了其中一个任务长时间霸占CPU。

4.  **SCHED_BATCH**
    SCHED_BATCH 是一种非交互式调度策略，它类似于 **SCHED_OTHER**，但会给予任务更长的时间片。这种策略的目的是为了减少上下文切换的开销，从而提高吞吐量。它通常用于那些不需要用户交互、长时间运行的CPU密集型批处理任务。

5.  **SCHED_ISO**
    SCHED_ISO 是一种非主流的调度策略，它并非Linux主线内核的一部分。它由内核开发者Con Kolivas在ck补丁集中提出，旨在为交互性任务（如游戏、视频播放）提供更好的低延迟性能。由于它没有被合并到主线内核，因此很少在通用发行版中见到。

6.  **SCHED_IDLE**
    SCHED_IDLE 是一种最低优先级的调度策略。只有当系统上没有任何其他任务可以运行时，`SCHED_IDLE` 任务才会被调度。它的优先级甚至低于具有最高“nice”值的 **SCHED_OTHER** 任务。这种策略适用于那些不重要的、可以随时被中断的后台任务，例如系统清理、垃圾回收等。

7.  **SCHED_DEADLINE**
    SCHED_DEADLINE 是 Linux 内核中最新的实时调度策略。它基于 Earliest Deadline First (EDF) 算法，并结合了 Constant Bandwidth Server (CBS) 机制。**SCHED_DEADLINE** 任务在创建时会指定三个参数：`runtime`（任务需要运行的时间）、`deadline`（任务必须完成的截止时间）和`period`（任务重复执行的周期）。调度器会优先执行具有最早截止时间的任务，以确保它们能在截止日期前完成，适用于对时间约束要求最严格的应用程序。


## 例子

### 用户

```c
#include <pthread.h>
#include <sched.h>
#include <stdio.h>
#include <stdlib.h>

// 线程要执行的函数
void *thread_policy_function(void *arg) {
  int policy;
  struct sched_param param;

  // 获取并打印当前线程的调度策略值
  if (pthread_getschedparam(pthread_self(), &policy, &param) == 0) {
    printf("Thread policy value: %d\n", policy);
  } else {
    perror("pthread_getschedparam");
  }
  return NULL;
}

int main(void) {
  pthread_t thread;
  pthread_attr_t attr;

  pthread_attr_init(&attr);
  pthread_attr_setschedpolicy(&attr, SCHED_OTHER);

  // 创建线程
  if (pthread_create(&thread, &attr, thread_policy_function, NULL) != 0) {
    perror("pthread_create");
    return 1;
  }

  pthread_join(thread, NULL);
  pthread_attr_destroy(&attr);

  return 0;
}
```


### 内核

下面是一个线程化中断的线程创建函数

```c
static int
setup_irq_thread(struct irqaction *new, unsigned int irq, bool secondary)
{
	struct task_struct *t;
	struct sched_param param = {
		.sched_priority = MAX_USER_RT_PRIO/2,
	};

	if (!secondary) {
		t = kthread_create(irq_thread, new, "irq/%d-%s", irq,
				   new->name);
	} else {
		t = kthread_create(irq_thread, new, "irq/%d-s-%s", irq,
				   new->name);
		param.sched_priority -= 1;
	}

	if (IS_ERR(t))
		return PTR_ERR(t);

	sched_setscheduler_nocheck(t, SCHED_FIFO, &param);

	new->thread = get_task_struct(t);
	set_bit(IRQTF_AFFINITY, &new->thread_flags);
	return 0;
}
```
