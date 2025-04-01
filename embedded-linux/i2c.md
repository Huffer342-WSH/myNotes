---
layout: post
title: Linux I2C 总线框架
date: 2025-04-01 16:57:18
categories: [Linux]
excerpt: 
hide: index
---
 

## I2C总线框架

I2C总线框架分三部分：**总线驱动-核心层-设备驱动**

1. **核心层（i2c-core）**：
    I2C 核心提供了 I2C 总线驱动（适配器）和设备驱动的注册、注销方法，I2C
通信方法与具体硬件无关的代码以及探测设备地址的上层代码等
2. **总线驱动层（Adapter驱动）**
    负责具体SoC的I2C控制器硬件操作
3. **设备驱动层（Client驱动）**
    实现特定外设（如EEPROM、传感器）的功能逻辑 



## I2C总线驱动

I2C总线驱动（I2C适配器驱动）的向核心层提供操控I2C总线驱动的功能。因为和芯片的I2C外设相关，一般由芯片厂提供代码。

I2C总线驱动层注册一个`i2c_adapter`结构体变量，其中包含`i2c_algorithm`结构体，`i2c_algorithm`中又包含了`master_xfer`等函数，负责具体的数据传输操作，将核心层的消息落实到接口。

`master_xfer`函数和其参数`struct i2c_msg`的定义如下：
```c
// i2c_adapter->i2c_algorithm->master_xfer

int (*master_xfer)(struct i2c_adapter *adap, struct i2c_msg *msgs, int num);

struct i2c_msg {
	__u16 addr;	/* slave address			*/
	__u16 flags;
#define I2C_M_RD		0x0001	/* read data, from slave to master */
					/* I2C_M_RD is guaranteed to be 0x0001! */
#define I2C_M_TEN		0x0010	/* this is a ten bit chip address */
#define I2C_M_DMA_SAFE		0x0200	/* the buffer of this message is DMA safe */
					/* makes only sense in kernelspace */
					/* userspace buffers are copied anyway */
#define I2C_M_RECV_LEN		0x0400	/* length will be first received byte */
#define I2C_M_NO_RD_ACK		0x0800	/* if I2C_FUNC_PROTOCOL_MANGLING */
#define I2C_M_IGNORE_NAK	0x1000	/* if I2C_FUNC_PROTOCOL_MANGLING */
#define I2C_M_REV_DIR_ADDR	0x2000	/* if I2C_FUNC_PROTOCOL_MANGLING */
#define I2C_M_NOSTART		0x4000	/* if I2C_FUNC_NOSTART */
#define I2C_M_STOP		0x8000	/* if I2C_FUNC_PROTOCOL_MANGLING */
	__u16 len;		/* msg length				*/
	__u8 *buf;		/* pointer to msg data			*/
};

int (*master_xfer)(struct i2c_adapter *adap, struct i2c_msg *msgs, int num);
```

`master_xfer`函数接收`num`个`struct i2c_msg *msgs`消息并处理，标志位`flags`可选项如下：

| 宏定义               | 作用                               |
| -------------------- | ---------------------------------- |
| `I2C_M_RD`           | 读取操作（从设备 -> 主机）         |
| `I2C_M_TEN`          | 使用 10 位地址模式                 |
| `I2C_M_DMA_SAFE`     | 缓冲区可安全用于 DMA 传输          |
| `I2C_M_RECV_LEN`     | 读取数据时，第一个字节表示数据长度 |
| `I2C_M_NO_RD_ACK`    | 读取时不发送 ACK                   |
| `I2C_M_IGNORE_NAK`   | 忽略从设备的 NACK                  |
| `I2C_M_REV_DIR_ADDR` | 反向地址传输顺序                   |
| `I2C_M_NOSTART`      | 不发送 START 信号                  |
| `I2C_M_STOP`         | 发送 STOP 信号                     |

具体见[《struct i2c_msg 解析》](i2c_msg.md)

## I2C核心层


