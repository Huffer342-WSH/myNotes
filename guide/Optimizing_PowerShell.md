---
layout: post
title: 优化PowerShell
date: 2024-10-03 19:55:00
categories: [教程]
excerpt: PowerShell按键优化+美化
---
PowerShell Prompt的美化方案可选[Oh-My-Posh](https://ohmyposh.dev/)和[Starship](https://Starship.rs/)， Starship速度比较快且功能够用了，所以下文一StarShip为例

## 0. 精简版

1. 安装 `PSReadLine`,`posh-git`,`Starship`

   ```PowerShell
   Install-Module PSReadLine -Force -SkipPublisherCheck
   Install-Module posh-git -Scope CurrentUser -Force
   winget install --id Starship.Starship
   ```
2. 打开PowerShell配置文件

   ```PowerShell
   # 打开配置文件
   notepad $PROFILE
   ```
3. 在配置文件中输入一下内容

   ```PowerShell
    [console]::OutputEncoding = [System.Text.Encoding]::UTF8

    # 单次加载conda
    function Invoke-CondaInit {
        if (-not $script:CondaAlreadyInitialized) {
            Write-Host "Initializing Conda..." -ForegroundColor Yellow
            If (Test-Path "E:\SDK\miniconda3\Scripts\conda.exe") {
                (& "E:\SDK\miniconda3\Scripts\conda.exe" "shell.powershell" "hook") | Out-String | ?{$_} | Invoke-Expression
            }
            $script:CondaAlreadyInitialized = $true
        }
    }

    # conda 指令替换
    Set-Alias -Name conda -Value conda-wrapper
    function conda-wrapper {
        Invoke-CondaInit
        conda @args
    }

    # posh-git
    Import-Module posh-git

    # PSReadLine
    Import-Module PSReadLine
    Set-PSReadLineOption -EditMode Emacs
    Set-PSReadLineKeyHandler -Chord Ctrl+v -Function Paste
    Set-PSReadLineOption -PredictionSource History
    Set-PSReadLineOption -Colors @{
        Command            = 'Cyan'
        Parameter          = 'Yellow'
        String             = 'Green'
        Operator           = 'White'
        Number             = 'Magenta'
        Comment            = 'DarkGreen'
        ContinuationPrompt = 'DarkGray'
    }

    # Starship - 美化Prompt
    Invoke-Expression (&starship init powershell)
   ```
4. 安装Nerd字体并修改终端的字体

   进这个网站下载一个Nerd字体并安装：[https://www.nerdfonts.com/](https://www.nerdfonts.com/)

   然后再使用的终端中修改字体，比如VSCode是在 `Settings`中的 `terminal.integrated.fontFamily`中修改

## 1. 修改PowerShell编码

中文的windows系统下的PowerShell默认编码是gbk，常常导致一些程序输出乱码(单片机用C语言是这样的)。windows里

下面的PowerShell指令检查当前的编码：

```PowerShell
[console]::OutputEncoding
```

如果不是 UTF-8，使用以下命令将输出编码设置为 UTF-8：

```PowerShell
[console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

为了确保每次启动 PowerShell 时都将输出编码设置为 UTF-8，可以将设置写入 PowerShell 的 `profile` 文件。

- `AllUsersAllHosts`：为所有用户和所有 PowerShell 会话加载（位于 PowerShell 安装目录下）。
- `AllUsersCurrentHost`：为所有用户但仅在当前 PowerShell 主机中加载。
- `CurrentUserAllHosts`：为当前用户但在所有 PowerShell 会话中加载。
- `CurrentUserCurrentHost`：为当前用户且仅在当前 PowerShell 主机中加载。通常是指 `$PROFILE`，位于用户主目录下。
- 可以通过以下命令查看它们的位置：

  ```PowerShell
  $PROFILE | Format-List * -Force
  ```

  输出类似下面这样

  ```PowerShell
  AllUsersAllHosts       : C:\Windows\System32\WindowsPowerShell\v1.0\profile.ps1
  AllUsersCurrentHost    : C:\Windows\System32\WindowsPowerShell\v1.0\Microsoft.  PowerShell_profile.ps1
  CurrentUserAllHosts    : E:\Users\Huffer\Documents\WindowsPowerShell\profile.ps1
  CurrentUserCurrentHost : E:\Users\Huffer\Documents\WindowsPowerShell\Microsoft. PowerShell_profile.ps1
  Length                 : 76
  ```

一般选 `CurrentUserCurrentHost`这一项的文件就行了，不过 `conda init`也会将指令添加到 `CurrentUserAllHosts`这个文件, 建议参考[4. conda延迟加载](#4-conda延迟加载)。

在文件中添加以下内容：

```PowerShell
[console]::OutputEncoding = [System.Text.Encoding]::UTF8
```

保存文件后，PowerShell 每次启动时都会自动应用这个设置。

## 2. 优化 PowerShell 补全

### 2.1 安装并加载 `PSReadLine` 模块

PowerShell的路径补全是一个一个轮流显示的，而不是bash那样根据上文补全的。`PSReadLine` 模块可以让 PowerShell 的体验更像 Linux 命令行一样。

PSReadLine的Github仓库链接： [https://github.com/PowerShell/PSReadLine](https://github.com/PowerShell/PSReadLine)

PowerShell的路径补全是一个一个轮流显示的，而不是bash那样根据上文补全的。`PSReadLine` 模块可以让 PowerShell 的体验更像 Linux 命令行一样。

PSReadLine的Github仓库链接： [https://github.com/PowerShell/PSReadLine](https://github.com/PowerShell/PSReadLine)

**安装**

```PowerShell
Install-Module PSReadLine -Force -SkipPublisherCheck
```

**配置**

和上面一样，打开 `$PROFILE` 配置文件,添加一下内容

```PowerShell
Import-Module PSReadLine
Set-PSReadLineOption -EditMode Emacs
```

### 2.2 安装 posh-git 提供Git指令支持

**安装**

```PowerShell
Install-Module posh-git -Scope CurrentUser -Force
```

**配置**

`$PROFILE`：

```PowerShell
Import-Module posh-git
```

## 3. 安装Starship美化PowerShell

**安装**

```
winget install --id Starship.Starship
```

**启用StarShip**
以下下内容添加到 `$PROFILE`

```
Invoke-Expression (&Starship init PowerShell)
```

**设置主题**
`~/.config/Starship.toml`

```toml
# 根据 schema 提供自动补全
"$schema" = 'https://Starship.rs/config-schema.json'

# 在提示符之间插入空行
add_newline = true

format = """
$directory\
$git_branch\
$git_status\
$python\
\n$character\
"""

[directory]
truncation_length = 8
truncate_to_repo = false
truncation_symbol = '…/'
use_os_path_sep = false

[python]
symbol = ' '
pyenv_version_name = false
```

### 3.2 安装 Nerd 字体

[官网教程: https://ohmyposh.dev/docs/installation/fonts](https://ohmyposh.dev/docs/installation/fonts)

安装显示图标需要的[Nerd](https://www.nerdfonts.com/)字体,否则就会像下图这样，不能正常显示。我使用的是[CaskaydiaMonoNerdFontMono-Regular.ttf](https://github.com/ryanoasis/nerd-fonts/releases/download/v3.2.1/CascadiaMono.zip)

![字体乱码](../assets/Optimizing_PowerShell/pwsh-error-display.png)

安装完成过后需要设置终端使用的字体，Windows Terminal的修改方式如下

![打开外观设置](../assets/Optimizing_PowerShell/wt0.png)

![选择字体](../assets/Optimizing_PowerShell/wt1.png)

VSCode的话再设置里搜索terminal.integrated.fontFamily

填上安装的字体就可以

`<a id="conda"></a>`

## 4. conda延迟加载

`conda init`会添加初始化指令到 `~\Documents\PowerShell\profile.ps1`，封装里面的初始化指令

```PowerShell
# 单次加载conda
function Invoke-CondaInit {
    if (-not $script:CondaAlreadyInitialized) {
        Write-Host "Initializing Conda..." -ForegroundColor Yellow
        If (Test-Path "C:\SDK\Miniconda3\Scripts\conda.exe") {
            (& "C:\SDK\Miniconda3\Scripts\conda.exe" "shell.PowerShell" "hook") | Out-String | ?{$_} | Invoke-Expression
        }
        $script:CondaAlreadyInitialized = $true
    }
}

# conda 指令替换
Set-Alias -Name conda -Value conda-wrapper
function conda-wrapper {
    Invoke-CondaInit
    conda @args
}
```
