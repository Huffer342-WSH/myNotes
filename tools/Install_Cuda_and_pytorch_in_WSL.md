---
layout: post
title: WSL2中安装Cuda和Pytorch
date: 2024-08-31 21:55:00
excerpt: 记录一下怎么在WSL2中安装的Cuda+cudnn和conda+pytorch
---

参考资料：来自[公孙启](https://www.gongsunqi.xyz/)的文章[《Windows11 + WSL Ubuntu + Pycharm + Conda for deeplearning》](https://www.gongsunqi.xyz/posts/3c995b2a/)以及对应的视频[【深度学习：wsl ubuntu安装cuda和cudnn】](https://www.bilibili.com/video/BV1Am4y1G7Pv)


教程很完整没有什么坑，该文仅作记录。

## 注意事项

### 网络问题

安装过程中可能会遇到**下载速度很慢**的问题，需要挂代理。因为用的是WSL，可以选择主机（即正在使用的windwos系统）开代理，wsl连接主机的代理端口。

给出一个现成的脚本如下：

```sh
#!/bin/bash

# 查找主机的IP地址
host_ip=$(cat /etc/resolv.conf |grep "nameserver" |cut -f 2 -d " ")

# 设置代理，其中7890修改为主机设置的代理服务器端口，
export ALL_PROXY="http://$host_ip:7890"
export http_proxy="http://$host_ip:7890"
export https_proxy="http://$host_ip:7890"
```
 
将这个脚本放在 `/etc/profile.d/` 目录下，就会在启动时自动设置代理。

设置代理后还要注意一下防火墙，设置完代理后可能网络直接卡住，这个时候可以ping一下主机，如果 WSL2 虚拟机无法 ping 通主机，但是可以 ping 通百度，说明是宿主机的防火墙没有设置 WSL 入站规则。可以登录管理员账号执行：

```powershell
New-NetFirewallRule -DisplayName "WSL" -Direction Inbound  -InterfaceAlias "vEthernet (WSL)"  -Action Allow
```

### WSL内存问题

WSl比正常使用linux更加耗内存，而且疑似存在内存泄漏，建议用一段时间后重启一下。

加入遇到内存不够无法编译的情况，少开几个线程，或者设置wsl的swap分区大小,参考[微软WSL文档](https://learn.microsoft.com/zh-cn/windows/wsl/wsl-config#example-wslconfig-file)

新建文件 `C:\Users\<UserName>\.wslconfig`，写入

```
[wsl2]
swap = 80GB
swapfile=C:\\temp\\wsl-swap.vhdx
memory = 16GB
```
具体大小视情况修改。
