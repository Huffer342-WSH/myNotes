---
layout: post
title: 求职笔记 . 面经
date: 2025-04-15 16:16:32
categories: ["求职笔记"]
excerpt: 
hide: index
---


## 嵌入式-kernel

### 如何检查栈溢出、如何获取最大栈深度

检测最大深度是检测栈溢出的子集，可以得到最大深度就一定能判断是否溢出，只要判断是否溢出则会有一些特殊优化的方法

想要获取最大栈深度，可选的方法有：
1. 给栈填充magic字节，通过检查多少magic字节没有被修改获取没有使用的栈空间。
2. 通过函数`进入/退出 钩子`，例如GCC的`-finstrument-functions`选项，编译器会在每个函数入口和出口插入对 `__cyg_profile_func_enter` 和 `__cyg_profile_func_exit` 的调用。

对于检测栈溢出来说，可选的方法有：
1. 仅仅在栈的末尾添加magic字节，检查magic字节是否被修改；FreeRTOS中的栈溢出检查就是用这种方法
2. 在链接脚本中将栈设置到RAM的开头，栈向下增长溢出后触发hardfault
3. 通过MPU等硬件实现内存空间访问保护

--- 

这里重点讲一下**函数的`进入/退出 钩子`**

在 C 语言层面，主流编译器都提供了“函数级”自动插桩（instrumentation）机制，能够在每个函数入口和出口自动插入用户定义的钩子函数。下面是几种常见方案：

1. **GCC / Clang**：`-finstrument-functions`

- **功能**
    使用`-finstrument-functions`选项后，编译器会在函数的如口和出口处分别调用：
    ```c
    void __cyg_profile_func_enter (void *this_fn, void *call_site);
    void __cyg_profile_func_exit  (void *this_fn, void *call_site);
    ```
    函数的第一个参数是是当前函数起始地址，可以再符号表中查找
    >添加`__attribute__((no_instrument_function))`的函数不会进行插桩


2. **MSVC（Visual C++）**：`/Gh` 与 `/GH`

- **用法**：在项目的“C/C++ → 命令行”中添加  
  ```
  /Gh    // 在每个函数入口调用 _penter
  /GH    // 在每个函数出口调用 _pexit
  ```
- **钩子函数**：用户需自己提供  
  ```c
  // 入口钩子
  void __declspec(naked) __cdecl _penter(void);
  // 出口钩子
  void __declspec(naked) __cdecl _pexit(void);
  ```

---

#### instrument-functions 案例
下面给出一个具体的例子

源文件`instrument-functions.c`代码如下

```c
/**
 * instrument-functions.c
 * gcc -finstrument-functions -O0 -g -o instrument instrument-functions.c
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <inttypes.h>

static uintptr_t stack_base;
static uintptr_t stack_lowest = ~(uintptr_t)0;
static int call_depth = 0;

// 获取当前栈指针
__attribute__((always_inline)) __attribute__((no_instrument_function)) static inline uintptr_t get_sp(void)
{
    uintptr_t sp;
    __asm__ volatile("mov %%rsp, %0" : "=r"(sp));
    return sp;
}

// 记录初始栈顶
__attribute__((constructor)) __attribute__((no_instrument_function)) static void record_stack_base(void)
{
    stack_base = get_sp();
}

// 函数入口钩子
void __attribute__((no_instrument_function)) __cyg_profile_func_enter(void *this_fn, void *call_site)
{
    uintptr_t sp = get_sp();
    call_depth++;
    if (sp < stack_lowest) {
        stack_lowest = sp;
    }

    printf("%*s[ENTER] SP=0x%" PRIxPTR " FUNC=0x%" PRIxPTR " CALLER=0x%" PRIxPTR "\n", call_depth * 2, "", sp, (uintptr_t)this_fn, (uintptr_t)call_site);
}

// 函数出口钩子
void __attribute__((no_instrument_function)) __cyg_profile_func_exit(void *this_fn, void *call_site)
{
    call_depth--;
}

// 模拟调用栈增长
void deep_recursion(int n)
{
    char buf[100];
    if (n > 0) {
        deep_recursion(n - 1);
    }
}

void func_a()
{
    ;
    return;
}

void func_b()
{
    func_a();
    func_a();
    return;
}

void func_c()
{
    func_b();
    func_b();
    return;
}

int main(void)
{
    printf("Initial SP: 0x%" PRIxPTR "\n", stack_base);
    deep_recursion(4);
    func_c();
    printf("Deepest SP: 0x%" PRIxPTR "\n", stack_lowest);
    printf("Stack usage: %" PRIuPTR " bytes\n", stack_base - stack_lowest);
    return 0;
}

```

编译：
```sh
gcc -finstrument-functions -O0 -g -o instrument instrument-functions.c
```

**运行结果：**

```sh
$ ./instrument
  [ENTER] SP=0x7ffee07bc6d0 FUNC=0x4012be CALLER=0x7f10c4858083
Initial SP: 0x7ffee07bc6d0
    [ENTER] SP=0x7ffee07bc640 FUNC=0x4011d8 CALLER=0x4012fb
      [ENTER] SP=0x7ffee07bc5b0 FUNC=0x4011d8 CALLER=0x401207
        [ENTER] SP=0x7ffee07bc520 FUNC=0x4011d8 CALLER=0x401207
          [ENTER] SP=0x7ffee07bc490 FUNC=0x4011d8 CALLER=0x401207
            [ENTER] SP=0x7ffee07bc400 FUNC=0x4011d8 CALLER=0x401207
    [ENTER] SP=0x7ffee07bc6c0 FUNC=0x401281 CALLER=0x401305
      [ENTER] SP=0x7ffee07bc6b0 FUNC=0x401244 CALLER=0x4012a0
        [ENTER] SP=0x7ffee07bc6a0 FUNC=0x40121b CALLER=0x401263
        [ENTER] SP=0x7ffee07bc6a0 FUNC=0x40121b CALLER=0x40126d
      [ENTER] SP=0x7ffee07bc6b0 FUNC=0x401244 CALLER=0x4012aa
        [ENTER] SP=0x7ffee07bc6a0 FUNC=0x40121b CALLER=0x401263
        [ENTER] SP=0x7ffee07bc6a0 FUNC=0x40121b CALLER=0x40126d
Deepest SP: 0x7ffee07bc400
Stack usage: 720 bytes
```

**验证:**

使用`nm`查看符号表，根据上文中`instrument`打印内容中`FUNC=0x40121b`的地址查询对应的符号，结果如下：
```sh
$ nm ./instrument | grep 4012be
00000000004012be T main

$ nm ./instrument | grep 4011d8
00000000004011d8 T deep_recursion
```

---


### 如何检查堆溢出
