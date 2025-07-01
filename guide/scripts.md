---
layout: post
title: 记录一些shell指令
date: 2025-07-01 10:16:45
categories: [教程]
excerpt:
hide: false
---

### 搜索静态库并查找符号

```sh
find . -name "*.a" -exec sh -c 'nm "$0" | grep -E " [Tt] get" && echo "Defined in $0"' {} \;
```
