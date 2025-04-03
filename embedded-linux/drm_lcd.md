---
layout: post
title: DRM框架下LCD驱动编写
date: 2025-04-02 19:30:12
categories: [Linux]
excerpt: 
hide: false
---

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
