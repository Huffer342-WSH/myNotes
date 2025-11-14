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

可以选清华源、中科大源、浙大源等

`.condarc`:
```yaml
show_channel_urls: true
auto_activate: false
default_channels:
  - https://mirrors.zju.edu.cn/anaconda/pkgs/main
  - https://mirrors.zju.edu.cn/anaconda/pkgs/r
  - https://mirrors.zju.edu.cn/anaconda/pkgs/msys2
custom_channels:
  conda-forge: https://mirrors.zju.edu.cn/anaconda/cloud
  msys2: https://mirrors.zju.edu.cn/anaconda/cloud
  bioconda: https://mirrors.zju.edu.cn/anaconda/cloud
  menpo: https://mirrors.zju.edu.cn/anaconda/cloud
  pytorch: https://mirrors.zju.edu.cn/anaconda/cloud
  pytorch-lts: https://mirrors.zju.edu.cn/anaconda/cloud
  simpleitk: https://mirrors.zju.edu.cn/anaconda/cloud
  nvidia: https://mirrors.zju.edu.cn/anaconda-r
```


```sh
pip config set global.index-url https://mirrors.zju.edu.cn/pypi/web/simple
```

`cuda版pytorch`
```sh
pip3 install torch torchvision -f https://mirrors.aliyun.com/pytorch-wheels/cu130
```

### 代理

```sh
pip install <package> --proxy="http://127.0.0.1:7890"
```
