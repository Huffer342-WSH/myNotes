#include <iostream>
#include <iomanip>

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

    /* 输出：
    Base::ordinary_func()
    Derived::ordinary_func()
    Base::ordinary_func()
    Base::virtual_func()
    Derived::virtual_func()
    Derived::virtual_func()
    */
    return 0;
}
