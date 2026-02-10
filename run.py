#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文件分类器启动脚本
检查依赖并启动应用程序
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """检查Python版本"""
    if sys.version_info < (3, 7):
        print("错误: 需要Python 3.7或更高版本")
        print(f"当前版本: {sys.version}")
        return False
    return True

def check_dependencies():
    """检查依赖包"""
    required_packages = {
        'watchdog': 'watchdog>=3.0.0',
        'PIL': 'pillow>=9.0.0',
        'send2trash': 'send2trash>=1.8.0'
    }
    
    missing_packages = []
    
    for package, pip_name in required_packages.items():
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(pip_name)
    
    return missing_packages

def install_dependencies(packages):
    """安装缺失的依赖包"""
    print("正在安装缺失的依赖包...")
    for package in packages:
        print(f"安装 {package}...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        except subprocess.CalledProcessError as e:
            print(f"安装 {package} 失败: {e}")
            return False
    return True

def main():
    """主函数"""
    print("智能文件分类器 v1.0")
    print("=" * 40)
    
    # 检查Python版本
    if not check_python_version():
        input("按回车键退出...")
        return
    
    # 检查依赖
    missing = check_dependencies()
    if missing:
        print("缺少以下依赖包:")
        for pkg in missing:
            print(f"  - {pkg}")
        
        response = input("是否自动安装缺失的依赖包? (y/n): ")
        if response.lower() in ['y', 'yes', '是']:
            if not install_dependencies(missing):
                print("依赖安装失败!")
                input("按回车键退出...")
                return
        else:
            print("请手动安装依赖包:")
            print("pip install -r requirements.txt")
            input("按回车键退出...")
            return
    
    # 启动应用程序
    try:
        print("启动文件分类器...")
        from main import main as app_main
        app_main()
    except Exception as e:
        print(f"启动失败: {e}")
        input("按回车键退出...")

if __name__ == "__main__":
    main() 