- 面向适配器，提供`int i2c_add_adapter(struct i2c_adapter *adapter)`和`int i2c_add_numbered_adapter(struct i2c_adapter *adap)`以及对应的卸载函数，提供I2C适配器的注册/注销

- 面向设备驱动层，提供`int i2c_transfer(struct i2c_adapter *adap, struct i2c_msg *msgs, int num)`函数
  
其他参考[《i2c_core》](i2c_core.md)

## I2C设备驱动

platform框架下，我们会编写并注册一个`platform_device`和`platform_driver`结构体来描述设备和驱动，或者使用设备树描述设备，当内核在解析设备树的时候会自动帮我们创建一个 `platform_device对象`。
```c
struct platform_driver {
	int (*probe)(struct platform_device *);
	int (*remove)(struct platform_device *);
	void (*shutdown)(struct platform_device *);
	int (*suspend)(struct platform_device *, pm_message_t state);
	int (*resume)(struct platform_device *);
	struct device_driver driver;
	const struct platform_device_id *id_table;
	bool prevent_deferred_probe;
};
```
 
I2C设备驱动的开发和platform框架类似，需要注册一个`struct i2c_driver`结构体，并使用设备树描述设备，内核会创建一个`i2c_client`对象。`struct i2c_driver`结构体定义如下：

```c
struct i2c_driver {
	unsigned int class;
	int (*probe)(struct i2c_client *client, const struct i2c_device_id *id);
	int (*remove)(struct i2c_client *client);
	int (*probe_new)(struct i2c_client *client);
	void (*shutdown)(struct i2c_client *client);
	void (*alert)(struct i2c_client *client, enum i2c_alert_protocol protocol,
		      unsigned int data);
	int (*command)(struct i2c_client *client, unsigned int cmd, void *arg);
	struct device_driver driver;
	const struct i2c_device_id *id_table;
	int (*detect)(struct i2c_client *client, struct i2c_board_info *info);
	const unsigned short *address_list;
	struct list_head clients;
	bool disable_i2c_core_irq_mapping;
};
```


比如现在有一个ft5x06触摸屏挂在i2c1接口下面，设备树描述如下：

```
/ {
	amba: amba {
		u-boot,dm-pre-reloc;
		compatible = "simple-bus";
		#address-cells = <1>;
		#size-cells = <1>;
		interrupt-parent = <&intc>;
		ranges;

		i2c1: i2c@e0005000 {
			compatible = "cdns,i2c-r1p10";
			status = "disabled";
			clocks = <&clkc 39>;
			interrupt-parent = <&intc>;
			interrupts = <0 48 4>;
			reg = <0xe0005000 0x1000>;
			#address-cells = <1>;
			#size-cells = <0>;
		};
    }；
};

&i2c1 {
	clock-frequency = <100000>;

	edt-ft5x06@38 {
		compatible = "edt,edt-ft5426";
		reg = <0x38>;

		interrupt-parent = <&gpio0>;
		interrupts = <60 0x2>;

		reset-gpio = <&gpio0 59 GPIO_ACTIVE_LOW>;
		interrupt-gpio = <&gpio0 60 GPIO_ACTIVE_LOW>;
	};
};
```

- `i2c1`的属性`compatible = "cdns,i2c-r1p10";`会匹配到`i2c-cadence.c`，注册一个适配器驱动。
- 内核解析设备树会为`edt-ft5x06`生成一个`i2c_client`对象，因为`edt-ft5x06`节点在`i2c1`下面，内部包含匹配到的适配器`struct i2c_adapter *adapter`会指向`i2c1`生成的`i2c_adapter`
- 当驱动层注册的驱动和`edt-ft5x06`的属性`compatible = "edt,edt-ft5426"`匹配后，就会自动调用`.probe`函数，传入对应的`i2c_client`。


对于设备驱动开发者来说，I2C子框架提供了自动匹配和`i2c_transfer()`函数。和开发platform驱动一样，开发者只需要在`.probe`函数中
