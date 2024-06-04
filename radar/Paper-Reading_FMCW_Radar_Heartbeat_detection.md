---
layout: post
title: 论文阅读 《基于单通道 ISM 频段 FMCW 雷达的非接触式心脏活动检测》
date: 2024-06-04 16:29:00
excerpt_type: html
categories: [信号处理算法]
---

论文地址：[《Noncontact Cardiac Activity Detection Based on Single-Channel ISM Band FMCW Radar》](https://doi.org/10.3390/bios13110982)，这篇论文是根据知识共享署名 (CC BY) 许可证的条款和条件分发的，这里所以这里还拷贝了一份 [点击跳转](./paper/基于单通道%20ISM%20频段%20FMCW%20雷达的非接触式心脏活动检测.pdf)

## 概述



## 

>For FMCW radar, the phase of the beat signal from the target varies linearly with distance. When the target’s position changes by half a wavelength relative to the radar, the phase will shift by 2π.

毫米波雷达的接收信号的相位对目标的位置变化很敏感。因为电磁波传播是一个来回，距离差是物体距离差的两倍，所以两个物体距离差半个波长，相位就会变化2π。当然这是对定频雷达而言的，假如发射信号是调频的，不同时间的两个物体回波的相位差就不是固定的了。

这里简单计算一下 ，看一下调频对相位差的影响有多少：

$$
\begin{align}
    \Phi_{t}(t) &= f_{c} t + \frac{B}{2 T_{chrip}}t^{2} \\
    \Phi_{r}(t) &= \Phi_{t}(t-\tau) = f_{c} (t-\tau) + \frac{B}{2 T_{chrip}}(t-\tau)^{2} \\
    \Phi_{mix}(t) &= \Phi_{t}(t) - \Phi_{r}(t)  = f_{c} \tau  + \frac{B}{2 T_{chrip}}(2t\tau-\tau^{2}) \\
    \Phi_{\Delta}(t)&= f_{c} (\tau_{1}-\tau_{2}) + \frac{B}{2 T_{chrip}}(\tau_{1}^{2}-\tau_{2}^{2}+2(\tau_{2}-\tau_{1})t) \\
\end{align}                                            
$$

其中 $t$ 的取值范围是 $[0,T_{chrip}]$
