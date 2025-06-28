---
layout: post
title: Windows下的类unix shell
date: 2025-06-28 11:45:25
categories: [教程]
excerpt:
hide: false
---
 由于习惯问题，想要在windows使用类unix的shell。在网上搜了一堆都是些wsl和msys的方案，最后在[Starship](https://starship.rs/zh-CN/)发现了一些windws下可用的shell。

> - WSL根本不算在windows环境
> - MSYS2/CYGWIN的方案因为兼容层的问题都很卡(包括git bash)

当然只有shell是不够的，还要配上常用的工具、比如:grep、find之类的。我暂时使用的是[w64devkit](https://github.com/skeeto/w64devkit)，里面包含了busy-box基本够用。使用方法就是下载、解压、添加到PATH环境变量。

## 简单比较SHELL

目前找到了下面三个shell，正在体验...(待更新)

|     shell     |                Nushell                |             Xonsh             |             Elvish             |
| :------------: | :------------------------------------: | :----------------------------: | :-----------------------------: |
|      link      |   https://github.com/nushell/nushell   | https://github.com/xonsh/xonsh | https://github.com/elves/elvish |
| 和bash的相似性 | find为内建指令，需要alias find = ^find |                                |                                |
|  历史记录补全  |                  ✅️                  |              ✅️              |              ✅️              |
|    git补全    |             需要source脚本             |         内置，但是卡死         |         需要source脚本         |
|      问题      |                                        |          git补全卡死          |                                |

## Nushell

### 下载脚本

nushell有一个用户贡献的脚本仓库[nu_scripts](https://github.com/nushell/nu_scripts)

可以clone该仓库

```
cd  ~/AppData/Roaming/nushell
git clone https://github.com/nushell/nu_scripts.git --depth=1
```

主题、补全都可以通过source里面的脚本实现

### 配置脚本

` ~/AppData/Roaming/nushell/config.nu`

### git补全

配置脚本添加
```
source ~/AppData/Roaming/nushell/nu_scripts/custom-completions/git/git-completions.nu
```

### find指令

在Nushell中，内置的find指令实际上类似grep

**解决方案**：在 ` ~/AppData/Roaming/nushell/config.nu`中添加

```
alias find = ^find
```

`^find`代表外部的code


## Xonsh

git补全卡死，放弃
