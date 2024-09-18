---
layout: post
title: python脚本批量修改文本文件的编码格式
date: 2024-09-18 15:16:00
categories: [工具]
excerpt: 写了一个python脚本用批量转化文本文件的编码格式
---

狗屎vivado自带的文本编辑器不能改编码格式，而且linux里是utf-8，在中文的windows下面是gbk。

脚本内容如下：
[change_encoding.py](https://raw.githubusercontent.com/Huffer342-WSH/myScripts/main/change_encoding.py)

```python
import os
import sys
import chardet
import argparse

def convert_to_encoding(file_paths, target_encoding):
    """
    将给定的多个文本文件编码转换为目标编码（UTF-8 或 GB18030）。
    
    参数:
    - file_paths: 一个包含文件路径的列表。
    - target_encoding: 目标编码，如 'utf-8' 或 'gb18030'。
    """
    for file_path in file_paths:
        if not os.path.isfile(file_path):
            print(f"文件 {file_path} 不存在.")
            continue

        # 检测文件的编码格式
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            source_encoding = detected['encoding']
        
        print(f"文件 {file_path} 的原始编码为 {source_encoding}")

        # 如果文件已经是目标编码，跳过转换
        if source_encoding and source_encoding.lower() == target_encoding.lower():
            print(f"文件 {file_path} 已经是 {target_encoding.upper()} 编码，跳过转换.")
            continue
        
        # 读取文件内容并转换为目标编码
        try:
            with open(file_path, 'r', encoding=source_encoding) as f:
                file_content = f.read()
            # 将内容写回文件，使用目标编码
            with open(file_path, 'w', encoding=target_encoding) as f:
                f.write(file_content)
            print(f"文件 {file_path} 已成功转换为 {target_encoding.upper()} 编码.")
        except Exception as e:
            print(f"转换文件 {file_path} 过程中出错: {e}")

def get_all_files_in_folder(folder_path, recursive=False):
    """
    获取文件夹下的所有文件，如果 recursive 为 True，则递归获取子文件夹中的文件。
    
    参数:
    - folder_path: 文件夹路径。
    - recursive: 是否递归获取子文件夹中的文件。
    
    返回:
    - 文件路径列表。
    """
    all_files = []
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            all_files.append(os.path.join(root, file))
        if not recursive:
            break  # 如果不递归，处理完顶层文件后直接退出
    return all_files

def main():
    parser = argparse.ArgumentParser(description="批量转换文件编码格式")
    parser.add_argument('-R', '--recursive', action='store_true', help="递归处理文件夹中的文件")
    parser.add_argument('-e', '--encoding', choices=['utf-8', 'gb18030'], default='utf-8', help="目标编码格式，默认为 UTF-8")
    parser.add_argument('paths', nargs='+', help="文件或文件夹路径，可以指定多个")

    args = parser.parse_args()

    file_paths = []
    for path in args.paths:
        if os.path.isfile(path):
            file_paths.append(path)
        elif os.path.isdir(path):
            # 获取该文件夹下的所有文件
            files_in_folder = get_all_files_in_folder(path, recursive=args.recursive)
            file_paths.extend(files_in_folder)
        else:
            print(f"路径 {path} 无效，跳过处理.")

    if file_paths:
        convert_to_encoding(file_paths, args.encoding)
    else:
        print("未找到任何可处理的文件。")

if __name__ == "__main__":
    main()
```
