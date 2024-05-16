---
layout: post
title: 将markdown文件中的图片转化为webp
date: 2024-06-01 16:40:00
excerpt: 写了一个python脚本用来压缩并替换markdown文件中引用的图片。
---

为了加快网页加载速度，想把博客中的图片压缩成webp格式的。所以写了一个python脚本用来压缩并替换markdown文件中引用的图片。

脚本的GitHub地址：[convert_images_to_webp_for_markdown](https://github.com/Huffer342-WSH/convert_images_to_webp_for_markdown)


## 关于这个脚本

这个脚本使用的正则表达式匹配的图片链接，所以漏洞应该挺多的。

脚本先对文本分块，分成文本块和代码块，然后再文本块中用正则表达式搜索并替换图片链接。

## 碎碎念

讲道理这个功能应该在markdown翻译成html的时候实现，[valaxy博客框架](https://valaxy.site/)也提供了[钩子](https://valaxy.site/guide/custom/hooks)，无奈我是个写c语言的，对ts是一窍不通，所以先写个python脚本凑合一下了。实际上这个python脚本一大半也是ChatGPT写的。
