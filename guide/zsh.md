---
layout: post
title: 使用ZSH
date: 2025-08-05 15:19:56
categories: [教程]
excerpt:
hide: true
---

## 安装

安装zsh、on-my-zsh和插件

```sh

```


## 主题

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
