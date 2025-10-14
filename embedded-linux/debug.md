---
layout: post
title: Linux内核调试
date: 2025-10-14 18:19:50
categories: [Linux]
excerpt:
hide: false
---


## printk()

### 工作原理

源文件`kernel/printk/printk.c`

printk()将消息写入环形缓冲区，然后读取消息输出到**控制台**。


在`printk.c`中包含一个存储**控制台**用的单向链表`struct console *console_drivers;`

结构体`struct console`部分内容如下：
```c
struct console {
	char	name[16];
	void	(*write)(struct console *, const char *, unsigned);
	int	(*read)(struct console *, char *, unsigned);
	struct tty_driver *(*device)(struct console *, int *);
	void	(*unblank)(void);
	int	(*setup)(struct console *, char *);
	int	(*match)(struct console *, char *name, int idx, char *options);
	short	flags;
	short	index;
	int	cflag;
	void	*data;
	struct	 console *next;
};
```


### 查看日志

1. 开机过程自动打印
2. 进入系统后使用`demesg`

### 调试等级设置


#### 修改/etc/sysctl.conf

在文件中添加
```
kernel.printk = 7 4 1 7
```
四个数字含义如下：

| 参数位置              | 含义                      |
| --------------------- | ------------------------- |
| 第1个（current）      | 当前控制台打印级别（0~7） |
| 第2个（default）      | 默认消息级别              |
| 第3个（minimum）      | 系统允许的最低级别        |
| 第4个（boot default） | 启动时的默认级别          |

#### bootloader设置`bootargs`

例如u-boot设置booratgs为：`console=ttyS0,115200 loglevel=7 root=/dev/mmcblk0p2 rw`


```
setenv bootargs console=ttyS0,115200 loglevel=7 root=/dev/mmcblk0p2 rw
saveenv
boot
```


## kgdb

[《Using kgdb, kdb and the kernel debugger internals》](https://docs.kernel.org/process/debugging/kgdb.html)

kgdb是内核代码的一部分，表面上看相当于在内核中启动了一个gdbserver。可以选择以下三种方法连接并调试：

- 串口+kdb
- 串口+gdb
- 以太网+gdb
