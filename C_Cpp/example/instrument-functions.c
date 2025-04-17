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
