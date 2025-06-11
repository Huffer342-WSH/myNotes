---
layout: post
title: nsh启动应用的过程
date: 2025-06-09 14:24:28
categories: [nuttx]
excerpt:
hide: false
---


## 函数调用

**用户空间：**
- nsh_session()
  - nsh_parse()
    - nsh_parse_command()
      - nsh_execute()
        - nsh_fileapp()
          - posix_spawn() in 'PROXY_posix_spawn.c'

nsh一系列的函数主要用于解析命令行，得到argc、argv等参数，然后通过`posix_spawn()`新建任务。

在启用了`KERNAL_BUILD`的情况下，用户空间不能直接调用nuttx内核提供的的`posix_spawn()`函数，而是通过节点(PROXY)传递需要调用函数序号(SYS_posix_spawn)和参数进svc中断，在svc中断中根据函数序号找到内核中的函数并调用

用户空间的`posix_spawn`函数如下，调用该函数后进入svc中断
```c
#  define sys_call6(nbr, parm1, parm2, parm3, parm4, parm5, parm6) \
({                                                                 \
  register uintptr_t reg6 __asm__("r6") = (uintptr_t)(parm6);      \
  register uintptr_t reg5 __asm__("r5") = (uintptr_t)(parm5);      \
  register uintptr_t reg4 __asm__("r4") = (uintptr_t)(parm4);      \
  register uintptr_t reg3 __asm__("r3") = (uintptr_t)(parm3);      \
  register uintptr_t reg2 __asm__("r2") = (uintptr_t)(parm2);      \
  register uintptr_t reg1 __asm__("r1") = (uintptr_t)(parm1);      \
  register uintptr_t reg0 __asm__("r0") = (uintptr_t)(nbr);        \
  __asm__ __volatile__                                             \
  (                                                                \
    "svc %1"                                                       \
    : "=r"(reg0)                                                   \
    : "i"(SYS_syscall), "r"(reg0), "r"(reg1), "r"(reg2),           \
      "r"(reg3), "r"(reg4), "r"(reg5), "r"(reg6)                   \
    : "memory"                                                     \
  );                                                               \
  reg0;                                                            \
})

int posix_spawn(FAR pid_t * parm1, FAR const char * parm2, FAR const posix_spawn_file_actions_t * parm3, FAR const posix_spawnattr_t * parm4, FAR char * const parm5[], FAR char * const parm6[])
{
  return (int)sys_call6((unsigned int)SYS_posix_spawn, (uintptr_t)parm1, (uintptr_t)parm2, (uintptr_t)parm3, (uintptr_t)parm4, (uintptr_t)parm5, (uintptr_t)parm6);
}
```

**内核空间**

触发svc中断时，`r0`寄存器中保存了需要的系统调用函数的序号，剩下若干个寄存器则保存了系统调用的参数。

出发svc中断后的工作如下：

- arm_syscall：svc中断函数
  - 保存LR和SPSR到sys模式栈: `srsdb		sp!, #PSR_MODE_SYS`
  - 切换到sys模式:`cpsid		if, #PSR_MODE_SYS`
  - 寄存器压栈
  - arm_syscall()，switch进入default分支
    - 修改刚才压入栈中的寄存器
  - 切换到svc模式
- dispatch_syscall()
  - 出栈恢复寄存器，作为syscall的参数
  - 从g_stublookup[]对应的syscall并执行
  - 出发svc中断，r0保存为SYS_syscall_return
- arm_syscall
  - ...
  - arm_syscall(),switch进入SYS_syscall_return分支
    - 修改刚才压入栈中的寄存器
  - 出栈，回到用户模式
