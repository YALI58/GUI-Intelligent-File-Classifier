#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import subprocess
import platform


def _data_sep() -> str:
    return ";" if platform.system().lower() == "windows" else ":"


def _add_data_arg(src: str, dst: str) -> str:
    sep = _data_sep()
    return f"--add-data={src}{sep}{dst}"

def build_executable():
    """构建可执行文件"""
    print("开始构建可执行文件...")
    
    # 确保PyInstaller已安装
    try:
        import PyInstaller
    except ImportError:
        print("正在安装PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 检查图标文件
    icon_path = os.path.join("resources", "icon.ico")
    if not os.path.exists(icon_path):
        print(f"警告：未找到图标文件 {icon_path}")
        icon_path = None
    else:
        print(f"使用自定义图标：{icon_path}")
    
    # 构建命令参数
    args = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=intelligent_file_classifier",
        "--onedir",
        "--windowed",
        "--clean",
        "main.py"
    ]

    # 资源与文档
    if os.path.exists("resources"):
        args.append(_add_data_arg("resources", "resources"))

    for doc in [
        "README.md",
        "README_EN.md",
        "LICENSE",
        "CHANGELOG.md",
        "hierarchical_classification_guide.md",
        "intelligent_recommendations_guide.md",
    ]:
        if os.path.exists(doc):
            args.append(_add_data_arg(doc, "."))

    # keyring 在不同平台会动态加载后端，PyInstaller 可能需要补齐
    args.extend([
        "--collect-all=keyring",
        "--hidden-import=keyring.backends",
        "--hidden-import=keyring.backends.Windows",
        "--hidden-import=keyring.backends.win32",
        "--hidden-import=keyring.backends.chainer",
    ])
    
    # 添加图标
    if icon_path:
        args.append(f"--icon={icon_path}")
    
    print(f"执行命令: {' '.join(args)}")
    subprocess.check_call(args)
    
    # 创建发布包
    release_dir = "release"
    if not os.path.exists(release_dir):
        os.makedirs(release_dir)

    # 复制整个 onedir 包到发布目录（确保 resources 等相对路径可用）
    bundle_dir = os.path.join("dist", "intelligent_file_classifier")
    if not os.path.exists(bundle_dir):
        print(f"错误：未找到构建目录 {bundle_dir}")
        return False

    release_bundle_dir = os.path.join(release_dir, "intelligent_file_classifier")
    if os.path.exists(release_bundle_dir):
        shutil.rmtree(release_bundle_dir, ignore_errors=True)
    shutil.copytree(bundle_dir, release_bundle_dir)

    exe_name = "intelligent_file_classifier.exe" if platform.system().lower() == "windows" else "intelligent_file_classifier"
    exe_path = os.path.join(release_bundle_dir, exe_name)
    if os.path.exists(exe_path):
        print(f"可执行文件已构建并复制到 {release_bundle_dir} 目录")
    else:
        print(f"警告：未在发布目录找到可执行文件 {exe_path}，请检查 PyInstaller 输出")

    return True

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)