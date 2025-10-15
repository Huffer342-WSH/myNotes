---
layout: post
title: 安装ZSH
date: 2025-08-05 15:19:56
categories: [教程]
excerpt:
hide: false
---

## 一键[安装脚本](https://gist.githubusercontent.com/Huffer342-WSH/3d42fcb5ebbedcf2d47fe3dfea033739/raw/f013ccf4048e1c65e5d93cb2b353b9196444dbd8/install-zsh.sh)
```sh
sh -c "$(wget -qO- https://gist.githubusercontent.com/Huffer342-WSH/3d42fcb5ebbedcf2d47fe3dfea033739/raw/f013ccf4048e1c65e5d93cb2b353b9196444dbd8/install-zsh.sh)"
```


## 安装

安装zsh、on-my-zsh和插件

```sh
# 安装zsh
sudo apt install zsh

# 安装oh-my-zsh
sh -c "$(wget https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh -O -)"

# 切换zsh
chsh -s $(which zsh)
```

修改默认shell后需要注销重新登陆才能生效

## 主题

在 `{ZSH_CUSTOM:-~/.oh-my-zsh/custom}/themes/`下添加自己的主题`my.zsh-theme`:
```sh
ZSH_THEME_GIT_PROMPT_PREFIX=" on %{$fg[magenta]%}"
ZSH_THEME_GIT_PROMPT_SUFFIX="%{$reset_color%}"
ZSH_THEME_GIT_PROMPT_DIRTY="%{$fg[red]%}!"
ZSH_THEME_GIT_PROMPT_UNTRACKED="%{$fg[green]%}?"
ZSH_THEME_GIT_PROMPT_CLEAN=""

VIRTUAL_ENV_DISABLE_PROMPT=1
ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX=" %{$fg[green]%}🐍 "
ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX="%{$reset_color%}"
ZSH_THEME_VIRTUALENV_PREFIX=$ZSH_THEME_VIRTUAL_ENV_PROMPT_PREFIX
ZSH_THEME_VIRTUALENV_SUFFIX=$ZSH_THEME_VIRTUAL_ENV_PROMPT_SUFFIX

PROMPT='%{$fg_bold[green]%} %~%{$reset_color%}$(git_prompt_info)$(virtualenv_prompt_info)
❯ '
```

[下载地址](https://gist.githubusercontent.com/Huffer342-WSH/452c50b3172bf5857927e76626b5af06/raw/23449072063f6f6a72644c13e7267e6665f75ea1/my.zsh-theme)

## 插件

安装zsh-autosuggestions和zsh-syntax-highlighting

```sh
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```

在~/.zshrc中修改：

```sh
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
```
