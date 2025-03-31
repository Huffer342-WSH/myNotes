---
layout: post
title: Input子系统——按键输入驱动
date: 2025-03-30 15:10:49
categories: [Linux]
excerpt: 
hide: index
---

## 简述

在input子系统下的开发驱动，需要**注册一个`input_dev`设备**并**在输入设备触发时调用input_event()汇报事件**，该接口在 `<include/linux/input.h`中定义。

一般来说就是在`struct platform_driver`的`probe`函数中实现`input_dev`设备和中断的注册。


## 案例

假设现在需要将一个GPIO注册为一个按键，并使用定时器实现按键消抖，实现方案如下：

---

首先使用一个自定义的结构体**保存该设备需要用到的信息**：

```c
/* 自定义的按键设备结构体 */
struct mykey_dev {
    struct input_dev *idev;  // 按键对应的input_dev指针
    struct timer_list timer; // 消抖定时器
    int gpio;                // 按键对应的gpio编号
    int irq;                 // 按键对应的中断号
};
```

---

然后按照编写platform驱动的方式开发按键驱动，器拓扑结构如下：


注册platform驱动： module_platform_driver(mykey_driver);
- .probe = mykey_probe
    +  为自定义结构体`mykey_dev`分配内存并保存到`platform_device`结构体中
        ```c
        struct mykey_dev *key;
        key = devm_kzalloc(&pdev->dev, sizeof(struct mykey_dev), GFP_KERNEL);
        platform_set_drvdata(pdev, key);        
        ```

        其中`devm_kzalloc()`函数申请的内存会在设备`remove`时被释放，不需要手动释放。`devm`开头的函数都有这种功能，代表`设备托管（Device-Managed）`
    + 初始化按键
        ```c
        static int mykey_init(struct platform_device *pdev)
        {
            struct mykey_dev *key = platform_get_drvdata(pdev);
            struct device *dev = &pdev->dev;
            unsigned long irq_flags = 0;

            /* 从设备树中获取GPIO */
            key->gpio = of_get_named_gpio(dev->of_node, "key-gpio", 0);
            /* 申请使用GPIO */
            ret = devm_gpio_request(dev, key->gpio, "Key Gpio");
            /* 将GPIO设置为输入模式 */
            gpio_direction_input(key->gpio);
            key->irq = gpio_to_irq(key->gpio);
            /* 获取设备树中指定的中断触发类型 */
            irq_flags = irq_get_trigger_type(key->irq);
            /* 申请中断 */
            return devm_request_irq(dev, key->irq, mykey_interrupt, irq_flags, "PS_Key0 IRQ", key);
        }
        ```
        - 其中`mykey_interrupt`是`irqreturn_t (*irq_handler_t)(int, void *)`类型的中断服务函数，内部负责启动定时器
            + 定时器中断服务函数中上报按键事件并同步
                ```c
                static inline void input_report_key(struct input_dev *dev, unsigned int code, int value)
                {
	                input_event(dev, EV_KEY, code, !!value);
                }
                void input_sync(struct input_dev *dev);                
                ```
                
    + 初始化定时器
        ```c
        timer_setup(&key->timer, key_timer_function, 0);
        ```
    + 初始化 `input_dev`
        ```c
        idev = devm_input_allocate_device(&pdev->dev);
        idev->name = "mykey";
        __set_bit(EV_KEY, idev->evbit);        // 可产生按键事件
        __set_bit(EV_REP, idev->evbit);        // 可产生重复事件
        __set_bit(PS_KEY0_CODE, idev->keybit); // 可产生KEY_0按键事件
        /* 注册按键输入设备 */
        return input_register_device(idev);
        ```
    + 注册 `input_dev`
- .remove = mykey_remove
    + 获取自定义结构体
    + 删除定时器
    + 卸载 `mykey_dev`
