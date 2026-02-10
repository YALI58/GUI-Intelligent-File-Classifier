#!/bin/bash

echo "====================================="
echo "   智能文件分类器 - 安装脚本"
echo "====================================="
echo

echo "正在检查Python环境..."
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到Python3环境"
    echo "请先安装Python 3.7或更高版本"
    exit 1
fi

python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.7"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then 
    echo "Python环境检查通过 (版本: $python_version)"
else
    echo "错误: Python版本过低 (当前: $python_version, 需要: >= $required_version)"
    exit 1
fi

echo
echo "正在安装依赖包..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo
    echo "依赖包安装失败！"
    echo "请检查网络连接或手动安装"
    exit 1
fi

echo
echo "====================================="
echo "    安装完成！"
echo "====================================="
echo
echo "您可以通过以下方式启动应用："
echo "1. 运行: python3 run.py"
echo "2. 运行: python3 main.py"
echo "3. 运行: ./start.sh"
echo

# 给启动脚本添加执行权限
chmod +x start.sh 2>/dev/null

echo "安装脚本执行完成。" 