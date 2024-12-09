---
layout: post
title: LFMCM雷达工作原理
date: 2024-05-14 13:59:03
excerpt: LFMCM雷达工作原理
categories: [信号处理算法]
---
调频连续波(Frequency Modulated Continuous Wave)雷达在交通领域、室内定位等一些民用领域应用较多。线性调频连续波（LFMCW，Linear Frequency Modulated Continuous Wave）毫米波雷达是最基础的一种毫米波雷达，一般学习都从这个入手，实际场景中使用的毫米波雷达调制方式和波束都更为复杂。



## 信号模型

![LFMCW信号时频示意图](./assets/LFMCW信号时频示意图.webp)

LFMCW雷达系统发射一个连续的波形信号，其频率随时间线性变化，形成一个锯齿波或者三角波频率调制信号。一般一个调频周期简称为一个chirp或者一个脉冲。

雷达会将接收到的反射信号与当前发射信号进行混频，产生一个差频信号（拍频信号）。差频信号的频率与目标物体的距离成正比；同一个通道，不同chirp之间的微小相位差可以反应速度信息；不同通道直接的信号差距反应目标的方向信息。

- 距离测量：通过测量差频信号的频率，可以计算出目标物体的距离。
- 速度测量：通过多次测量的相位变化，利用多普勒效应可以计算目标物体的速度。
- 角度测量：通过天线阵列和波束成形技术，可以确定目标物体的方位角。


我们处理信号的起点是混频后的信号采样后的离散数据,一般将数据排列成一个 $M×N×L$ 的三维数组
- $M$ 表示空间维的长度，表示共有 $M$ 个通道
- $N$ 表示速度（慢时间）维的长度，表示共有 $N$ 个chirp
- $L$ 表示距离（慢时间）维的长度，表示一个chirp共 $L$ 个采样点

