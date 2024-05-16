#!/bin/bash

# 获取脚本所在的目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# 将该目录添加到 PATH
export PATH="$SCRIPT_DIR:$PATH"

# 提示用户已将目录添加到 PATH
echo "Directory $SCRIPT_DIR added to PATH"
