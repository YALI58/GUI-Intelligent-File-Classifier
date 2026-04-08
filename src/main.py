#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文件分类器 - 重构版主程序
Intelligent File Classifier - Refactored Main Program
"""

import sys
import tkinter as tk
from src.ui.main_window import FileClassifierApp


def main():
    """主函数"""
    root = tk.Tk()
    app = FileClassifierApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
