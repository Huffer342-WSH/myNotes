---
layout: post
title: 在VSCode中使用Git管理项目
date: 2024-06-29 18:10:00
excerpt_type: html
categories: [编程工具]
---

最近大量的代码都是用vscode写的，不管是单片机还是FPGA或者是matlab，虽然各自有各自的IDE，但是写代码还是VSCode好用。
vscode中的GitLens拓展给VSCode增加了很多Git操作，该文主要记录一些VSCode中常用的Git指令

<!-- more -->
## 0 概述

1. 使用.gitignore文件忽略不需要存入仓库的文件
2. 提交时使用统一的规范
3. 项目包含产品分支main、开发分支develop、发布分支release(可选)以及功能分支FeatureA、FeatureB...和热修复分支HotfixA、HotfixB...
   1. main分支是产品分支，里面只存稳定版
   2. develop分支是开发分支，所有人开发人员的代码都先合并到这个分支
   3. FeatureA、FeatureB...分支是功能分支，开发一个新功能时从develop分支签出，开发完成后合并到develop分支
4. 在私人分支开发代码时，使用rebase来合并代码，保证历史记录清晰
5. 将私人分支合并到公共分支时使用`merge`，避免已有的提交哈希值发生变化

## 1 .gitignore文件

`.gitignore` 文件在 Git 项目中用于指定哪些文件和目录应该被 Git 忽略，不纳入版本控制。比如忽略编译的时候产生的 `build` 文件夹或者是一些日志。

