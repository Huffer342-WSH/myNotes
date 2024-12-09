---
layout: post
title: 数据关联-全局最近邻
date: 2024-11-22 11:35:06
categories: []
excerpt: 
hide: false
---


在多目标跟踪中，数据关联是指将最新的检测结果和被跟踪目标的预测状态关联起来。全局最近邻算法可以说是有用的算法里最简单的。

全局最近邻算法的核心思想是全局优化，通过考虑所有的观测和候选目标，找到一种整体匹配，使得总的代价最小。这里的代价常用观测向量的欧氏距离。




参考资料：

[](R. Jonker and A. Volgenant, "A shortest augmenting path algorithm for dense and spare linear assignment problems", Computing, Vol. 38, pp. 325-340, 1987.)

<div id="refer-1"></div>

[1] [DF Crouse. On implementing 2D rectangular assignment algorithms. IEEE Transactions on Aerospace and Electronic Systems, 52(4):1679-1696, August 2016, DOI:10.1109/TAES.2016.140952](DOI:10.1109/TAES.2016.140952)

<div id="refer-12"></div>
[1]:  [G. Paterniani et al., "Radar-Based Monitoring of Vital Signs: A Tutorial Overview," in Proceedings of the IEEE, vol. 111, no. 3, pp. 277-317, March 2023, doi: 10.1109/JPROC.2023.3244362.](https://github.com/scipy/scipy/blob/main/scipy/optimize/rectangular_lsap/rectangular_lsap.cpp)
