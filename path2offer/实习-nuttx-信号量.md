---
layout: post
title: NuttX 互斥锁（mutex）模块bug修复
date: 2026-04-07 00:04:00
categories: [求职笔记]
excerpt:
hide: index
---

> 开源的东西应该写出来也没事吧🤓

## 工作背景

我在实习期间处理的第二条主线集中在 `sched/semaphore`。这里需要先说明一个前提：在 NuttX 中，`mutex` 并不是完全独立的一套底层实现，而是复用 `sem` 的内部等待 / 唤醒机制；因此相关修改虽然都落在 `sched/semaphore` 目录中，但我关注的重点其实是 `mutex` 语义路径上的状态一致性问题。

这组问题的难点不在普通参数校验，而在于：

- `mutex` 的 owner 状态保存在 `sem` 的 `mholder` 中
- `mholder` 里既编码了 holder pid，也编码了 `NXSEM_MBLOCKING_BIT`
- 是否有人在等锁，还体现在 `SEM_WAITLIST(sem)` 中
- 超时、信号、中断、解锁唤醒都可能并发改变这些状态

因此，真正要解决的是：`holder`、`blocking bit`、`waitlist` 这三部分信息，是否在所有路径上保持一致。

## `mutex` 在 NuttX 里的工作原理

### 1. 初始化

`nxmutex_init()` 本质上是对 `sem` 的封装：

- 先调用 `nxsem_init(&mutex->sem, 0, NXSEM_NO_MHOLDER)`
- 再通过 `nxsem_set_protocol()` 把这个 `sem` 标记为 `SEM_TYPE_MUTEX`
- 如果启用了优先级继承，还会附带 `SEM_PRIO_INHERIT`

所以从数据结构上看，`mutex_t` 里面包的是一个 `sem_t`，只是这个 `sem_t` 被赋予了 mutex 语义。

### 2. 如何拿到锁

调用链上，`nxmutex_lock()` / `nxmutex_clocklock()` 最终都会进入 `nxsem_wait()` / `nxsem_clockwait()`。

拿锁大体分两种情况：

- 没有竞争时，直接获取锁
- 已有 holder 时，当前线程进入等待

在 `nxsem_wait_slow()` 的 mutex 路径里，代码会先对 `NXSEM_MHOLDER(sem)` 做 `atomic_fetch_or(..., NXSEM_MBLOCKING_BIT)`：

- 如果旧值里没有有效 holder，说明锁当前可获取
- 如果旧值里已经有 holder，就说明当前线程需要阻塞等待

对于无竞争场景，当前线程在通过 `nxsem_protect_wait()` 之后，会把 `mholder` 设置成自己的 `pid`，如果此时等待队列非空，还会把 `NXSEM_MBLOCKING_BIT` 一起带上。

### 3. 拿不到锁时如何阻塞

如果 mutex 已经被其他线程持有，`nxsem_wait_slow()` 会进入阻塞流程：

- 在 `rtcb->waitobj` 中记录当前等待的 `sem`
- 如果启用了优先级继承，则通过 `nxsem_boost_priority()` 提升当前 holder 的优先级
- 把当前线程从运行队列移除
- 按优先级插入 `SEM_WAITLIST(sem)`
- 执行上下文切换，线程睡眠

这里有一个容易混淆但很重要的点：对于 mutex，等待线程被唤醒后并不是自己再去“补写 holder”；真正的 owner 交接动作发生在解锁路径里。

### 4. 解锁后如何唤醒下一个等待线程

调用 `nxmutex_unlock()` 最终会进入 `nxsem_post()` / `nxsem_post_slow()`。

在 mutex 路径下，`nxsem_post_slow()` 会做几件关键事情：

- 先把 `NXSEM_MBLOCKING_BIT` 设上，锁住当前 mutex 状态
- 检查当前调用线程是否就是 holder
- 释放当前 holder 的优先级继承相关记录
- 从 `SEM_WAITLIST(sem)` 中取出优先级最高的等待线程
- 直接把 `mholder` 设置成这个等待线程的 `pid`
- 如果等待队列里还有别人，再把 `NXSEM_MBLOCKING_BIT` 保留下来
- 清空被唤醒线程的 `waitobj`，把它放回 ready-to-run 队列

