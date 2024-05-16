#!/bin/bash

# 检查是否提供了输入文件
if [ -z "$1" ]; then
    echo "Usage: $0 <input_file>"
    exit 1
fi

INPUT_FILE="$1"

# 检查输入文件是否存在
if [ ! -f "$INPUT_FILE" ]; then
    echo "Error: File '$INPUT_FILE' not found!"
    exit 1
fi

# 获取文件路径、文件名和扩展名
DIRNAME=$(dirname "$INPUT_FILE")
BASENAME=$(basename "$INPUT_FILE")
EXTENSION="${BASENAME##*.}"
BASENAME="${BASENAME%.*}"
OUTPUT_FILE="${DIRNAME}/${BASENAME}.webp"

# 根据文件扩展名选择转换工具
if [ "$EXTENSION" = "gif" ]; then
    gif2webp -q 80 "$INPUT_FILE" -o "$OUTPUT_FILE"
elif [ "$EXTENSION" = "png" ] || [ "$EXTENSION" = "jpg" ] || [ "$EXTENSION" = "jpeg" ]; then
    cwebp -q 80 "$INPUT_FILE" -o "$OUTPUT_FILE"
else
    echo "Unsupported file format: '$EXTENSION'"
    exit 1
fi

# 提示用户转换完成
if [ $? -eq 0 ]; then
    echo "Conversion successful: '$OUTPUT_FILE'"
else
    echo "Error during conversion."
    exit 1
fi
