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
