---
layout: post
title: 虚函数的应用
date: 2025-09-28 15:32:18
categories: [C/C++]
excerpt:
hide: false
---

## 使用

一般情况下，使用指针访问普通成员函数时，会使用指针所指类型的成员函数。
但是使用指针访问虚成员函数时，调用的时指针指向的对象的真实类型。

测试用例如下：

```c
#include <iostream>
using namespace std;

// 基类
class Base
{
public:
    void ordinary_func()
    {
        cout << "Base::ordinary_func()" << endl;
    }
    virtual void virtual_func()
    {
        cout << "Base::virtual_func()" << endl;
    }
};

// 派生类
class Derived : public Base
{
public:
    void ordinary_func()
    {
        cout << "Derived::ordinary_func()" << endl;
    }
    virtual void virtual_func()
    {
        cout << "Derived::virtual_func()" << endl;
    }
};

int main()
{
    Base* b = new Base;
    Derived* d = new Derived;
    Base* bd = d;

    b->ordinary_func();
    d->ordinary_func();
    bd->ordinary_func();

    b->virtual_func();
    d->virtual_func();
    bd->virtual_func();
    return 0;
}
```
---
**输出：**
```shell
Base::ordinary_func()
Derived::ordinary_func()
Base::ordinary_func()
Base::virtual_func()
Derived::virtual_func()
Derived::virtual_func()
```

虚函数用于实现多态，举一个例子：

卡尔曼滤波有各种不同的测量模型和状态转移模型，但是更新和滤波的流程是固定的。因此可以为测量模型和状态转移模型设计由纯虚函数构成的抽象类，规定返回矩阵F和H的函数，并在派生类中实现这些纯虚函数。由此可以实现各种类型的卡尔曼滤波。

## 实现方式

调用虚函数时无视指针类型，而是调用对象的真实类型的成员函数，很容易想到是因为包含虚函数的对象的内存中保存了对象的类型信息，添加virtual关键字后编译器不在根据指针类型来调用成员函数，而是在运行时根据对象的真实类型来调用成员函数。

下面用一个例程展示GCC实现方式：

- 类的继承都是在编译器确定的，每一个包含虚函数的类都有一个对应的虚函数表，存放在静态数据区。
- 当一个包含虚函数的对象被创建时，其内存中的第一个字是一个指向其虚函数表的指针。
- 无论以派生类还是基类指针访问虚函数时，都会先访问对象内存中的vptr，找到虚函数表，然后访问对应的虚函数

以下代码根据对象地址找到虚函数表指针，然后找到虚函数表，强转成函数指针类型直接调用对象的虚函数

```c
#include <iostream>

using namespace std;

uintptr_t* test_vtable(const char* name, uintptr_t* obj)
{
    uintptr_t* vtab;
    printf("%s addr: 0x%016x\n", name, obj);
    printf("vtable = 0x%016x\n", obj[0]);
    printf("member[0] = 0x%016x\n", obj[1]);
    printf("member[1] = 0x%016x\n", obj[2]);

    vtab = reinterpret_cast<uintptr_t*>(*obj);
    printf("tab[%d] = 0x%016x\n", 0, vtab[0]);
    printf("tab[%d] = 0x%016x\n", 1, vtab[1]);
    return vtab;
}

// 基类
class Base
{
public:
    virtual void f1()
    {
        cout << "Base::f1()" << endl;
    }
    virtual void f2()
    {
        cout << "Base::f2()" << endl;
    }
    void f3() { cout << "Base::f3()" << endl; } // 普通函数
    uintptr_t a = 0x11111111;
};

// 派生类
class Derived : public Base
{
public:
    void f1() override { cout << "Derived::f1()" << endl; }
    uintptr_t b = 0x22222222;
};

int main()
{
    Base b;
    Derived d;

    uintptr_t *tableB, *tableD;
    tableB = test_vtable("Base", reinterpret_cast<uintptr_t*>(&b));
    tableD = test_vtable("Derived", reinterpret_cast<uintptr_t*>(&d));

    cout << "=== 通过函数指针访问成员函数 ===" << endl;
    using FnB = void (*)(Base*);
    (reinterpret_cast<FnB>(tableB[0]))(&b);
    (reinterpret_cast<FnB>(tableB[1]))(&b);

    using FnD = void (*)(Derived*);
    (reinterpret_cast<FnD>(tableD[0]))(&d);
    (reinterpret_cast<FnD>(tableD[1]))(&d);

    return 0;
}
```


```shell
Base addr: 0x000000000fdffad0
vtable = 0x00000000a4a25bd0
member[0] = 0x0000000011111111
member[1] = 0x0000000008bf6a95
tab[0] = 0x00000000a49b5c10
tab[1] = 0x00000000a49b5c50
Derived addr: 0x000000000fdffab0
vtable = 0x00000000a4a25bf0
member[0] = 0x0000000011111111
member[1] = 0x0000000022222222
tab[0] = 0x00000000a49b5c90
tab[1] = 0x00000000a49b5c50
=== 通过函数指针访问成员函数 ===
Base::f1()
Base::f2()
Derived::f1()
Base::f2()
```

可以看到Base的虚函数表中
