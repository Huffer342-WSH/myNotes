---
layout: post
title: 单一公网端口服务器的访问方案：HAProxy 流量分流与 WireGuard 隧道
date: 2025-11-28 14:28:38
categories: [教程]
excerpt:
hide: false
---

假设一个内网的服务器只有一个端口映射到离公网，目前希望实现的功能为：
1. 通过HAProxy实现SSH、RDP、HTTP分流，使用公网IP+端口直接访问这三种功能
2. wireguard虚拟局域网


## 设置SSH、RDP、HTTP分流

### 安装

```sh
sudo apt install haproxy -y
```

### 配置

打开文件
```sh
vi /etc/haproxy/haproxy.cfg
```

全选删除
```sh
:%d
```

粘贴一下配置
```yaml
# Global settings
global
    log /dev/log local0
    log /dev/log local1 notice
    chroot /var/lib/haproxy
    stats socket /run/haproxy/admin.sock mode 660 level admin expose-fd listeners
    stats timeout 30s
    user haproxy
    group haproxy
    daemon

    # Default SSL material locations
    ca-base /etc/ssl/certs
    crt-base /etc/ssl/private

    # See: https://ssl-config.mozilla.org/#server=haproxy&server-version=2.0.3&config=intermediate
    ssl-default-bind-ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384
    ssl-default-bind-ciphersuites TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256
    ssl-default-bind-options ssl-min-ver TLSv1.2 no-tls-tickets

# Default settings
defaults
    log     global
    mode    http
    option  httplog
    option  dontlognull
    timeout connect 5000ms
    timeout client  50000ms
    timeout server  50000ms
    errorfile 400 /etc/haproxy/errors/400.http
    errorfile 403 /etc/haproxy/errors/403.http
    errorfile 408 /etc/haproxy/errors/408.http
    errorfile 500 /etc/haproxy/errors/500.http
    errorfile 502 /etc/haproxy/errors/502.http
    errorfile 503 /etc/haproxy/errors/503.http
    errorfile 504 /etc/haproxy/errors/504.http

# Stream (TCP) configuration
frontend main_front
    bind *:3322
    mode tcp
    option tcplog

    tcp-request inspect-delay 3s
    acl is_http req.payload(0,3) -m bin 474554 504f53 505554 44454c 4f5054 484541 434f4e 545241
    acl is_ssh req.payload(0,3) -m bin 535348
    acl is_rdp req.payload(0,3) -m bin 030000

    tcp-request content accept if is_http
    tcp-request content accept if is_ssh
    tcp-request content accept if is_rdp
    tcp-request content accept


    use_backend bk_ssh if is_ssh
    use_backend bk_rdp if is_rdp
    use_backend bk_nginx if is_http
    default_backend bk_nginx

backend bk_ssh
    mode tcp
    server backend_server localhost:22

backend bk_rdp
    mode tcp
    server backend_server localhost:3389

backend bk_nginx
    mode http
    # 后端服务器配置
    server backend_server 127.0.0.1:8083


listen stats    #定义监控页面
    bind *:1080                   #绑定端口1080
    stats refresh 30s             #每30秒更新监控数据
    stats uri /stats              #访问监控页面的uri
    stats realm HAProxy\ Stats    #监控页面的认证提示
    stats auth admin:admin        #监控页面的用户名和密码
```

### 开启

```sh
sudo systemctl restart haproxy
sudo systemctl enable haproxy
sudo systemctl status haproxy
```

### 验证

```sh
ssh -p 3322 <用户名>@127.0.0.1
```

## 安装wireguard

