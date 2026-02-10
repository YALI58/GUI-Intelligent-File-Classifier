#!/bin/bash
echo "正在构建智能文件分类器可执行文件..."
python3 build_executable.py
if [ $? -eq 0 ]; then
    echo "构建成功！可执行文件位于 release/ 目录中"
else
    echo "构建失败！"
    exit 1
fi
echo "构建完成！可执行文件位于release目录。" 