[https://git-scm.com/docs/gitignore/zh_HANS-CN](https://git-scm.com/docs/gitignore/zh_HANS-CN)，这是官网的文档。

在 [gitignore@github](https://github.com/github/gitignore) 这仓库里收集了很多gitignore模板，主要针对各种IDE。

## 2 日常开发常用的Git操作

### 2.1 设置网络代理

```shell
git config --global http.proxy http://username:password@proxy.server:port
git config --global https.proxy https://username:password@proxy.server:port
```

例如

```shell
git config --global http.proxy http://127.0.0.1:7890
git config --global https.proxy https://127.0.0.1:7890
```

### 2.2 设置用户名和密码

Git 需要用户名和邮箱来标识每个提交的作者信息。一般来说配置一个全局的用户名和邮箱就可以了。

**全局配置**
```shell
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

**获取全局配置**
``` shell
git config --global --get user.name
git config --global --get user.email
```

**单个仓库配置**
``` shell
git config user.name "Your Name"
git config user.email "your.email@example.com"
```

**获取单个仓库的配置**
``` shell
git config --get user.name
git config --get user.email
```

**设置VSCode中Git Commit记录中的头像**

VSCode是根据commit的邮箱，从[https://gravatar.com/](https://gravatar.com/)中找的头像。只需要用同一个邮箱在[gravatar](https://gravatar.com/)注册一个账号，提交头像就可以了
![alt text](./assets/Screenshot-of-git-commit-in-vscode.png)




### 2.3 初始化本地仓库

打开工程根目录，点击`Initialize Repository`初始化仓库
![VSCode仓库初始化](./assets/Initialize-Repository.png)

可以看到在git日志中使用了
``` shell
git init -b main
```
意思是初始化一个新的 Git 仓库，并将默认分支名称设置为 `main`。
![VSCode git 初始化日志](./assets/git-log-init.png)

初始化仓库工程根目录新增一个隐藏的`.git`文件夹。
![git文件夹](./assets/git-folder.png)

### 2.4 发布到github

VSCode中可以一键提交到Github，点底部状态栏的☁图标就行了。或者在命令面板搜索`publish to github`

![发布到github](./assets/git-publish.png)

发布的时候可以设置仓库的名字，默认时当前文件夹的名字，还可以选择私有还是公共。

![发布到Github时设置信息](./assets/git-publish-to-github-pannel.png)

### 2.5 暂存、提交文件

`git add` 命令用于将文件的更改添加到暂存区（staging area）; `git commit` 命令用于将暂存区的更改记录到本地仓库。

对应的指令如下：
```shell
git add <filename> #暂存一个文件
git add <directory> #暂存一个文件夹
git commit -m "Your commit message" #将暂存区中的文件提交，并带有提交信息
```

在VScode中的`'SOURCE CONTRIL' > 'Changes'`面板中可以暂存想要的文件或者文件夹，暂存后会显示在`'Staged Changes'`面板中。
![Git Stage in VSCode](./assets/git-stage.png)

![Git Staged in VSCode](./assets/git-unstage.png)

暂存后的文件就可以提交了。在点`Commit`按钮前输入Message了的话，点击时就直接提交了。假如Message是空白的，就会自动打开一个新的文件来输入Message。

![git commit message in VSCode](./assets/git-commit-message.png)

合作时提交信息要遵循一致的规范，参考[约定式提交 1.0.0](https://www.conventionalcommits.org/zh-hans/v1.0.0/)。

我实验室项目之前的代码的提交属于是有一点点规范。之后多人合作时得统一规范了。

### 2.6 新建分支（派生分支）

分支功能方便多个人共同开发，每个人再自己的分支中独立开发，然后合并到公共分支（最好不要一起改一个文件，要不然要解决冲突）。

单人开发的时候其实一两个分支就够用了，我以前都只用 `main` 分支和一个`develop`分支，平常再`develop`分支里写代码，有稳定版本了就`git merge --squash`到`main`分支。不过多人合作的时候就该每个人都现在自己的分支上写代码，然后`merge`到公共分支了。
>有一说一，实验室也不会有多少个人参加到同一个项目里，写代码的人更是少。而且写代码也会分开写，有人写matlab，有人写C语言。可能直接发文件合并代码比用git效率更高。不过练练git也没有坏处，再说项目进度慢一点急的也不是我。

Git新建分支可以从一个已有的分支为基点分叉出一个新的分支（一般都是从已有分支的最新提交作为基点）。
装了GitLens拓展后VSCode里有好几个地方都能找到新建分支按钮，这里贴个VSCode默认就有的：

![git create branch](./assets/git-create-branch.png)

VSCode命令栏里也能找到（Ctrl+Shift+P 打开命令栏）

![VSCode命令栏中的git create branch](./assets/git-create-branch-vscode-cmd.png)

点击按钮或者选择指令后，先选择一个已有的分支作为基础。

![选择已有分支](./assets/git-chose-ref-branch.png)

然后需要输入新分支的名字，这里先新建一个`develop`分支
![设置新分支的名字](./assets/git-provide-new-name-for-branch.png)

新建后就可以在底部状态栏和左侧栏中看到新建的分支了。
![vscode中查看分支](./assets/git-create-branch-result.png)

### 2.7 切换分支

`git checkout`指令用于切换到一个已有的分支。

```shell
git checkout <branch-name>
```

在VSCode中，底部状态栏中显示当前分支的名字，点击就可以切换分支或者新建分支。

![VSCode git切换分支](./assets/git-check-out-branch.png)


### 2.8 在新分支开发并合并分支



#### 2.8.1 用户A开发功能

首先用户A新建并切换到新的分支'feature/A'，写两个函数`sum()`和`sub()`并提交。

![在新分支中写函数](./assets/git-featA-new-func.png)

提交完之后用户A自己合并分支。合并分支有两中方式：`git merge`和`git rebase`。这里先演示`merge`。

>毕竟merge的中文就是'v.结合'，设计出来就是合并用的。
>而rebase的中文是'变基'，相当于把新分支上新的提交挪到了老分支上。

1. 首先切换到合并到的分支，比如想要将`feature/A`合并到`develop`分支，就切换到`develop`分支。

2. 从`'SOURCE CONTROL'`面板的菜单中找到。或者在命令面板中搜索`merge`，可以搜到GitLens和Git提供的`merge`指令，两个大差不差。

![VSCode merge按钮](./assets/git-merge-1.png)

3. 选择要合并的分支，这里选择`feature/A`。

![VSCode merge 选择分支](./assets/git-merge_2.png)

然后就会看到当前分支里多了`feature/A`分支的提交。

![git merge 结果](./assets/git-merge-3.png)


#### 2.8.2 用户B拉取develop分支并解决冲突

用户A把刚才的改动分支推到Github后，用户B打开VSCode的时候就会看到`develop`红了。可以选择fetch或者pull下载改动。
![用户B VSCode界面看到分支变化](./assets/git-UserB-fetch.png)

这边用户B先在develop分支提交两个commit`sum()`和`multiply()`，制造冲突。此时远程分支和本地分支存在冲突。在VSCode中点击`Pull`后会提示存在冲突。

![VSCode 拉去冲突](./assets/git-pull-conflicts.png)

Pull后可以看到sum.py和sub.py都已经拉取下来了。观察左侧边栏可以看到存在冲突的sum.py在`Merge Changes`面板中，没有冲突的sub.py则已经在暂存区了。

VScode会打开一个合并管理器，两个分支里二选一解决冲突，当然也可以再添加一些改动。修改完成后点击`Complete Merge`按钮就可以了。


![VSCode拉取冲突 缓存区](./assets/git-pull-merge-1.png)

![VSCode拉取冲突 解决冲突](./assets/git-pull-merge-2.png)

![VSCode git graph](./assets/git-graph-1.png)

#### 2.8.3 用户B再feature/B分支上开发，A更新了develop分支，用户B拉取develop分支并解决冲突

用户B新建了自己的`feature/B`分支，然后写了`main.py`文件,用来将两个列表中的数分别相加。

![main.py](./assets/main.py-1.png)

用户B刚准备把这个合并到develop分支时，发现用户A很体贴的给他准备了一个新的`sum()`函数,可以直接输入两个列表并求和。那么用户B该怎么才能用上最新的功能呢？
和之前合并分支一样有两种选择`merge`和`rebase`：
+ merge：用户B先更新develop分支，切换到feature/B分后`git merge develop`将develop的新提交合并到feature/B分支。
+ rebase：用户B先更新develop分支， 

##### merge
merge的过程和上文中的一样，下图是merge并提交了新的代码后的结果。


用户B再写main.py的过程中发现用户A还在sum()函数里留了个bug，用户A在用户B合并分支前又在develop分支提交了新的sub()函数，不过用户B暂时不需要这个函数，所以就没有再次把develop分支上的东西合并到子的`feature/B`分支上。可以看到使用merge合并分支的话，可以保留提交的顺序。不过在开发的过程中各个分支又相关功能的变动还是要尽量避免的。

![VSCode Merge结果](./assets/git-merge-4.png)


##### rebase
下面主要展示rebase。因为这里的需求是将公共分支的修改应用到用户B自己的分支上，使用rebase并不会影响其他人。使用rebase相当于改变了这个分支的起点，让`feature/B`变成从`develop`最新的提交上派生出来。

下文是rebase前的状态，用户B刚写完main.py， 用户A就在把新的sum()函数合并到develop分支上了。这个时候用户B就可以使用rebase让自己的分支变成从最新的develop分支派生出来。
![rebase前的状态](./assets/git-rebase-0.png)

![VSCode rebase](./assets/git-rebase-1.png)

![选择新基点](./assets/git-rebase-3.png)

下图是用户B rebase后，开发完新功能并`merge`到develop分支后的结果。对比上面使用`merge`获取公共分支更新的方式，rebase的流程图更加简洁，不会像蜘蛛网一样，所以在私人分支上更建议使用rebase，

![使用rebase获取新代码并merge后的结果](./assets/git-merge-5.png)

#### 2.8.4 在把功能分支合并到公共分支前使用rebase

先将私人分支`rebase`到最新的公共分支提交后面，然后再`merge`到公共分支，可以使得`merge`前各个分支上没有新的提交，使得各个分支的提交历史是串行的。

![再merge前rebase](./assets/git-rebase-brefore-merge.png)

>到此为止常用的git操作就讲完了，冲突和中途从公共分支合并代码还是比较烦人的，在分配任务的时候要尽量避免这种情况。在合并代码前一定要验证过，不要给别人挖坑。


### 2.9 为什么不建议使用rebase把私人分支的提交合并到公共分支上

具体的来说，是不要rebase公共分支中别人已经引用的提交。因为rebase其实是把已有的提交暂存，并在新的基点上重新提交，提交的哈希值会发生变化。一但把rebase过的公共分支发布，在别人的视角里就会出现一模一样的新提交。