通过[wireguard-install@angristan](https://github.com/angristan/wireguard-install)的自动化脚本安装

### 1. 下载并运行脚本

```bash
curl -O https://raw.githubusercontent.com/angristan/wireguard-install/master/wireguard-install.sh
chmod +x wireguard-install.sh
```

linuxmint或者其他魔改系统可能会遇到下面的问题：
```sh
❯ sudo ./wireguard-install.sh -h
Looks like you aren't running this installer on a Debian, Ubuntu, Fedora, CentOS, AlmaLinux, Oracle or Arch Linux system
```

打开脚本添加修改里面的`checkOS()`函数，手动指定OS和VERSION_ID即可

### 2. 交互式配置（关键步骤）
脚本运行后会问你几个问题，请按以下说明填写：

1.  **Public IPv4 or IPv6 address**:
    *   脚本通常能自动识别你的公网 IP。如果识别正确直接回车；如果是内网 IP，请手动填入你的**公网 IP**（或者动态域名 DDNS 域名）。
2.  **Public interface**:
    *   直接回车（默认检测到的网卡）。
3.  **WireGuard interface name**:
    *   直接回车（默认 `wg0`）。
4.  **Server's WireGuard IPv4**:
    *   直接回车（默认 `10.66.66.1`，这是 VPN 内部局域网 IP）。
5.  **Server's WireGuard IPv6**:
    *   直接回车。
6.  **Server's WireGuard port** (**最重要的一步**):
    *   默认通常是 51820，**这里请手动输入 `3322`**，然后回车。
7.  **First DNS resolver**:
    *   选择一个 DNS，比如 Google (1) 或 Cloudflare (3)。
8.  **Allowed IPs list for generated clients**:
9.  * 客户端走wireguard的流量，一般填虚拟局域网网段和内网网段即可

之后脚本会自动安装软件、生成密钥并启动服务。脚本的输出如下：

```
You can keep the default options and just press enter if you are ok with them.

IPv4 or IPv6 public address: <公网IP>(default: /etc/wireguard/wg0.conf)
Public interface: <网卡>
WireGuard interface name: <接口>
Server WireGuard IPv4: 10.66.66.1
Server WireGuard IPv6: fd42:42:42::1
Server WireGuard port [1-65535]: <wireguard端口>
First DNS resolver to use for the clients: 223.5.5.5
Second DNS resolver to use for the clients (optional): 1.1.1.1

WireGuard uses a parameter called AllowedIPs to determine what is routed over the VPN.
Allowed IPs list for generated clients (leave default to route everything): 0.0.0.0/0,::/0

Okay, that was all I needed. We are ready to setup your WireGuard server now.
You will be able to generate a client at the end of the installation.
Press any key to continue...
...
```

### 3. 创建客户端配置文件
安装完成后，脚本会提示你创建一个客户端（Client）：

1.  **Client name**: 输入设备名（例如 `myphone`）。
2.  **Client's WireGuard IPv4**: 直接回车。

脚本运行结束后，会在当前目录下生成一个 `.conf` 文件（例如 `myphone.conf`）或者是显示一个二维码（如果你安装了 `qrencode`）。

```
Client configuration

The client name must consist of alphanumeric character(s). It may also include underscores or dashes and can't exceed 15 chars.
Client name: mypc
Client WireGuard IPv4: 10.66.66.2
Client WireGuard IPv6: fd42:42:42::2

Here is your client config file as a QR Code:


█████████████████████████████████████████████████████████████████████████████████████████
█████████████████████████████████████████████████████████████████████████████████████████
████ ▄▄▄▄▄ █ ▄▄ ██ ██ ▀ ▄█▄▄██ ▀█ ▄▀▀▄▀██ █▀ ▄▄ ███ ▄ ▄█▄▀▄▄▄  ▀▀ ▄ ▄▀▄ ▀▄▀▀▀█ ▄▄▄▄▄ ████
████ █   █ █   ▄   █▀  ▄▄█▀ █ █ ▄▀ ▄█▀▀▄▄▄  ██▄▄██▄▄▀█ ▄▄ ▄▄▄▀▄▀███▄  ▀ ▄▄ █ █ █   █ ████
████ █▄▄▄█ █▀██▀▄ ▀     ▀ ▄█ ▄▄▄ ██▀ ▄▀▀█▀▀▄ ▄▀▀ █ ▄ ▄▄▄ ██ ▀  ▄▀▄▄▀▄█ █▀▄█▀██ █▄▄▄█ ████
████▄▄▄▄▄▄▄█▄█▄▀ ▀▄▀ █ █▄▀▄▀ █▄█ █ █▄█▄▀▄█▄▀▄█▄█ ▀▄█ █▄█ ▀▄█▄█ █ █ █ █▄█▄█ █▄█▄▄▄▄▄▄▄████

 ...

█████▄▄▄██▄▄ ▀▄▄ ▀█ ▄▄▄   ▄  ▄▄▄ ▄ ▀ ██  ▀ ▀██▀  ██▀ ▄▄▄ ▄  ▀▄ ██ █  ██ ▀▀ █ ▄▄▄ ████████
████ ▄▄▄▄▄ █▀▀ ▄█▄▄▄▀▀▄█▄▀ ▄ █▄█ ▄ ▄█▄▄ ███ █▄ ▄▄▄ ▄ █▄█ ▀▀▀▀█ ▀▀██ ▄▀ ▄ █ ▄ █▄█ ▄▀██████
████ █   █ █▄▄ ▀▀▀ ▄ █ ▄▀  ▄▄▄▄▄  ▄▀█▄▄██▀ █▄██▀██ █ ▄  ▄█▀▄▄█ ▄█  ▄▀▄▀█ ▀▄█  ▄▄ █▄▀ ████
████ █▄▄▄█ █▀▄▀▀ ▄▀█▀██ ▄█▄▄▄▄█▀▄▄▄▄▄▄▀█▄ █▀█▄▀▄▄▄ ██ ▄█ ▄█ ██  ▀▀ █▄▄▄▀█▄ ▀██▀▀ ▄▀██████
████▄▄▄▄▄▄▄█▄███████▄▄█▄▄▄█▄█▄▄▄▄▄▄▄▄▄▄▄▄███▄█▄▄▄█▄▄▄██▄█▄█▄█▄▄█▄█▄██▄██▄▄▄▄█▄▄▄█▄██▄████
█████████████████████████████████████████████████████████████████████████████████████████
█████████████████████████████████████████████████████████████████████████████████████████

```

### 4. 配置防火墙（UFW）

你需要显式放行 UDP 的wireguard服务求端口：

```bash
sudo ufw allow 3322/udp
sudo ufw reload
```
