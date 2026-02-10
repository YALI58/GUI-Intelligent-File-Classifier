#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设置对话框模块
提供高级配置选项和自定义规则管理
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from typing import Dict, List, Any
import threading

from ui_theme import apply_wabi_sabi_theme, fade_in_window, create_scrollable_container

class SettingsDialog:
    """设置对话框类"""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config_manager = config_manager
        self.dialog = None
        self.custom_rules = []
        self.file_type_mapping = {}
        
        self.create_dialog()
        
    def create_dialog(self):
        """创建对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("高级设置")
        self.dialog.geometry("800x700")
        self.dialog.resizable(True, True)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_close)

        try:
            apply_wabi_sabi_theme(self.dialog)
        except Exception:
            pass

        try:
            fade_in_window(self.dialog, duration_ms=240, steps=12)
        except Exception:
            pass

        scroll_outer, _scroll_canvas, scroll_content = create_scrollable_container(self.dialog, padding=10)
        scroll_outer.pack(fill=tk.BOTH, expand=True)
        
        # 创建笔记本控件
        notebook = ttk.Notebook(scroll_content)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 创建各个标签页
        self.create_file_type_tab(notebook)
        self.create_custom_rules_tab(notebook)
        self.create_advanced_tab(notebook)
        self.create_exclude_tab(notebook)
        self.create_ai_service_tab(notebook)
        self.create_association_tab(notebook)
        
        # 按钮框架
        button_frame = ttk.Frame(scroll_content)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        ttk.Button(button_frame, text="保存", 
                  command=self.save_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="重置", 
                  command=self.reset_settings).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="导入配置", 
                  command=self.import_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="导出配置", 
                  command=self.export_config).pack(side=tk.LEFT, padx=5)
        
        # 加载当前设置
        self.load_settings()
        
        # 居中显示
        self.center_dialog()

    def on_close(self):
        try:
            if messagebox.askyesno("提示", "关闭前是否保存设置？"):
                self.save_settings()
                return
        except Exception:
            pass
        try:
            self.dialog.destroy()
        except Exception:
            pass
        
    def create_file_type_tab(self, notebook):
        """创建文件类型映射标签页"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="文件类型")
        
        # 说明标签
        info_label = ttk.Label(frame, text="配置不同文件扩展名对应的分类文件夹")
        info_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # 创建滚动框架
        canvas = tk.Canvas(frame)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        self.type_frame = ttk.Frame(canvas)
        
        self.type_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.type_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)
        
        # 存储文件类型映射控件
        self.type_entries = {}
        
    def populate_file_type_mapping(self):
        """填充文件类型映射"""
        # 清空现有控件
        for widget in self.type_frame.winfo_children():
            widget.destroy()
            
        self.type_entries.clear()
        
        row = 0
        for type_name, extensions in self.file_type_mapping.items():
            # 类型名标签
            ttk.Label(self.type_frame, text=f"{type_name}:").grid(
                row=row, column=0, sticky=tk.W, padx=5, pady=2
            )
            
            # 扩展名输入框
            extensions_str = ', '.join(extensions)
            entry = ttk.Entry(self.type_frame, width=60)
            entry.insert(0, extensions_str)
            entry.grid(row=row, column=1, sticky=(tk.W, tk.E), padx=5, pady=2)
            
            self.type_entries[type_name] = entry
            self.type_frame.columnconfigure(1, weight=1)
            
            row += 1
            
    def create_custom_rules_tab(self, notebook):
        """创建自定义规则标签页"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="自定义规则")
        
        # 说明标签
        info_label = ttk.Label(frame, 
            text="创建基于文件名模式的自定义分类规则\n"
                 "支持通配符: * (任意字符) ? (单个字符)")
        info_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # 规则列表框架
        list_frame = ttk.Frame(frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 规则列表
        columns = ("启用", "名称", "模式", "目标文件夹", "描述")
        self.rules_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12, style="WabiSabi.Treeview")
        
        column_widths = {"启用": 50, "名称": 100, "模式": 120, "目标文件夹": 150, "描述": 200}
        for col in columns:
            self.rules_tree.heading(col, text=col)
            self.rules_tree.column(col, width=column_widths.get(col, 100))
            
        # 滚动条
        rules_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.rules_tree.yview)
        self.rules_tree.configure(yscrollcommand=rules_scrollbar.set)
        
        self.rules_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        rules_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 按钮框架
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="添加规则", 
                  command=self.add_custom_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="编辑规则", 
                  command=self.edit_custom_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="删除规则", 
                  command=self.delete_custom_rule).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="切换启用", 
                  command=self.toggle_rule_enabled).pack(side=tk.LEFT, padx=5)
                  
    def create_advanced_tab(self, notebook):
        """创建高级设置标签页"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="高级设置")
        
        # 标志文件设置
        flag_frame = ttk.LabelFrame(frame, text="标志文件设置", padding="10")
        flag_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 启用标志文件
        self.respect_flag_file = tk.BooleanVar(value=True)
        ttk.Checkbutton(flag_frame, text="启用标志文件功能", 
                       variable=self.respect_flag_file).pack(anchor=tk.W)
        
        # 标志文件名称
        flag_name_frame = ttk.Frame(flag_frame)
        flag_name_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(flag_name_frame, text="标志文件名称:").pack(side=tk.LEFT)
        self.flag_file_name = tk.StringVar(value=".noclassify")
        flag_entry = ttk.Entry(flag_name_frame, textvariable=self.flag_file_name)
        flag_entry.pack(side=tk.LEFT, padx=(5, 0))
        
        # 说明文本
        info_text = """当文件夹中存在标志文件时，该文件夹及其子文件夹将被跳过不进行分类。
这对于保持某些特定文件夹的结构很有用，比如软件安装目录、项目文件夹等。
您可以通过在文件夹中创建一个名为".noclassify"（或自定义名称）的空文件来标记该文件夹。"""
        info_label = ttk.Label(flag_frame, text=info_text, wraplength=600, 
                             justify=tk.LEFT, foreground="gray")
        info_label.pack(anchor=tk.W, pady=(5, 0))
        
        # 重复文件处理
        duplicate_frame = ttk.LabelFrame(frame, text="重复文件处理", padding=10)
        duplicate_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.duplicate_var = tk.StringVar()
        ttk.Radiobutton(duplicate_frame, text="重命名（推荐）", variable=self.duplicate_var, 
                       value="rename").pack(anchor=tk.W)
        ttk.Radiobutton(duplicate_frame, text="跳过", variable=self.duplicate_var, 
                       value="skip").pack(anchor=tk.W)
        ttk.Radiobutton(duplicate_frame, text="覆盖（危险）", variable=self.duplicate_var, 
                       value="overwrite").pack(anchor=tk.W)
        
        # 监控设置
        monitor_frame = ttk.LabelFrame(frame, text="监控设置", padding=10)
        monitor_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.monitor_subfolders_var = tk.BooleanVar()
        ttk.Checkbutton(monitor_frame, text="监控子文件夹", 
                       variable=self.monitor_subfolders_var).pack(anchor=tk.W)
        
        self.auto_start_monitoring_var = tk.BooleanVar()
        ttk.Checkbutton(monitor_frame, text="启动时自动开始监控", 
                       variable=self.auto_start_monitoring_var).pack(anchor=tk.W)
        
        # 监控延迟设置
        delay_frame = ttk.Frame(monitor_frame)
        delay_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(delay_frame, text="监控延迟 (秒):").pack(side=tk.LEFT)
        self.monitor_delay_var = tk.DoubleVar()
        delay_spin = ttk.Spinbox(delay_frame, from_=0.1, to=10.0, increment=0.1, 
                                textvariable=self.monitor_delay_var, width=10)
        delay_spin.pack(side=tk.LEFT, padx=5)
        
        # 性能设置
        performance_frame = ttk.LabelFrame(frame, text="性能设置", padding=10)
        performance_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.parallel_processing_var = tk.BooleanVar()
        ttk.Checkbutton(performance_frame, text="启用并行处理", 
                       variable=self.parallel_processing_var).pack(anchor=tk.W)
        
        workers_frame = ttk.Frame(performance_frame)
        workers_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(workers_frame, text="最大工作线程数:").pack(side=tk.LEFT)
        self.max_workers_var = tk.IntVar()
        workers_spin = ttk.Spinbox(workers_frame, from_=1, to=16, 
                                  textvariable=self.max_workers_var, width=10)
        workers_spin.pack(side=tk.LEFT, padx=5)
        
        # 其他设置
        other_frame = ttk.LabelFrame(frame, text="其他设置", padding=10)
        other_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.auto_create_folders_var = tk.BooleanVar()
        ttk.Checkbutton(other_frame, text="自动创建目标文件夹", 
                       variable=self.auto_create_folders_var).pack(anchor=tk.W)
        
        self.preserve_timestamps_var = tk.BooleanVar()
        ttk.Checkbutton(other_frame, text="保留文件时间戳", 
                       variable=self.preserve_timestamps_var).pack(anchor=tk.W)
        
        self.use_recycle_bin_var = tk.BooleanVar()
        ttk.Checkbutton(other_frame, text="删除文件时使用回收站", 
                       variable=self.use_recycle_bin_var).pack(anchor=tk.W)
        
    def create_exclude_tab(self, notebook):
        """创建排除设置标签页"""
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="排除设置")
        
        # 说明标签
        info_label = ttk.Label(frame, text="设置要排除的文件模式和大小限制")
        info_label.pack(anchor=tk.W, padx=10, pady=5)
        
        # 排除模式
        exclude_frame = ttk.LabelFrame(frame, text="排除模式", padding=10)
        exclude_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 排除模式列表
        list_frame = ttk.Frame(exclude_frame)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        self.exclude_listbox = tk.Listbox(list_frame, height=8)
        exclude_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, 
                                         command=self.exclude_listbox.yview)
        self.exclude_listbox.configure(yscrollcommand=exclude_scrollbar.set)
        
        self.exclude_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        exclude_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 排除模式操作按钮
        exclude_btn_frame = ttk.Frame(exclude_frame)
        exclude_btn_frame.pack(fill=tk.X, pady=5)
        
        self.exclude_entry = ttk.Entry(exclude_btn_frame, width=30)
        self.exclude_entry.pack(side=tk.LEFT, padx=(0, 5))
        
        ttk.Button(exclude_btn_frame, text="添加", 
                  command=self.add_exclude_pattern).pack(side=tk.LEFT, padx=2)
        ttk.Button(exclude_btn_frame, text="删除", 
                  command=self.remove_exclude_pattern).pack(side=tk.LEFT, padx=2)
        
        # 文件大小限制
        size_frame = ttk.LabelFrame(frame, text="文件大小限制", padding=10)
        size_frame.pack(fill=tk.X, padx=10, pady=5)
        
        # 最小文件大小
        min_size_frame = ttk.Frame(size_frame)
        min_size_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(min_size_frame, text="最小文件大小 (字节):").pack(side=tk.LEFT)
        self.min_file_size_var = tk.IntVar()
        ttk.Entry(min_size_frame, textvariable=self.min_file_size_var, width=15).pack(side=tk.LEFT, padx=5)
        
        # 最大文件大小
        max_size_frame = ttk.Frame(size_frame)
        max_size_frame.pack(fill=tk.X, pady=2)
        
        ttk.Label(max_size_frame, text="最大文件大小 (字节):").pack(side=tk.LEFT)
        self.max_file_size_var = tk.IntVar()
        ttk.Entry(max_size_frame, textvariable=self.max_file_size_var, width=15).pack(side=tk.LEFT, padx=5)

    def create_ai_service_tab(self, notebook):
        frame = ttk.Frame(notebook)
        notebook.add(frame, text="AI服务")

        header_frame = ttk.LabelFrame(frame, text="密钥管理", padding=10)
        header_frame.pack(fill=tk.X, padx=10, pady=10)

        info_text = "请输入您的AI服务API密钥，该密钥仅用于文件智能分类分析，我们不会保存或中转您的密钥。"
        ttk.Label(header_frame, text=info_text, wraplength=650, justify=tk.LEFT).pack(anchor=tk.W)

        self.ai_enabled_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(header_frame, text="启用AI智能分类（仅用于文件归类）", variable=self.ai_enabled_var).pack(anchor=tk.W, pady=(8, 0))

        key_row = ttk.Frame(header_frame)
        key_row.pack(fill=tk.X, pady=(10, 0))
        ttk.Label(key_row, text="API密钥:").pack(side=tk.LEFT)
        self.ai_api_key_var = tk.StringVar()
        self.ai_api_key_entry = ttk.Entry(key_row, textvariable=self.ai_api_key_var, show="*", width=50)
        self.ai_api_key_entry.pack(side=tk.LEFT, padx=(8, 8), fill=tk.X, expand=True)

        self.ai_validate_btn = ttk.Button(key_row, text="验证密钥", command=self.validate_ai_key)
        self.ai_validate_btn.pack(side=tk.LEFT)

        status_row = ttk.Frame(header_frame)
        status_row.pack(fill=tk.X, pady=(8, 0))
        self.ai_key_status_dot = ttk.Label(status_row, text="●", foreground="gray")
        self.ai_key_status_dot.pack(side=tk.LEFT, padx=(0, 6))
        self.ai_key_status_text = tk.StringVar(value="未配置")
        ttk.Label(status_row, textvariable=self.ai_key_status_text).pack(side=tk.LEFT)

        self.ai_clear_key_btn = ttk.Button(header_frame, text="清除本地密钥", command=self.clear_ai_key)
        self.ai_clear_key_btn.pack(anchor=tk.W, pady=(8, 0))

        provider_frame = ttk.LabelFrame(frame, text="服务商配置", padding=10)
        provider_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        row0 = ttk.Frame(provider_frame)
        row0.pack(fill=tk.X, pady=2)
        ttk.Label(row0, text="服务商:").pack(side=tk.LEFT)
        self.ai_provider_var = tk.StringVar(value="openai")
        self.ai_provider_combo = ttk.Combobox(
            row0,
            textvariable=self.ai_provider_var,
            values=["openai", "deepseek"],
            width=20,
            state="readonly"
        )
        self.ai_provider_combo.pack(side=tk.LEFT, padx=(8, 0))
        self.ai_provider_combo.bind("<<ComboboxSelected>>", self.on_ai_provider_change)

        ttk.Label(row0, text="推荐使用具备文本理解与分类能力的AI模型", foreground="gray").pack(side=tk.LEFT, padx=(12, 0))

        row1 = ttk.Frame(provider_frame)
        row1.pack(fill=tk.X, pady=2)
        ttk.Label(row1, text="Endpoint:").pack(side=tk.LEFT)
        self.ai_endpoint_var = tk.StringVar(value="https://api.openai.com/v1/chat/completions")
        ttk.Entry(row1, textvariable=self.ai_endpoint_var).pack(side=tk.LEFT, padx=(8, 0), fill=tk.X, expand=True)

        row2 = ttk.Frame(provider_frame)
        row2.pack(fill=tk.X, pady=2)
        ttk.Label(row2, text="Model:").pack(side=tk.LEFT)
        self.ai_model_var = tk.StringVar(value="gpt-4o-mini")
        ttk.Entry(row2, textvariable=self.ai_model_var, width=30).pack(side=tk.LEFT, padx=(8, 0))

        row3 = ttk.Frame(provider_frame)
        row3.pack(fill=tk.X, pady=2)
        ttk.Label(row3, text="代理(可选):").pack(side=tk.LEFT)
        self.ai_proxy_var = tk.StringVar(value="")
        ttk.Entry(row3, textvariable=self.ai_proxy_var).pack(side=tk.LEFT, padx=(8, 0), fill=tk.X, expand=True)

        mode_frame = ttk.LabelFrame(frame, text="隐私与用量", padding=10)
        mode_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        self.ai_filename_only_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(mode_frame, text="仅分析文件名（不发送文件内容片段）", variable=self.ai_filename_only_var).pack(anchor=tk.W)

        self.ai_content_assist_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            mode_frame,
            text="允许使用文件内容辅助分类（将发送少量文本片段到第三方AI）",
            variable=self.ai_content_assist_var
        ).pack(anchor=tk.W, pady=(6, 0))

        assist_row = ttk.Frame(mode_frame)
        assist_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(assist_row, text="最大上传字符数:").pack(side=tk.LEFT)
        self.ai_max_content_chars_var = tk.IntVar(value=2000)
        ttk.Entry(assist_row, textvariable=self.ai_max_content_chars_var, width=10).pack(side=tk.LEFT, padx=(8, 0))
        ttk.Label(assist_row, text="(仅对白名单文本类型生效)", foreground="gray").pack(side=tk.LEFT, padx=(10, 0))

        exts_row = ttk.Frame(mode_frame)
        exts_row.pack(fill=tk.X, pady=(6, 0))
        ttk.Label(exts_row, text="白名单扩展名:").pack(side=tk.LEFT)
        self.ai_allowed_text_exts_var = tk.StringVar(value=".txt,.md,.py,.json,.csv")
        ttk.Entry(exts_row, textvariable=self.ai_allowed_text_exts_var).pack(side=tk.LEFT, padx=(8, 0), fill=tk.X, expand=True)

        self.ai_desensitize_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(mode_frame, text="内容脱敏（邮箱/手机号/身份证掩码）", variable=self.ai_desensitize_var).pack(anchor=tk.W, pady=(6, 0))

        usage_row = ttk.Frame(mode_frame)
        usage_row.pack(fill=tk.X, pady=(8, 0))
        ttk.Label(usage_row, text="分类功能使用量:").pack(side=tk.LEFT)
        self.ai_usage_var = tk.StringVar(value="已用 0 次")
        ttk.Label(usage_row, textvariable=self.ai_usage_var).pack(side=tk.LEFT, padx=(8, 0))

    def on_ai_provider_change(self, _event=None):
        provider = (self.ai_provider_var.get() or '').strip().lower()
        if provider == 'deepseek':
            endpoint = self.ai_endpoint_var.get().strip()
            model = self.ai_model_var.get().strip()
            if (not endpoint) or endpoint == 'https://api.openai.com/v1/chat/completions':
                self.ai_endpoint_var.set('https://api.deepseek.com/v1/chat/completions')
            if (not model) or model == 'gpt-4o-mini':
                self.ai_model_var.set('deepseek-chat')
        else:
            endpoint = self.ai_endpoint_var.get().strip()
            model = self.ai_model_var.get().strip()
            if (not endpoint) or endpoint == 'https://api.deepseek.com/v1/chat/completions':
                self.ai_endpoint_var.set('https://api.openai.com/v1/chat/completions')
            if (not model) or model == 'deepseek-chat':
                self.ai_model_var.set('gpt-4o-mini')

    def _set_ai_key_status(self, status: str):
        mapping = {
            '未配置': ('gray', '未配置'),
            '已配置': ('gray', '已配置'),
            '连接中...': ('blue', '连接中...'),
            '有效': ('green', '有效'),
            '无效': ('red', '无效'),
            '配置错误': ('orange', '配置错误'),
            '权限受限': ('orange', '权限受限'),
            '网络异常': ('orange', '网络异常'),
            '连接失败': ('red', '连接失败')
        }
        color, text = mapping.get(status, ('gray', status))
        self.ai_key_status_dot.configure(foreground=color)
        self.ai_key_status_text.set(text)

    def _get_key_store(self):
        from secure_storage import SecureKeyStore

        return SecureKeyStore()

    def validate_ai_key(self):
        def _worker():
            try:
                from ai_service import FileCategorizationAIClient

                cfg = self.config_manager.get_nested_setting('ai_service', default={}) or {}
                api_key = self.ai_api_key_var.get().strip()
                if not api_key:
                    api_key = self._get_key_store().get_secret('ai_api_key') or ''

                if not api_key:
                    self.dialog.after(0, lambda: self._set_ai_key_status('未配置'))
                    return

                client = FileCategorizationAIClient(
                    api_key=api_key,
                    provider=str(self.ai_provider_var.get() or cfg.get('provider', 'openai')),
                    endpoint=str(self.ai_endpoint_var.get() or cfg.get('endpoint', 'https://api.openai.com/v1/chat/completions')),
                    model=str(self.ai_model_var.get() or cfg.get('model', 'gpt-4o-mini')),
                    proxy=str(self.ai_proxy_var.get() or cfg.get('proxy', '')),
                )
                ok, status = client.validate_key()
                self.dialog.after(0, lambda: self._set_ai_key_status('有效' if ok else status))
                if not ok:
                    if status == '无效':
                        self.dialog.after(0, lambda: messagebox.showerror(
                            "验证失败",
                            "密钥验证失败，请检查：\n1. 密钥是否正确\n2. 该密钥是否具有AI分类权限\n3. 网络连接是否正常"
                        ))
            except Exception as e:
                err_type = type(e).__name__
                err_msg = str(e)
                if err_msg and len(err_msg) > 300:
                    err_msg = err_msg[:300]

                def _ui_fail():
                    self._set_ai_key_status('连接失败')
                    messagebox.showerror(
                        "连接失败",
                        f"AI服务验证发生异常（不包含密钥信息）。\n错误类型: {err_type}\n错误信息: {err_msg or '无'}"
                    )

                try:
                    self.dialog.after(0, _ui_fail)
                except Exception:
                    pass

        self._set_ai_key_status('连接中...')
        threading.Thread(target=_worker, daemon=True).start()

    def clear_ai_key(self):
        try:
            if not messagebox.askyesno("确认", "确定要清除本地存储的AI服务API密钥吗？"):
                return

            self._get_key_store().delete_secret('ai_api_key')
            self.ai_api_key_var.set('')
            self._set_ai_key_status('未配置')
            messagebox.showinfo("完成", "本地密钥已清除")
        except Exception:
            messagebox.showerror("错误", "清除本地密钥失败")
        
    def load_settings(self):
        """加载当前设置"""
        config = self.config_manager.load_config()
        
        # 加载标志文件设置
        flag_file_config = config.get('flag_file', {
            'enabled': True,
            'name': '.noclassify'
        })
        self.respect_flag_file.set(flag_file_config.get('enabled', True))
        self.flag_file_name.set(flag_file_config.get('name', '.noclassify'))
        
        # 加载文件类型映射
        self.file_type_mapping = config.get('file_type_mapping', {})
        self.populate_file_type_mapping()
        
        # 加载自定义规则
        self.custom_rules = config.get('custom_rules', [])
        self.populate_custom_rules()
        
        # 加载高级设置
        self.duplicate_var.set(config.get('handle_duplicates', 'rename'))
        self.monitor_subfolders_var.set(config.get('monitor_subfolders', True))
        self.auto_start_monitoring_var.set(config.get('auto_start_monitoring', False))
        self.monitor_delay_var.set(config.get('monitor_delay', 1.0))
        self.parallel_processing_var.set(config.get('parallel_processing', True))
        self.max_workers_var.set(config.get('max_workers', 4))
        self.auto_create_folders_var.set(config.get('auto_create_folders', True))
        self.preserve_timestamps_var.set(config.get('preserve_timestamps', True))
        self.use_recycle_bin_var.set(config.get('use_recycle_bin', True))
        
        # 加载排除设置
        exclude_patterns = config.get('exclude_patterns', [])
        self.exclude_listbox.delete(0, tk.END)
        for pattern in exclude_patterns:
            self.exclude_listbox.insert(tk.END, pattern)
            
        self.min_file_size_var.set(config.get('min_file_size', 0))
        self.max_file_size_var.set(config.get('max_file_size', 1024*1024*1024))

        ai_cfg = config.get('ai_service', {}) if isinstance(config.get('ai_service', {}), dict) else {}
        self.ai_enabled_var.set(bool(ai_cfg.get('enabled', False)))
        self.ai_provider_var.set(ai_cfg.get('provider', 'openai'))
        self.ai_endpoint_var.set(ai_cfg.get('endpoint', 'https://api.openai.com/v1/chat/completions'))
        self.ai_model_var.set(ai_cfg.get('model', 'gpt-4o-mini'))
        self.ai_proxy_var.set(ai_cfg.get('proxy', ''))
        self.ai_filename_only_var.set(bool(ai_cfg.get('filename_only', True)))
        try:
            self.ai_content_assist_var.set(bool(ai_cfg.get('content_assist_enabled', False)))
        except Exception:
            self.ai_content_assist_var.set(False)
        try:
            self.ai_max_content_chars_var.set(int(ai_cfg.get('max_content_chars', 2000)))
        except Exception:
            self.ai_max_content_chars_var.set(2000)
        try:
            exts = ai_cfg.get('allowed_text_exts', ['.txt', '.md', '.py', '.json', '.csv'])
            if isinstance(exts, list):
                self.ai_allowed_text_exts_var.set(','.join([str(x) for x in exts if str(x).strip()]))
        except Exception:
            pass
        try:
            self.ai_desensitize_var.set(bool(ai_cfg.get('desensitize_enabled', True)))
        except Exception:
            self.ai_desensitize_var.set(True)
        try:
            used = int(ai_cfg.get('usage_used_calls', 0))
        except Exception:
            used = 0
        self.ai_usage_var.set(f"已用 {max(0, used)} 次")

        try:
            stored = self._get_key_store().get_secret('ai_api_key')
            self._set_ai_key_status('未配置' if not stored else '已配置')
        except Exception:
            self._set_ai_key_status('未配置')

        try:
            self.on_ai_provider_change()
        except Exception:
            pass

    def create_association_tab(self, notebook):
        association_frame = ttk.Frame(notebook)
        notebook.add(association_frame, text="文件关联")

        main_frame = ttk.Frame(association_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        info_label = ttk.Label(
            main_frame,
            text="启用后，相关文件（如程序与依赖库、项目文件等）将尽量保持在同一文件夹中。",
            justify=tk.LEFT
        )
        info_label.pack(anchor=tk.W)
        
    def populate_custom_rules(self):
        """填充自定义规则"""
        # 清空现有项目
        for item in self.rules_tree.get_children():
            self.rules_tree.delete(item)
            
        # 添加规则
        for rule in self.custom_rules:
            enabled = "✓" if rule.get('enabled', True) else "✗"
            self.rules_tree.insert('', 'end', values=(
                enabled,
                rule.get('name', ''),
                rule.get('pattern', ''),
                rule.get('target_folder', ''),
                rule.get('description', '')
            ))
            
    def add_custom_rule(self):
        """添加自定义规则"""
        dialog = CustomRuleDialog(self.dialog)
        if dialog.result:
            self.custom_rules.append(dialog.result)
            self.populate_custom_rules()
            
    def edit_custom_rule(self):
        """编辑自定义规则"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要编辑的规则")
            return
            
        item = selection[0]
        index = self.rules_tree.index(item)
        
        current_rule = self.custom_rules[index]
        dialog = CustomRuleDialog(self.dialog, current_rule)
        
        if dialog.result:
            self.custom_rules[index] = dialog.result
            self.populate_custom_rules()
            
    def delete_custom_rule(self):
        """删除自定义规则"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要删除的规则")
            return
            
        if messagebox.askyesno("确认", "确定要删除选中的规则吗？"):
            item = selection[0]
            index = self.rules_tree.index(item)
            del self.custom_rules[index]
            self.populate_custom_rules()
            
    def toggle_rule_enabled(self):
        """切换规则启用状态"""
        selection = self.rules_tree.selection()
        if not selection:
            messagebox.showwarning("警告", "请选择要切换的规则")
            return
            
        item = selection[0]
        index = self.rules_tree.index(item)
        
        rule = self.custom_rules[index]
        rule['enabled'] = not rule.get('enabled', True)
        self.populate_custom_rules()
        
    def add_exclude_pattern(self):
        """添加排除模式"""
        pattern = self.exclude_entry.get().strip()
        if pattern:
            self.exclude_listbox.insert(tk.END, pattern)
            self.exclude_entry.delete(0, tk.END)
            
    def remove_exclude_pattern(self):
        """删除排除模式"""
        selection = self.exclude_listbox.curselection()
        if selection:
            self.exclude_listbox.delete(selection[0])
            
    def save_settings(self):
        """保存设置"""
        try:
            config = self.config_manager.load_config()
            
            # 保存标志文件设置
            config['flag_file'] = {
                'enabled': self.respect_flag_file.get(),
                'name': self.flag_file_name.get()
            }
            
            # 保存文件类型映射
            new_mapping = {}
            for type_name, entry in self.type_entries.items():
                extensions_str = entry.get().strip()
                if extensions_str:
                    extensions = [ext.strip() for ext in extensions_str.split(',')]
                    # 确保扩展名以点开头
                    extensions = [ext if ext.startswith('.') else f'.{ext}' for ext in extensions if ext]
                    new_mapping[type_name] = extensions
                else:
                    new_mapping[type_name] = []
                    
            config['file_type_mapping'] = new_mapping
            
            # 保存自定义规则
            config['custom_rules'] = self.custom_rules
            
            # 保存高级设置
            config['handle_duplicates'] = self.duplicate_var.get()
            config['monitor_subfolders'] = self.monitor_subfolders_var.get()
            config['auto_start_monitoring'] = self.auto_start_monitoring_var.get()
            config['monitor_delay'] = self.monitor_delay_var.get()
            config['parallel_processing'] = self.parallel_processing_var.get()
            config['max_workers'] = self.max_workers_var.get()
            config['auto_create_folders'] = self.auto_create_folders_var.get()
            config['preserve_timestamps'] = self.preserve_timestamps_var.get()
            config['use_recycle_bin'] = self.use_recycle_bin_var.get()
            
            # 保存排除设置
            exclude_patterns = [self.exclude_listbox.get(i) for i in range(self.exclude_listbox.size())]
            config['exclude_patterns'] = exclude_patterns
            config['min_file_size'] = self.min_file_size_var.get()
            config['max_file_size'] = self.max_file_size_var.get()

            filename_only = bool(self.ai_filename_only_var.get())
            content_assist_enabled = bool(self.ai_content_assist_var.get())
            if filename_only:
                content_assist_enabled = False

            config['ai_service'] = {
                'enabled': self.ai_enabled_var.get(),
                'provider': self.ai_provider_var.get().strip() or 'openai',
                'endpoint': self.ai_endpoint_var.get().strip() or 'https://api.openai.com/v1/chat/completions',
                'model': self.ai_model_var.get().strip() or 'gpt-4o-mini',
                'filename_only': filename_only,
                'content_assist_enabled': content_assist_enabled,
                'max_content_chars': int(self.ai_max_content_chars_var.get()),
                'allowed_text_exts': [e.strip() for e in (self.ai_allowed_text_exts_var.get() or '').split(',') if e.strip()],
                'desensitize_enabled': bool(self.ai_desensitize_var.get()),
                'proxy': self.ai_proxy_var.get().strip(),
                'usage_used_calls': int((config.get('ai_service') or {}).get('usage_used_calls', 0))
            }

            key_input = self.ai_api_key_var.get().strip()
            if key_input:
                self._get_key_store().set_secret('ai_api_key', key_input)
            
            # 保存配置
            if self.config_manager.save_config(config):
                messagebox.showinfo("成功", "设置已保存")
                self.dialog.destroy()
            else:
                messagebox.showerror("错误", "保存设置失败")
            
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {str(e)}")
            
    def reset_settings(self):
        """重置设置"""
        if messagebox.askyesno("确认", "确定要重置所有设置到默认值吗？"):
            if self.config_manager.reset_to_default():
                self.load_settings()
                messagebox.showinfo("成功", "设置已重置")
            else:
                messagebox.showerror("错误", "重置设置失败")
                
    def export_config(self):
        """导出配置"""
        filename = filedialog.asksaveasfilename(
            title="导出配置文件",
            defaultextension=".json",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            if self.config_manager.export_config(filename):
                messagebox.showinfo("成功", f"配置已导出到: {filename}")
            else:
                messagebox.showerror("错误", "导出配置失败")
                
    def import_config(self):
        """导入配置"""
        filename = filedialog.askopenfilename(
            title="导入配置文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        
        if filename:
            if messagebox.askyesno("确认", "导入配置将覆盖当前设置，确定要继续吗？"):
                if self.config_manager.import_config(filename):
                    self.load_settings()
                    messagebox.showinfo("成功", "配置已导入")
                else:
                    messagebox.showerror("错误", "导入配置失败")
            
    def center_dialog(self):
        """居中显示对话框"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')

class CustomRuleDialog:
    """自定义规则编辑对话框"""
    
    def __init__(self, parent, rule=None):
        self.parent = parent
        self.result = None
        self.dialog = None
        
        self.create_dialog(rule)
        
    def create_dialog(self, rule):
        """创建规则编辑对话框"""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("自定义规则")
        self.dialog.geometry("500x350")
        self.dialog.resizable(False, False)
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        try:
            scroll_outer, _scroll_canvas, scroll_content = create_scrollable_container(self.dialog, padding=20)
            scroll_outer.pack(fill=tk.BOTH, expand=True)
            main_frame = ttk.Frame(scroll_content)
            main_frame.pack(fill=tk.BOTH, expand=True)
        except Exception:
            main_frame = ttk.Frame(self.dialog, padding=20)
            main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 规则名称
        ttk.Label(main_frame, text="规则名称:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.name_var = tk.StringVar(value=rule.get('name', '') if rule else '')
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        name_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 模式输入
        ttk.Label(main_frame, text="文件名模式:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.pattern_var = tk.StringVar(value=rule.get('pattern', '') if rule else '')
        pattern_entry = ttk.Entry(main_frame, textvariable=self.pattern_var, width=40)
        pattern_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 目标文件夹
        ttk.Label(main_frame, text="目标文件夹:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.folder_var = tk.StringVar(value=rule.get('target_folder', '') if rule else '')
        folder_entry = ttk.Entry(main_frame, textvariable=self.folder_var, width=40)
        folder_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 描述
        ttk.Label(main_frame, text="描述:").grid(row=3, column=0, sticky=tk.W, pady=5)
        self.desc_var = tk.StringVar(value=rule.get('description', '') if rule else '')
        desc_entry = ttk.Entry(main_frame, textvariable=self.desc_var, width=40)
        desc_entry.grid(row=3, column=1, sticky=(tk.W, tk.E), pady=5, padx=(10, 0))
        
        # 启用状态
        self.enabled_var = tk.BooleanVar(value=rule.get('enabled', True) if rule else True)
        ttk.Checkbutton(main_frame, text="启用此规则", 
                       variable=self.enabled_var).grid(row=4, column=1, sticky=tk.W, pady=5, padx=(10, 0))
        
        main_frame.columnconfigure(1, weight=1)
        
        # 示例说明
        example_frame = ttk.LabelFrame(main_frame, text="模式示例", padding=10)
        example_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        examples = [
            "*.jpg - 所有jpg文件",
            "报告* - 以'报告'开头的文件",
            "*_backup.* - 以'_backup'结尾的文件",
            "???.txt - 三个字符的txt文件",
            "*重要* - 文件名包含'重要'的文件"
        ]
        
        for example in examples:
            ttk.Label(example_frame, text=example).pack(anchor=tk.W)
            
        # 按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=6, column=0, columnspan=2, pady=20)
        
        ttk.Button(button_frame, text="确定", 
                  command=self.save_rule).pack(side=tk.RIGHT, padx=5)
        ttk.Button(button_frame, text="取消", 
                  command=self.dialog.destroy).pack(side=tk.RIGHT, padx=5)
                  
        # 居中显示
        self.center_dialog()
        
    def save_rule(self):
        """保存规则"""
        name = self.name_var.get().strip()
        pattern = self.pattern_var.get().strip()
        folder = self.folder_var.get().strip()
        
        if not name:
            messagebox.showwarning("警告", "请输入规则名称")
            return
            
        if not pattern:
            messagebox.showwarning("警告", "请输入文件名模式")
            return
            
        if not folder:
            messagebox.showwarning("警告", "请输入目标文件夹")
            return
            
        self.result = {
            'name': name,
            'pattern': pattern,
            'target_folder': folder,
            'description': self.desc_var.get().strip(),
            'enabled': self.enabled_var.get()
        }
        
        self.dialog.destroy()
        
    def center_dialog(self):
        """居中显示对话框"""
        self.dialog.update_idletasks()
        width = self.dialog.winfo_width()
        height = self.dialog.winfo_height()
        x = (self.dialog.winfo_screenwidth() // 2) - (width // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (height // 2)
        self.dialog.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_association_tab(self, notebook):
        """创建文件关联配置标签页"""
        association_frame = ttk.Frame(notebook)
        notebook.add(association_frame, text="文件关联")
        
        # 主框架
        main_frame = ttk.Frame(association_frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 说明文本
        info_text = """
文件关联功能可以保持相关文件在同一文件夹中，避免破坏文件间的依赖关系。

支持的关联类型：
• 程序文件：可执行文件与其依赖库保持一起
• 项目文件夹：包含源码、配置文件的项目目录  
• 网页文件：HTML文件与相关的CSS、JS、图片文件
• 媒体集合：视频文件与字幕、海报等相关文件
• 同名文件：相同名称但不同扩展名的文件
        """
        
        info_label = ttk.Label(main_frame, text=info_text.strip(), justify=tk.LEFT, 
                              font=("微软雅黑", 9))
        info_label.pack(anchor=tk.W, pady=(0, 15))
        
        # 关联规则配置
        rules_frame = ttk.LabelFrame(main_frame, text="关联规则配置", padding="10")
        rules_frame.pack(fill=tk.BOTH, expand=True)
        
        # 程序文件关联
        program_frame = ttk.LabelFrame(rules_frame, text="程序文件关联", padding="8")
        program_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.enable_program_association = tk.BooleanVar(value=True)
        program_check = ttk.Checkbutton(
            program_frame, 
            text="启用程序文件关联检测", 
            variable=self.enable_program_association
        )
        program_check.pack(anchor=tk.W)
        
        program_desc = ttk.Label(
            program_frame,
            text="主文件类型: .exe, .app, .jar | 相关文件: .dll, .so, .ini, .cfg",
            foreground="gray",
            font=("微软雅黑", 8)
        )
        program_desc.pack(anchor=tk.W, pady=(2, 0))
        
        # 项目文件关联
        project_frame = ttk.LabelFrame(rules_frame, text="项目文件关联", padding="8")
        project_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.enable_project_association = tk.BooleanVar(value=True)
        project_check = ttk.Checkbutton(
            project_frame, 
            text="启用项目文件夹检测", 
            variable=self.enable_project_association
        )
        project_check.pack(anchor=tk.W)
        
        project_desc = ttk.Label(
            project_frame,
            text="检测标志: package.json, requirements.txt, .gitignore 等项目指示文件",
            foreground="gray",
            font=("微软雅黑", 8)
        )
        project_desc.pack(anchor=tk.W, pady=(2, 0))
        
        # 网页文件关联
        web_frame = ttk.LabelFrame(rules_frame, text="网页文件关联", padding="8")
        web_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.enable_web_association = tk.BooleanVar(value=True)
        web_check = ttk.Checkbutton(
            web_frame, 
            text="启用网页文件关联检测", 
            variable=self.enable_web_association
        )
        web_check.pack(anchor=tk.W)
        
        web_desc = ttk.Label(
            web_frame,
            text="HTML文件与同名或相关的CSS、JS、图片等资源文件保持一起",
            foreground="gray",
            font=("微软雅黑", 8)
        )
        web_desc.pack(anchor=tk.W, pady=(2, 0))
        
        # 媒体文件关联
        media_frame = ttk.LabelFrame(rules_frame, text="媒体文件关联", padding="8")
        media_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.enable_media_association = tk.BooleanVar(value=True)
        media_check = ttk.Checkbutton(
            media_frame, 
            text="启用媒体文件关联检测", 
            variable=self.enable_media_association
        )
        media_check.pack(anchor=tk.W)
        
        media_desc = ttk.Label(
            media_frame,
            text="视频文件与同名字幕文件(.srt, .ass)、海报图片等保持一起",
            foreground="gray",
            font=("微软雅黑", 8)
        )
        media_desc.pack(anchor=tk.W, pady=(2, 0))
        
        # 同名文件关联
        samename_frame = ttk.LabelFrame(rules_frame, text="同名文件关联", padding="8")
        samename_frame.pack(fill=tk.X, pady=(0, 8))
        
        self.enable_samename_association = tk.BooleanVar(value=True)
        samename_check = ttk.Checkbutton(
            samename_frame, 
            text="启用同名文件关联检测", 
            variable=self.enable_samename_association
        )
        samename_check.pack(anchor=tk.W)
        
        samename_desc = ttk.Label(
            samename_frame,
            text="相同文件名但不同扩展名的文件将保持在同一文件夹中",
            foreground="gray",
            font=("微软雅黑", 8)
        )
        samename_desc.pack(anchor=tk.W, pady=(2, 0))
        
        # 测试和重置按钮
        test_frame = ttk.Frame(rules_frame)
        test_frame.pack(fill=tk.X, pady=(15, 0))
        
        test_btn = ttk.Button(
            test_frame, 
            text="测试关联检测", 
            command=self.test_association_detection
        )
        test_btn.pack(side=tk.LEFT)
        
        reset_btn = ttk.Button(
            test_frame, 
            text="重置为默认", 
            command=self.reset_association_settings
        )
        reset_btn.pack(side=tk.LEFT, padx=(10, 0))
        
        # 关联强度设置
        strength_frame = ttk.LabelFrame(rules_frame, text="关联强度设置", padding="8")
        strength_frame.pack(fill=tk.X, pady=(15, 0))
        
        ttk.Label(strength_frame, text="项目文件密度阈值:").pack(anchor=tk.W)
        self.project_threshold = tk.DoubleVar(value=0.5)
        threshold_scale = ttk.Scale(
            strength_frame, 
            from_=0.1, 
            to=0.9, 
            variable=self.project_threshold,
            orient=tk.HORIZONTAL
        )
        threshold_scale.pack(fill=tk.X, pady=(2, 0))
        
        threshold_desc = ttk.Label(
            strength_frame,
            text="值越高，要求项目文件夹中代码/配置文件比例越高才被识别为项目",
            foreground="gray",
            font=("微软雅黑", 8)
        )
        threshold_desc.pack(anchor=tk.W, pady=(2, 0))
    
    def test_association_detection(self):
        """测试关联检测功能"""
        test_folder = filedialog.askdirectory(
            title="选择测试文件夹",
            parent=self.dialog
        )
        if not test_folder:
            return
        
        try:
            from file_classifier_enhanced import EnhancedFileClassifier
            enhanced_classifier = EnhancedFileClassifier()
            
            associations = enhanced_classifier.preview_associations(test_folder)
            
            # 显示结果
            result_text = (
                f"检测完成！\n\n"
                f"总文件数: {associations['total_files']}\n"
                f"关联组数: {associations['total_groups']}\n\n"
                f"详细信息:\n"
            )
            
            for group_name, group_info in associations['groups'].items():
                if group_name == 'individual_files':
                    result_text += f"• 独立文件: {group_info['file_count']} 个\n"
                else:
                    group_type = ""
                    if group_name.startswith('project_'):
                        group_type = "项目文件夹"
                    elif group_name.startswith('program_'):
                        group_type = "程序文件组"
                    elif group_name.startswith('web_'):
                        group_type = "网页文件组"
                    elif group_name.startswith('media_'):
                        group_type = "媒体文件组"
                    elif group_name.startswith('samename_'):
                        group_type = "同名文件组"
                    
                    result_text += f"• {group_type}: {group_info['file_count']} 个文件\n"
            
            messagebox.showinfo("检测结果", result_text, parent=self.dialog)
            
        except ImportError:
            messagebox.showerror(
                "功能不可用", 
                "增强版文件分类器模块不可用，请检查文件是否存在。",
                parent=self.dialog
            )
        except Exception as e:
            messagebox.showerror("错误", f"检测失败: {str(e)}", parent=self.dialog)
    
    def reset_association_settings(self):
        """重置关联设置为默认值"""
        self.enable_program_association.set(True)
        self.enable_project_association.set(True)
        self.enable_web_association.set(True)
        self.enable_media_association.set(True)
        self.enable_samename_association.set(True)
        self.project_threshold.set(0.5)
        messagebox.showinfo("提示", "已重置为默认设置", parent=self.dialog) 