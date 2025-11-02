---
layout: post
title: DRM框架下LCD驱动编写(Xilinx版)
date: 2025-04-02 19:30:12
categories: [Linux]
excerpt:
hide: false
---

直接渲染管理器(Direct Rendering Manager,DRM)，用户空间程序可以通过DRM API使用GPU。


在Zynq7010上搭建LCD显示接口时，Xilinx提供了IP核和对应的DRM驱动：

- **Video Frame Buffer Read**：通过AXI4接口从PS段的DDR搬运数据到PL端，在`drivers/dma/xilinx/xilinx_frmbuf.c`中将给设备注册成一个DMA设备
- 和`Video Timing Controller`


## Component框架

由于DRM框架设计到多个子设备，因此涉及到Component框架。Component框架用于确保多个组件按顺序加载。

Component框架下分两种设备：master和component，对应一下两个函数
- `int component_master_add_with_match(struct device *, const struct component_master_ops *, struct component_match *)`
- `int component_add(struct device *, const struct component_ops *)`

使用Component框架的流程如下
1. **子设备注册组件**：
   - 每个子设备的驱动程序在其 `probe` 函数中调用 `component_add()`，注册自身为组件。
   - 在调用 `component_add()` 时，需要提供 `component_ops` 结构体，其中包含该组件的 `bind` 和 `unbind` 回调函数。

2. **主设备注册匹配信息**：
   - 主设备的驱动程序在其 `probe` 函数中，使用 `component_match_add()` 为所需的每个子设备添加匹配项，构建匹配列表。
   - 随后，调用 `component_master_add_with_match()` 注册自身为聚合驱动，并提供 `component_master_ops` 结构体，其中包含主设备的 `bind` 和 `unbind` 回调函数。

3. **触发主设备的 `bind` 回调**：
   - 当所有匹配的子设备都已注册（即所有必要的组件都已添加）后，Component 框架会调用主设备驱动程序的 `bind` 回调函数。
   - 在主设备的 `bind` 回调函数中，通常执行以下步骤：
     - 分配并初始化聚合驱动的数据结构。
     - 调用 `component_bind_all()`，这将触发所有子设备组件的 `bind` 回调函数。
     - 完成聚合驱动的其他初始化步骤，并将其注册到相应的子系统中。


## 程序框架

该应用基于Xilinx的IP核和对应的内核代码，位于`drivers/gpu/drm/xlnx/`目录下

Xilinx的DRM驱动分几个步骤
1. `xlnx,pl-disp`设备probe会创建一个`xlnx-drm`设备作为master，`xlnx-drm`的probe会根据设备树节点的ports属性添加component
2. 其他子设备probe并注册自己的`bind()`函数
3. 所有子设备都probe后按顺序执行`bind()`函数，最后执行`xlnx-drm`的`bind()`函数，注册一个DRM设备

4. 需要一个compatible为`"xlnx,pl-disp"`的设备树节点，代表PL端的显示接口，触发xlnx_pl_disp.c中的挂载函数，准备创建`xlnx-drm`设备
5. xlnx_drv.c中的`xlnx_platform_probe()`会根据设备树节点中的ports属性，添加DRM框架下的各个组件(component)，并注册所有组件probe后的回调函数`xlnx_bind()`
6. 各个子设备在设备树中需要有对应的节点用于触发probe函数，在各自的probe函数中通过`component_add()`注册真正的设备初始化函数`bind()`
7. xlnx_bind()调用`component_bind_all()`执行所有子组件的`bind()`，最终完成DRM设备注册

### xlnx_drv.c

该文件是Xilinx DRM系统的核心，负责连接其他显示IP核，组成完整的DRM设备

该文件注册`module_init(xlnx_drm_drv_init);`
功能有：
1. xlnx_drm_drv_init()函数注册了platform_driver驱动`xlnx-drm`，其他驱动可以xlnx_drm_pipeline_init()创建一个`xlnx-drm`设备，触发probe函数
2. `xlnx-drm`设备的probe函数中调用`xlnx_of_component_probe()`可以根据设备书节点的属性添加所有的component
3. 所有component都probe完成后自动调用`xlnx_bind()`

### xlnx_pl_disp.c

对应PL端所有的显示设备IP核，主要负责CRTC和Plane设备的注册

**`xlnx_pl_disp_probe()`**

1. 从设备树获取硬件信息
   - 获取DMA通道
   - 颜色格式
   - 获取VTC Bridge 设备，在创建CRTC设备时需要用到
2. 将当前设备xlnx-pl-disp注册为一个component
3. 创建并出发DRM Master("xlnx-drm")


**`bind():`**
1. 创建并注册DRM Plane
2. 创建并注册DRM CRTC


### 用户实现DRM Encoder和DRM Connector