也就是说，mutex 的 owner 切换是在 `nxsem_post_slow()` 中完成的，不是等等待线程真正恢复运行之后才完成。

### 5. 超时 / 信号到来时如何清理

如果等待中的线程超时，`nxsem_timeout()` 会调用 `nxsem_wait_irq(wtcb, ETIMEDOUT)`；如果被信号打断，也会进入 `nxsem_wait_irq()`。

这条路径负责把“已经等待但尚未拿到锁”的线程从 sem 机制里清理出去，核心动作包括：

- 调用 `nxsem_canceled()` 恢复 holder 的优先级
- 从 `SEM_WAITLIST(sem)` 中移除等待线程
- 对 counting sem，恢复 `semcount`
- 对 mutex，如果等待队列已经空了，就清掉 `NXSEM_MBLOCKING_BIT`
- 给等待线程设置 `errcode`
- 把线程重新放回 ready-to-run 队列

这条路径的关键在于：它处理的是“等待失败后的状态收尾”，而不是 owner 转移。

## 修改一：修复 `nxsem_wait_irq()` 早返回路径未恢复 `addrenv`

### 问题表现

`nxsem_wait_irq()` 在某些场景下会提前返回。原实现中，对于 mutex 且错误码为 `EINTR` 或 `ECANCELED` 的路径，函数在返回前没有恢复 `addrenv`，导致线程地址环境切换不成对。

### 根因

这是一个典型的异常路径遗漏问题。问题本身不复杂，但隐藏得很深，因为它只出现在较窄的错误分支里，而且只有在具备独立地址环境的线程上才会暴露。

### 修改方案

我在这条早返回路径上补齐了 `addrenv_restore()`，保证无论是否提前返回，地址环境切换都能成对完成。

对应提交：

- `ca99f5b37a`
  修复点：修复 `nxsem_wait_irq()` 在 `EINTR` / `ECANCELED` 路径下未恢复 `addrenv` 的问题。
  价值：保证异常路径上的上下文恢复完整，避免线程环境被错误遗留。

## 修改二：修复 mutex 等待失败路径上的状态一致性问题

这组问题是整个专题里最核心、也最容易误判的一部分。回头看，它不是一个单点 bug，而是一条“从表象定位到真正根因”的排查过程。

### 最初观察到的现象

在 `nxmutex_clocklock()` 超时返回的场景里，我最开始观察到的现象是：

- 等待线程从 `nxsem_wait_slow()` 恢复时带着错误码返回
- 但 mutex 的 `blocking bit` 看起来没有随着等待者消失而正确更新

基于这个现象，我最初把注意力放在了 `nxsem_wait_slow()` 恢复返回之后的状态修正上。

### 第一阶段尝试：在 `nxsem_wait_slow()` 返回时补状态

我首先做了 `bf89278be8`，尝试在 `nxsem_wait_slow()` 从等待恢复、并以错误返回时，根据 `SEM_WAITLIST(sem)` 是否为空来更新 `NXSEM_MBLOCKING_BIT`。

这个思路解决了“返回后看到的状态不对”这个表面现象，但后来重新梳理代码路径时我意识到，它并没有抓到真正的问题位置。因为当线程已经从 `nxsem_wait_irq()` 中被移出等待队列后，真正危险的窗口并不在“它恢复运行之后”，而在“它刚刚被移出等待队列、但状态位还没同步”的那一小段并发区间。

对应提交：

- `bf89278be8`
  修复点：尝试在 `nxsem_wait_slow()` 错误返回时补充 blocking bit 更新。
  价值：这是一次基于现象的初步修正，帮助我把问题收敛到 mutex 状态维护路径上，但后来确认它处理的是表象，不是最终根因。

### 第二阶段尝试：把 holder 和 blocking bit 合并成一次原子更新

