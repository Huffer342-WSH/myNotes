---
layout: post
title: 如何给各种软件设置代理
date: 2025-09-22 10:53:13
categories: [教程]
excerpt:
hide: false
---

以下均用`127.0.0.1:7890`代替代理的地址

## git

```sh
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy http://127.0.0.1:7890
```

## npm、pnpm

```sh
npm config set proxy http://127.0.0.1:7890
npm config set https-proxy http://127.0.0.1:7890
```

## pip、conda

### 换源

可以选清华源、中科大源等
- [中科大anaconda](https://mirrors.ustc.edu.cn/help/anaconda.html)
- [清华anaconda](https://mirrors.tuna.tsinghua.edu.cn/help/anaconda/)
- [中科大pip](https://mirrors.ustc.edu.cn/help/pypi.html)
- [清华pip](https://mirrors.tuna.tsinghua.edu.cn/help/pypi/)

但是某校网被清华源拉黑了，所以用的腾讯源

```sh
pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple
```

### 代理

```sh
pip install <package> --proxy="http://127.0.0.1:7890"
```
