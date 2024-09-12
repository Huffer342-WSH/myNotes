---
layout: post
title: 对比numpy.arange 和 numpy.linspace
date: 2024-9-12 15:40:00
categories: [细枝末节]
excerpt: numpy.arange会因为浮点数的精度问题导致数组的长度和预想的不一样
---

我写的一个用来生成雷达仿真信号的函数中偶然出现了数组运算时大小不匹配的问题，最后排查到是np.arange的问题。np.arange在步长是浮点数，且终点时步长的整数倍时，有时会因为浮点数的精度问题导致生成的数组居然包含了终点，预想的长一点。

解决方案是使用会指定数组长度的 `np.linspace`；不知道matlab会不会犯一样的毛病。

## 精度和浮点数问题

- **`np.arange`**
  - 当 `step` 是浮点数时，浮点精度问题可能导致最后一个元素接近但不等于 `stop`，从而影响数组长度或数值。
  - 例如：
    ```python
    step = 118e-6
    x = np.arange(0,10*step,step)
    y = np.arange(0,11*step,step)
    print(f"x.shape:{x.shape}, x:{x}")
    print(f"y.shape:{y.shape}, y:{x}")
    ```
    会输出
    ```
    x.shape:(11,), x:[0.       0.000118 0.000236 0.000354 0.000472 0.00059  0.000708 0.000826 0.000944 0.001062 0.00118 ]

    y.shape:(11,), y:[0.       0.000118 0.000236 0.000354 0.000472 0.00059  0.000708 0.000826 0.000944 0.001062 0.00118 ]
    ```
    
    x的长度并不是我们预想的10,而是11。

- **`np.linspace`**
  - `linspace` 不存在这种浮点数精度问题，因为它根据元素数量计算出精确的步长，因此能够确保精确生成的数值。
  - 默认情况下，`stop` **包含在内**。不过可以通过设置 `endpoint=False` 来排除终点。
  
  示例：
  ```python
  arr = np.linspace(0, 1, 5, endpoint=False)
  print(arr)  # Output: [0.  0.2 0.4 0.6 0.8]
  ```

##  **是否包含终点**

- **`np.arange`**
  - **终点不包含**，即生成的数组不会包含 `stop` 值。
  
- **`np.linspace`**
  - 默认情况下，`stop` **包含在内**。不过可以通过设置 `endpoint=False` 来排除终点。
  
  示例：
  ```python
  arr = np.linspace(0, 1, 5, endpoint=False)
  print(arr)  # Output: [0.  0.2 0.4 0.6 0.8]
  ```



## 总结

- 使用 `np.arange`：
  - 适合生成整数的等差数列，加入需要浮点数可以先生成整数再做除法
  
- 使用 `np.linspace`：
  - 常常因为输入参数时要做一些额外的运算而被嫌弃，确实比 `np.arange` 稳健一点。
  - 需要整数的话还是建议使用 `np.arange`。