这个三维数组被称为[radar-data-cube](https://ww2.mathworks.cn/help/phased/gs/radar-data-cube.html)。使用这个三维数组来保存数据视为了更好的区分三个维度，信号处理就是在此基础上进行的。

一般雷达会在混频时采取IQ混频，得到两路正交的数据分别作为实部和虚部组成一个复数。IQ采样的好处是可以从一个点看出信号的相位，在测角时用处很大。

具体的原理和仿真代码见 [1_LFMCW-radar-receiving-signal-simulation.md](./project/doc/1_LFMCW-radar-receiving-signal-simulation.md)


### 雷达的发射接收与混频

为了简化表达式，将场景简化为单个点目标，且令发射信号的初始相位为0，忽略信号的幅度。

---
#### 发射信号的频率表达式：
$$
f_{tx}(t) = f_{0} + k_{f}t
$$

其中 $k_{f}$ 表示调频斜率，单位一般为 $Hz/s$；
    $f_{0}$ 表示调频的初始频率。

---
#### 发射信号的相位表达式

相位是频率随时间的积分

$$
\phi_{tx}(t) = 2\pi\int_{0}^{t}{(f_{0} + k_{f}t)dx} = 2\pi(f_{0}t + \frac{1}{2}kt^{2}) 
$$

---
#### 接收信号的相位表达式

$$
\phi_{rx}(t) = \phi_{tx}(t - \tau)
$$

其中  $\tau$ 表示从发射到接收的延迟，$\tau = \frac{r}{2c}$

>对于运动目标来说 $\tau$ 是一个时变的值，但是往往因为调频脉冲的时间很短，目标运动对 $\tau$ 的影响较小，所以近似的用一个定值表示

---
#### 下混频得到的中频信号表达式

混频就是将发射信号和接收信号相乘，根据三角函数的积化和差格式可以知道混频后会有一个相位相加的高频成分和相位相减的低频成分。下混频就只取低频成分，高频成分会滤除掉。

也就是说中频信号的相位表达式就是发射信号和接收信号相减。

$$
\begin{equation}
\begin{split}
s_{IF}(t) &= \exp(j2\pi(\phi_{tx}(t) - \phi_{rx}(t)))  \\
          &= \exp(j2\pi(k_{f}\tau t + f_{0}\tau - \frac{1}{2}k_{f}\tau^{2})),  \text{其中}\tau^{2}的值很小可以忽略\\
          &≈ \exp(j2\pi(k_{f}\tau t + f_{0}\tau)) 
\end{split}
\end{equation}
$$

进一步使用 $\tau = \frac{r}{2c}$ 带入得到

$$
\begin{equation}
\begin{split}
s_{IF}(t,r) &= \exp(j2\pi(\frac{2k_{f}}{c}rt + \frac{2}{\lambda}r))  \\
          &= \exp(j(\frac{4\pi k_{f}}{c}rt + \frac{4\pi}{\lambda}r))
\end{split}
\end{equation}
$$

这里用 $e$ 的复指数形式表示，是因为实际应用中常常会使用IQ采样以提高采样频率。IQ采样使用一对正交的发射信号分别和接收信号混频，然后采样，这样可以得到一对正交的中频信号。具体可以阅读 [《PySDR-IQ 采样》](https://pysdr.org/zh/content-zh/sampling.html#)

![IQ采样](https://pysdr.org/zh/_images/IQ_diagram_rx.png)


### 雷达信号采样

我们拿到的数据是中频信号经过ADC采样后的数字信号，下文简单概述离散形式的中频信号

#### 中频数字信号时域



假设时长为 $T_{Chirp}$ 的调频周期内，等间隔采样了 $N$ 个点，则采样后的中频信号可以表示为：

$$
x[n] =  \exp(j\frac{4\pi}{\lambda}r) \cdot \exp(j \frac{4\pi k_{f} T_{Chirp}}{cN}rn)
$$

其中 $k_{f} = \frac{B}{T_{Chirp}}$ , 带入得

$$
x[n] =  \exp(j\frac{4\pi}{\lambda}r) \cdot \exp(j \frac{4\pi B }{cN}rn)
$$


>实际情况下采样不能覆盖完整的调频周期，一次会浪费一部分带宽。






#### 中频数字信号频域

$$
\begin{equation}
\begin{split}
X[n] &= \exp(j\frac{4\pi}{\lambda}r) \displaystyle\sum_{i=0}^{N-1} \exp(j \frac{4\pi B }{cN}ri)\exp(-j2\pi\frac{n}{N}i) \\
 &= \exp(j\frac{4\pi}{\lambda}r)\displaystyle\sum_{i=0}^{N-1} \exp(j (\frac{4\pi B }{cN}r - \frac{2\pi n}{N})i)
\end{split}
\end{equation}
$$


注意到这是一个几何级数求和，其形式为：
$$
\sum_{i=0}^{N-1} \exp(j \alpha i)
$$
其中 $\alpha = \frac{4\pi B r}{cN} - \frac{2\pi n}{N}$。

此时需要分为两种情况计算

**第一种情况** 

当 $\alpha = 0$ 时， 即 $r|(\frac{c}{2B})$ 时

$$
X[n] = N\exp(j\frac{4\pi}{\lambda}r) \delta(n-\frac{2Br}{c})
$$

也就是

$$
X[n] = 
 \begin{cases}
   N &, n = \frac{2Br}{c}  \\
   0 &, \text{其他}
\end{cases}
$$

**第二种情况**
当 $\alpha \neq 0$ 时

$$
\begin{equation}
\begin{split}
X[n] &= \exp\left(j\frac{4\pi}{\lambda}r\right) \cdot \frac{1 - \exp\left(j \alpha N\right)}{1 - \exp\left(j \alpha\right)} \\
&= \frac{\sin(\frac{\alpha N}{2})}{\sin(\frac{\alpha}{2})} \exp(j(\frac{4\pi}{\lambda}r + \frac{\alpha N}{2} - \frac{\alpha}{2}))
\end{split}
\end{equation}
$$



综上所述


$$
\begin{equation}
 X[n] = 
 \begin{cases}
   N\delta(n-\frac{2Br}{c}) \exp(j\frac{4\pi}{\lambda}r)  &, r|(\frac{c}{2B})\\
   \frac{\sin(\frac{\alpha N}{2})}{\sin(\frac{\alpha}{2})} \exp(j(\frac{4\pi}{\lambda}r + \frac{\alpha N}{2} - \frac{\alpha}{2})) &,\text{其他}
\end{cases}   
\end{equation}
$$

其中 $\alpha = \frac{2\pi}{N}(\frac{2B}{c}r - n)$




## 测距原理

从中频信号的频域就以及可以看出距离的影响，已知中频信号频域的表达式如下：

$$
X[n] = 
 \begin{cases}
   N\delta(n-\frac{2Br}{c}) \exp(j\frac{4\pi}{\lambda}r)  &, r|(\frac{c}{2B})\\
   \frac{\sin(\frac{\alpha N}{2})}{\sin(\frac{\alpha}{2})} \exp(j(\frac{4\pi}{\lambda}r + \frac{\alpha N}{2} - \frac{\alpha}{2})) &,\text{其他}
\end{cases}
$$


当 $n$ 使得 $\{|\frac{2B}{c}r - n|\}_{Min}$时，可以得到 $|X[n]|$ 的最大值。也就是说只需要找到使得幅度谱 $|X[n]|$ 峰值点对应的序号 $n_{k}$ , 就可以到到距离 $r = n_{k} \frac{c}{2B}$

## 测速原理



## 测距测速指标

2-D FFT 可以分离不同速度和距离的信号。一些常见的参数计算如下
在线性调频连续波 (LFMCW) 雷达系统中，速度分辨率、距离分辨率、最大测速范围和最大测距范围的计算公式如下：

### 1. **速度分辨率 (Velocity Resolution)**

速度分辨率是指雷达能够区分的最小速度差，公式为：

$$
v_{res} = \frac{\lambda}{2T_{\text{coh}}}
$$

其中：
- $v_{res}$ 是速度分辨率
- $\lambda$ 是雷达信号的波长
- $T_{\text{coh}}$ 是雷达的相干处理时间，通常是连续的多个Chirp组成的一帧数据

> 测速分辨率很直观，就是观察的时间越长，分辨率越高，非常的符合直觉。实际应用中内存足够的话只要选择够长的时间就可以满足。内存不足时可以选择降采样。

### 2. **距离分辨率 (Range Resolution)**

距离分辨率定义为雷达能够区分的最小目标距离差，公式为：

$$
R_{res} = \frac{c}{2B}
$$

其中：
- $R_{res}$ 是距离分辨率
- $c$ 是光速 $3 \times 10^8 \, \text{m/s}$
- $B$ 是有效的调频带宽，单位为赫兹 (Hz)。

>有效的调频带宽是指单个脉冲中，采样点覆盖区域的调频带宽，相比雷达扫频范围略小。值得注意的一点是基于匹配滤波的脉冲压缩雷达系统中，距离分辨率也是这个。从另一方面来讲傅里叶变换相当于对每一个距离们的信号分别做匹配滤波。 距离分辨率受限于调频带宽，而调频带宽基本是硬件受限于法律法规，往往不是我们在数字信号处理时需要考虑的。

### 3. **最大测速范围 (Maximum Velocity Range)**

最大测速范围取决于系统的脉冲重复频率 (PRF)，公式为：

$$
v_{\text{max}} = \frac{\lambda}{4T_p}
$$

其中：
- $v_{\text{max}}$ 是最大测速范围
- $\lambda$ 是波长
- $T_p$ 是脉冲重复周期。

> 控制最大测速范围主要控制Chirp的间隔。也就是说在做数字信号处理时，需要足够块的处理速度以满足最大测速范围。

### 4. **最大测距范围 (Maximum Range)**



在LFMCW雷达中，最大测距范围由雷达的带宽、采样点数以及采样率共同决定。修正后的最大测距范围公式为：

$$
R_{\text{max}} = \frac{c \cdot N}{2B}
$$

其中：
- $R_{\text{max}}$ 是最大测距范围
- $c$ 是光速 $3 \times 10^8 \, \text{m/s}$
- $N$ 是采样点数
- $B$ 是调频带宽

> 傅里叶变化中决定的测距的理论上线往往超过我们需求的测距范围，很多时候限制测距范围的是射频设备的性能。

...未完待续


## DOA估计

**波达方向估计（Direction of Arrival Estimation, DOA）**是指根据接收到的信号，在不同天线之间的相位差或振幅差等信息，估计信号来自空间中哪个方向。常见的DOA算法包括**Beamscan（波束扫描）**、**Minimum-Variance Distortionless Response (MVDR)（最小方差无失真响应）**、**MUSIC（Multiple Signal Classification，多信号分类）**、**2-D MUSIC** 和 **Root-MUSIC**。

1. **Beamscan（波束扫描）**： Beamscan算法是一种直接的DOA估计方法，它通过在不同方向上形成波束并测量每个波束的能量来确定信号来源的方向。具体来说，该算法通过在空间中的不同方向上设置波束来搜索最大响应，然后将最大响应对应的方向作为信号的到达方向。这种方法简单直观，但受限于波束的选择和分辨率。
2. **Minimum-Variance Distortionless Response (MVDR)（最小方差无失真响应）**： MVDR算法旨在最小化输出信号的方差，同时保持对预期信号方向的无失真响应。它通过计算协方差矩阵的逆来实现。MVDR算法通常在受到噪声干扰时表现出色，能够有效地抑制噪声，提高DOA估计的准确性。
3. **MUSIC（Multiple Signal Classification，多信号分类）**： MUSIC算法是一种基于子空间分解的频谱方法，通过对信号子空间进行分析，能够准确地估计出多个信号的到达方向。MUSIC算法首先通过计算传感器阵列接收到的信号的特征向量分解协方差矩阵，然后通过对特征向量的空间谱进行峰值检测来确定信号的到达方向。
4. **2-D MUSIC**： 2-D MUSIC是MUSIC算法的扩展，用于处理二维平面阵列的信号处理问题。与传统的MUSIC算法相比，2-D MUSIC可以更精确地估计出信号在二维空间中的到达方向，适用于具有更复杂几何结构的阵列。
5. **Root-MUSIC**： Root-MUSIC算法是MUSIC算法的一种变体，它通过对特征值分解的根求解方法来直接估计信号到达方向，避免了对空间谱的搜索过程。Root-MUSIC算法通常具有更高的分辨率和更快的计算速度，适用于需要实时性能的应用场景。

matlab的[Phased Array System Toolbox](https://ww2.mathworks.cn/help/phased/index.html)用于模拟传感器阵列和波束形成系统。不过里面的很多功能封装了很多层，想要直接抄代码还是有点难度。一般来说学习的时候可以自己实现一个功能然后用matlab提供的功能来验证结果。

matlab提供的函数列表可以看这个网页 [Beamforming and Direction of Arrival Estimation — Functions](https://ww2.mathworks.cn/help/phased/referencelist.html?type=function&listtype=cat&category=beamforming-and-direction-finding&blocktype=all&capability=&startrelease=&endrelease=&s_tid=CRUX_topnav)
### 关于到达矢量

想要从不同通道的接收信号中估计信号的方向，就要先知道不同位置的阵元接收到的信号到底有什么差别，而到大矢量就是用来近似的描述这个区别的。

[到达矢量 (Arrival vector)](./arrival-vector.md)

### Capon 算法

[Capon算法（MVDR 波束形成器）](./Capon-algorithm.md)

### MUSIC 算法

[MUSIC算法](./MUSIC-algorithm.md)

### ...未完待续