沿着第一阶段的思路继续推，我又做了 `cca5b0efe4`，把 `nxsem_wait_slow()` 中 holder 和 blocking bit 的更新改成单次 compare-and-swap。

这个修改本身从并发语义上是成立的：如果真的要在这一层更新 mutex 状态，确实不能拆成多步，否则其他 CPU 可能读到半更新状态。

但问题在于，更新位置仍然选错了。即使这里做成单次原子更新，它依然发生在等待线程恢复执行之后；而在这之前，`waitlist` 早就已经在别的路径里变化了。所以它依然没有消除真正的竞争窗口。

对应提交：

- `cca5b0efe4`
  修复点：把 `nxsem_wait_slow()` 中的状态更新收敛成单次原子操作。
  价值：进一步验证了问题和状态更新原子性有关，但后来确认真正的问题不在这里更新，而在更早的清理路径。

### 真正的根因

把完整链路重新读通之后，真正的根因变得清楚了：

- 等待线程超时或被中断时，是在 `nxsem_wait_irq()` 里从 `SEM_WAITLIST(sem)` 中移除的
- 但如果 `NXSEM_MBLOCKING_BIT` 的修正放到等待线程恢复后的 `nxsem_wait_slow()` 再做
- 那么“waitlist 已经没有这个线程”与“blocking bit 还没同步”之间就会出现一个竞争窗口

这时另一个 CPU 如果正好去加锁或解锁 mutex，就可能同时观察到：

- 等待线程已经不在 waitlist 里
- 但 `mholder` 中的 blocking 信息仍然保留着旧状态

你在提交说明里写的双核时序，正是这个窗口的具体体现。

### 最终修复

真正解决问题的是 `8f9f8915e8`。这次修改不再试图在 `nxsem_wait_slow()` 返回后补状态，而是把 mutex 的 blocking bit 维护提前到 `nxsem_wait_irq()` 中，和 `dq_rem()` 放在同一个清理阶段完成：

- 先移除等待线程
- 如果等待队列已经空了，就立刻清掉 `NXSEM_MBLOCKING_BIT`
- 然后再设置 `errcode`、唤醒线程

这样做的关键价值在于：等待队列变化和 blocking bit 变化终于在同一条关键路径里完成了，不再把 waitlist 和状态位拆开到两个时刻更新。

同时，这个提交也把 `nxsem_wait_slow()` 中前一阶段增加的那段“返回后修状态”逻辑移除了，说明最终结论已经明确：前两次提交是排查过程中的中间站，真正的修复点在 `nxsem_wait_irq()`。

对应提交：

- `8f9f8915e8`
  修复点：把等待线程移除和 blocking bit 更新收敛到 `nxsem_wait_irq()` 中，修复两者之间的竞争窗口。
  价值：这是这组问题的最终根因修复，真正保证了 waitlist 与 mutex 状态位在并发视角下的一致性。

## 代表性提交总结

- `ca99f5b37a`
  独立修复异常路径上的 `addrenv` 恢复问题。

- `bf89278be8`
  第一次沿症状定位 mutex 超时返回后的状态异常，属于中间排查结论。

- `cca5b0efe4`
  继续验证状态更新原子性问题，仍属于向根因逼近的中间阶段。

- `8f9f8915e8`
  最终确认根因在 `nxsem_wait_irq()` 与 waitlist 清理路径之间，完成真正修复。

## 收获总结

这条主线给我的最大收获，不只是修了几个并发 bug，而是让我对 NuttX 中“基于 `sem` 实现的 mutex”有了比较完整的机制理解：

- 能从 `nxmutex_lock()` 一直追到 `nxsem_wait_slow()`，知道 mutex 在底层是怎么判断可获取、怎么进入等待的
- 能从 `nxmutex_unlock()` 追到 `nxsem_post_slow()`，知道 owner 切换其实发生在唤醒路径里
- 能理解等待线程超时 / 中断时，为什么必须在 `nxsem_wait_irq()` 中及时收尾，而不能把状态修正留到线程恢复运行之后
- 能区分“表象修复”和“根因修复”，并把一组连续提交讲成一次真实的排查和收敛过程
