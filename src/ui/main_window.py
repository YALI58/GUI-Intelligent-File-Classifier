#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
主窗口模块 - Main Window Module
智能文件分类器图形用户界面
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

from ..core import FileClassifier, EnhancedFileClassifier
from ..services import ConfigManager
from ..ui.theme import apply_wabi_sabi_theme, create_scrollable_container


class FileClassifierApp:
    """文件分类器主应用程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("智能文件分类器 v2.0 (重构版)")
        self.root.geometry("1000x750")
        self.root.minsize(900, 650)
        
        self.config_manager = ConfigManager()
        
        try:
            self.classifier = EnhancedFileClassifier()
        except ImportError:
            self.classifier = FileClassifier()
        
        self.file_monitor = None
        self.monitoring = False
        self.processing = False
        self.message_queue = queue.Queue()
        
        self._setup_ui()
        self._load_config()
        self._process_messages()
    
    def _setup_ui(self):
        """设置用户界面"""
        container = ttk.Frame(self.root)
        container.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(0, weight=1)
        
        canvas = tk.Canvas(container, highlightthickness=0)
        v_scroll = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=v_scroll.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        v_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        content = ttk.Frame(canvas, padding="10")
        content.columnconfigure(1, weight=1)
        window_id = canvas.create_window((0, 0), window=content, anchor="nw")
        
        def _on_content_configure(_event=None):
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
            except Exception:
                pass
        
        def _on_canvas_configure(event=None):
            try:
                if event is not None:
                    canvas.itemconfigure(window_id, width=event.width)
            except Exception:
                pass
        
        content.bind("<Configure>", _on_content_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        
        try:
            apply_wabi_sabi_theme(self.root)
        except Exception:
            pass
        
        self._create_widgets(content)
    
    def _create_widgets(self, parent):
        """创建界面组件"""
        title_label = ttk.Label(
            parent, 
            text="📁 智能文件分类器", 
            style="Title.TLabel"
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20), sticky=tk.W)
        
        dir_frame = ttk.LabelFrame(parent, text="目录选择", padding="10")
        dir_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        dir_frame.columnconfigure(1, weight=1)
        
        ttk.Label(dir_frame, text="源目录:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.source_path_var = tk.StringVar()
        self.source_entry = ttk.Entry(dir_frame, textvariable=self.source_path_var)
        self.source_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(dir_frame, text="浏览", command=self._browse_source).grid(row=0, column=2, pady=5)
        
        ttk.Label(dir_frame, text="目标目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.target_path_var = tk.StringVar()
        self.target_entry = ttk.Entry(dir_frame, textvariable=self.target_path_var)
        self.target_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=5, pady=5)
        ttk.Button(dir_frame, text="浏览", command=self._browse_target).grid(row=1, column=2, pady=5)
        
        rules_frame = ttk.LabelFrame(parent, text="分类规则", padding="10")
        rules_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.by_type_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(rules_frame, text="按文件类型", variable=self.by_type_var).grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.by_date_var = tk.BooleanVar()
        ttk.Checkbutton(rules_frame, text="按日期", variable=self.by_date_var).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        self.by_size_var = tk.BooleanVar()
        ttk.Checkbutton(rules_frame, text="按大小", variable=self.by_size_var).grid(row=0, column=2, sticky=tk.W, padx=5)
        
        operation_frame = ttk.LabelFrame(parent, text="操作方式", padding="10")
        operation_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.operation_var = tk.StringVar(value="move")
        ttk.Radiobutton(operation_frame, text="移动", variable=self.operation_var, value="move").grid(row=0, column=0, padx=10)
        ttk.Radiobutton(operation_frame, text="复制", variable=self.operation_var, value="copy").grid(row=0, column=1, padx=10)
        
        btn_frame = ttk.Frame(parent)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        
        self.start_btn = ttk.Button(btn_frame, text="开始分类", command=self._start_classification, style="Accent.TButton")
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        ttk.Button(btn_frame, text="预览", command=self._preview).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="设置", command=self._open_settings).pack(side=tk.LEFT, padx=5)
        
        result_frame = ttk.LabelFrame(parent, text="处理结果", padding="10")
        result_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)
        
        self.result_text = tk.Text(result_frame, height=10, wrap=tk.WORD)
        self.result_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        result_scroll = ttk.Scrollbar(result_frame, orient=tk.VERTICAL, command=self.result_text.yview)
        result_scroll.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.result_text.configure(yscrollcommand=result_scroll.set)
        
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, style="Secondary.TLabel")
        status_label.pack(side=tk.LEFT)
        
        self.progress_var = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_var.pack(side=tk.RIGHT, padx=10)
    
    def _browse_source(self):
        """浏览源目录"""
        directory = filedialog.askdirectory(title="选择源目录")
        if directory:
            self.source_path_var.set(directory)
    
    def _browse_target(self):
        """浏览目标目录"""
        directory = filedialog.askdirectory(title="选择目标目录")
        if directory:
            self.target_path_var.set(directory)
    
    def _load_config(self):
        """加载配置"""
        config = self.config_manager.load_config()
        self.source_path_var.set(config.get('source_path', ''))
        self.target_path_var.set(config.get('target_path', ''))
    
    def _process_messages(self):
        """处理消息队列"""
        try:
            while True:
                msg = self.message_queue.get_nowait()
                self._handle_message(msg)
        except queue.Empty:
            pass
        self.root.after(100, self._process_messages)
    
    def _handle_message(self, msg):
        """处理单条消息"""
        msg_type, data = msg
        if msg_type == 'status':
            self.status_var.set(data)
        elif msg_type == 'log':
            self.result_text.insert(tk.END, f"{data}\n")
            self.result_text.see(tk.END)
        elif msg_type == 'complete':
            self.progress_var.stop()
            self.start_btn.configure(state='normal')
    
    def _start_classification(self):
        """开始分类"""
        source = self.source_path_var.get()
        target = self.target_path_var.get()
        
        if not source or not target:
            messagebox.showwarning("警告", "请选择源目录和目标目录")
            return
        
        if not os.path.exists(source):
            messagebox.showerror("错误", "源目录不存在")
            return
        
        self.start_btn.configure(state='disabled')
        self.progress_var.start()
        self.result_text.delete(1.0, tk.END)
        
        rules = []
        if self.by_type_var.get():
            rules.append('by_type')
        if self.by_date_var.get():
            rules.append('by_date')
        if self.by_size_var.get():
            rules.append('by_size')
        
        operation = self.operation_var.get()
        
        def classify_thread():
            try:
                self.message_queue.put(('status', '正在分类...'))
                self.message_queue.put(('log', f"开始分类：{source}"))
                
                results = self.classifier.classify_files(source, target, rules, operation)
                
                success_count = sum(1 for r in results if r.get('success'))
                fail_count = len(results) - success_count
                
                self.message_queue.put(('log', f"\n分类完成！"))
                self.message_queue.put(('log', f"成功：{success_count} 失败：{fail_count}"))
                self.message_queue.put(('complete', None))
                
            except Exception as e:
                self.message_queue.put(('status', f'错误：{str(e)}'))
                self.message_queue.put(('log', f"错误：{str(e)}"))
                self.message_queue.put(('complete', None))
        
        thread = threading.Thread(target=classify_thread, daemon=True)
        thread.start()
    
    def _preview(self):
        """预览分类结果"""
        messagebox.showinfo("预览", "预览功能开发中...")
    
    def _open_settings(self):
        """打开设置"""
        messagebox.showinfo("设置", "设置功能开发中...")
