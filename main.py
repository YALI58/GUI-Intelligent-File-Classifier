#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能文件分类器 - 主程序
提供图形用户界面和完整的文件分类功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import threading
import queue
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 导入自定义模块
from file_classifier import FileClassifier
from config_manager import ConfigManager
from file_monitor import FileMonitor
from ui_theme import apply_wabi_sabi_theme
from ui_theme import create_scrollable_container

# 智能推荐相关导入
try:
    from recommendations_dialog import show_recommendations_dialog
    RECOMMENDATIONS_AVAILABLE = True
except ImportError:
    RECOMMENDATIONS_AVAILABLE = False
    print("智能推荐模块不可用，请检查依赖是否正确安装")

class FileClassifierApp:
    """文件分类器主应用程序"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("智能文件分类器 v1.0")
        self.root.geometry("1000x750")
        self.root.minsize(900, 650)
        
        # 初始化组件
        self.config_manager = ConfigManager()
        
        # 尝试使用增强版分类器
        try:
            from file_classifier_enhanced import EnhancedFileClassifier
            self.classifier = EnhancedFileClassifier()
        except ImportError:
            self.classifier = FileClassifier()
            
        self.file_monitor = None
        
        # 状态变量
        self.monitoring = False
        self.processing = False
        
        # 消息队列（用于线程间通信）
        self.message_queue = queue.Queue()
        
        # 设置UI
        self.setup_ui()
        self.load_config()
        
        # 启动消息处理
        self.process_messages()
        
    def setup_ui(self):
        """设置用户界面"""
        # 创建可滚动内容容器（避免窗口高度不足时底部组件不可见）
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
        content_window = canvas.create_window((0, 0), window=content, anchor="nw")

        def _on_content_configure(_event=None):
            try:
                canvas.configure(scrollregion=canvas.bbox("all"))
            except Exception:
                pass

        def _on_canvas_configure(event=None):
            try:
                if event is not None:
                    canvas.itemconfigure(content_window, width=event.width)
            except Exception:
                pass

        content.bind("<Configure>", _on_content_configure)
        canvas.bind("<Configure>", _on_canvas_configure)

        def _on_mousewheel(event):
            try:
                delta = 0
                if hasattr(event, 'delta') and event.delta:
                    delta = int(-1 * (event.delta / 120))
                elif getattr(event, 'num', None) == 4:
                    delta = -1
                elif getattr(event, 'num', None) == 5:
                    delta = 1
                if delta != 0:
                    canvas.yview_scroll(delta, "units")
            except Exception:
                pass

        def _bind_mousewheel(_event=None):
            try:
                self.root.bind_all("<MouseWheel>", _on_mousewheel)
            except Exception:
                pass

        def _unbind_mousewheel(_event=None):
            try:
                self.root.unbind_all("<MouseWheel>")
            except Exception:
                pass

        content.bind("<Enter>", _bind_mousewheel)
        content.bind("<Leave>", _unbind_mousewheel)

        # 创建顶部框架（标题和状态）
        self.create_header(content)

        # 创建路径选择区域
        self.create_path_selection(content)

        # 创建分类规则设置区域
        self.create_rules_section(content)

        # 创建操作选项区域
        self.create_options_section(content)

        # 创建按钮区域
        self.create_buttons_section(content)

        # 创建结果显示区域
        self.create_results_section(content)

        # 创建状态栏
        self.create_status_bar(content)
        
    def create_header(self, parent):
        """创建标题和状态区域"""
        header_frame = ttk.Frame(parent)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        header_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(header_frame, text="智能文件分类器", style="Title.TLabel")
        title_label.grid(row=0, column=0, sticky=tk.W)
        
        # 状态指示器
        status_frame = ttk.Frame(header_frame)
        status_frame.grid(row=0, column=1, sticky=tk.E)
        
        self.monitor_status_label = ttk.Label(status_frame, text="●", 
                                             foreground="red", font=("Arial", 12))
        self.monitor_status_label.grid(row=0, column=0, padx=5)
        
        ttk.Label(status_frame, text="监控状态").grid(row=0, column=1)
        
    def create_path_selection(self, parent):
        """创建路径选择区域"""
        path_frame = ttk.LabelFrame(parent, text="路径设置", padding="10")
        path_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        path_frame.columnconfigure(1, weight=1)
        
        # 源文件夹选择
        ttk.Label(path_frame, text="源文件夹:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        source_frame = ttk.Frame(path_frame)
        source_frame.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        source_frame.columnconfigure(0, weight=1)
        
        self.source_var = tk.StringVar()
        self.source_combo = ttk.Combobox(source_frame, textvariable=self.source_var, width=60)
        self.source_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(source_frame, text="浏览", 
                  command=self.browse_source).grid(row=0, column=1)
        
        # 目标文件夹选择
        ttk.Label(path_frame, text="目标文件夹:").grid(row=1, column=0, sticky=tk.W, pady=5)
        
        target_frame = ttk.Frame(path_frame)
        target_frame.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=5)
        target_frame.columnconfigure(0, weight=1)
        
        self.target_var = tk.StringVar()
        self.target_combo = ttk.Combobox(target_frame, textvariable=self.target_var, width=60)
        self.target_combo.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        ttk.Button(target_frame, text="浏览", 
                  command=self.browse_target).grid(row=0, column=1)
        
    def create_rules_section(self, parent):
        """创建分类规则设置区域"""
        rules_frame = ttk.LabelFrame(parent, text="分类规则", padding="10")
        rules_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 分类方式选择
        self.rule_vars = {
            'by_type': tk.BooleanVar(value=True),
            'by_date': tk.BooleanVar(value=False),
            'by_size': tk.BooleanVar(value=False),
            'by_custom': tk.BooleanVar(value=False),
            'by_ai': tk.BooleanVar(value=False)
        }
        
        rule_checkboxes_frame = ttk.Frame(rules_frame)
        rule_checkboxes_frame.grid(row=0, column=0, sticky=tk.W)
        
        ttk.Checkbutton(rule_checkboxes_frame, text="按文件类型分类", 
                       variable=self.rule_vars['by_type']).grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Checkbutton(rule_checkboxes_frame, text="按修改日期分类", 
                       variable=self.rule_vars['by_date']).grid(row=0, column=1, sticky=tk.W, padx=5)
        ttk.Checkbutton(rule_checkboxes_frame, text="按文件大小分类", 
                       variable=self.rule_vars['by_size']).grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Checkbutton(rule_checkboxes_frame, text="使用自定义规则", 
                       variable=self.rule_vars['by_custom']).grid(row=0, column=3, sticky=tk.W, padx=5)

        ttk.Checkbutton(rule_checkboxes_frame, text="AI智能分类（仅用于文件归类）", 
                       variable=self.rule_vars['by_ai']).grid(row=1, column=0, sticky=tk.W, padx=5, pady=(6, 0))

        boundary_label = ttk.Label(
            rules_frame,
            text="智能文件分类助手：仅用于自动化文件归类，不支持其他AI操作",
            style="Secondary.TLabel"
        )
        boundary_label.grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
        
    def create_options_section(self, parent):
        """创建操作选项区域"""
        options_frame = ttk.LabelFrame(parent, text="操作选项", padding="10")
        options_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # 操作类型选择
        operation_frame = ttk.Frame(options_frame)
        operation_frame.grid(row=0, column=0, sticky=tk.W)
        
        self.operation_var = tk.StringVar(value="move")
        ttk.Radiobutton(operation_frame, text="移动文件", variable=self.operation_var, 
                       value="move").grid(row=0, column=0, sticky=tk.W, padx=10)
        ttk.Radiobutton(operation_frame, text="复制文件", variable=self.operation_var, 
                       value="copy").grid(row=0, column=1, sticky=tk.W, padx=10)
        ttk.Radiobutton(operation_frame, text="创建链接", variable=self.operation_var, 
                       value="link").grid(row=0, column=2, sticky=tk.W, padx=10)
        
        # 其他选项
        other_options_frame = ttk.Frame(options_frame)
        other_options_frame.grid(row=0, column=1, sticky=tk.E)
        
        self.preview_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(other_options_frame, text="预览模式", 
                       variable=self.preview_var).grid(row=0, column=0, padx=10)
        
        self.confirm_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(other_options_frame, text="确认操作", 
                       variable=self.confirm_var).grid(row=0, column=1, padx=10)
        
        # 文件关联选项 - 新增
        association_frame = ttk.LabelFrame(options_frame, text="文件关联选项", padding="5")
        association_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        association_frame.columnconfigure(0, weight=1)
        
        self.preserve_associations = tk.BooleanVar(value=True)
        preserve_check = ttk.Checkbutton(
            association_frame, 
            text="保持文件关联关系（推荐）", 
            variable=self.preserve_associations
        )
        preserve_check.grid(row=0, column=0, sticky=tk.W)
        
        # 预览关联按钮
        preview_associations_btn = ttk.Button(
            association_frame,
            text="预览文件关联",
            command=self.preview_file_associations
        )
        preview_associations_btn.grid(row=0, column=1, sticky=tk.E, padx=(10, 0))
        
        # 关联说明标签
        info_label = ttk.Label(
            association_frame,
            text="启用后，相关文件（如程序和其依赖库、项目文件等）将保持在同一文件夹中",
            style="Secondary.TLabel"
        )
        info_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))
        
    def create_buttons_section(self, parent):
        """创建按钮区域"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=4, column=0, columnspan=2, pady=15)
        
        # 主要操作按钮
        main_buttons = ttk.Frame(button_frame)
        main_buttons.grid(row=0, column=0, padx=10)
        
        self.classify_btn = ttk.Button(main_buttons, text="开始分类", 
                                      command=self.start_classification)
        self.classify_btn.grid(row=0, column=0, padx=5)
        
        self.preview_btn = ttk.Button(main_buttons, text="预览分类", 
                                     command=self.preview_classification)
        self.preview_btn.grid(row=0, column=1, padx=5)
        
        self.monitor_btn = ttk.Button(main_buttons, text="开始监控", 
                                     command=self.toggle_monitoring)
        self.monitor_btn.grid(row=0, column=2, padx=5)
        
        # 辅助功能按钮
        aux_buttons = ttk.Frame(button_frame)
        aux_buttons.grid(row=0, column=1, padx=10)
        
        ttk.Button(aux_buttons, text="高级设置", 
                  command=self.open_settings_dialog).grid(row=0, column=0, padx=5)
        
        # 多层级分类设置按钮
        ttk.Button(aux_buttons, text="📊 分类设置", 
                  command=self.open_hierarchical_settings).grid(row=0, column=1, padx=5)
        
        # 智能推荐按钮
        if RECOMMENDATIONS_AVAILABLE:
            self.ai_recommend_btn = ttk.Button(aux_buttons, text="🤖 智能推荐", 
                                              command=self.open_recommendations_dialog)
            self.ai_recommend_btn.grid(row=0, column=2, padx=5)
            
            self.undo_btn = ttk.Button(aux_buttons, text="撤销操作", 
                                      command=self.undo_last_operation)
            self.undo_btn.grid(row=0, column=3, padx=5)
            
            ttk.Button(aux_buttons, text="清空结果", 
                      command=self.clear_results).grid(row=0, column=4, padx=5)
        else:
            self.undo_btn = ttk.Button(aux_buttons, text="撤销操作", 
                                      command=self.undo_last_operation)
            self.undo_btn.grid(row=0, column=2, padx=5)
            
            ttk.Button(aux_buttons, text="清空结果", 
                      command=self.clear_results).grid(row=0, column=3, padx=5)
        
    def create_results_section(self, parent):
        """创建结果显示区域"""
        results_frame = ttk.LabelFrame(parent, text="分类结果", padding="10")
        results_frame.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(0, weight=1)
        parent.rowconfigure(5, weight=1)
        
        # 创建Treeview显示结果
        columns = ("文件名", "原位置", "目标位置", "操作", "状态", "大小", "时间")
        self.result_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=12, style="WabiSabi.Treeview")
        
        # 设置列标题和宽度
        column_widths = {"文件名": 150, "原位置": 200, "目标位置": 200, 
                        "操作": 80, "状态": 100, "大小": 80, "时间": 120}
        
        for col in columns:
            self.result_tree.heading(col, text=col, command=lambda c=col: self.sort_results(c))
            self.result_tree.column(col, width=column_widths.get(col, 100))
        
        # 添加滚动条
        scrollbar_y = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.result_tree.yview)
        scrollbar_x = ttk.Scrollbar(results_frame, orient=tk.HORIZONTAL, command=self.result_tree.xview)
        self.result_tree.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        # 布局
        self.result_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_y.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_x.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 绑定右键菜单
        self.create_context_menu()
        
        # 统计信息框架
        stats_frame = ttk.Frame(results_frame)
        stats_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.stats_label = ttk.Label(stats_frame, text="准备就绪")
        self.stats_label.grid(row=0, column=0, sticky=tk.W)
        
        # 进度条
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(stats_frame, variable=self.progress_var, 
                                          mode='determinate')
        self.progress_bar.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        stats_frame.columnconfigure(1, weight=1)
        
    def create_context_menu(self):
        """创建右键菜单"""
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="打开源文件夹", command=self.open_source_folder)
        self.context_menu.add_command(label="打开目标文件夹", command=self.open_target_folder)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制路径", command=self.copy_path)
        self.context_menu.add_command(label="删除记录", command=self.delete_record)
        
        self.result_tree.bind("<Button-3>", self.show_context_menu)
        
    def create_status_bar(self, parent):
        """创建状态栏"""
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(0, weight=1)
        
        self.status_var = tk.StringVar(value="就绪")
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        status_label.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        # 监控统计信息
        self.monitor_stats_var = tk.StringVar(value="")
        monitor_stats_label = ttk.Label(status_frame, textvariable=self.monitor_stats_var)
        monitor_stats_label.grid(row=0, column=1, padx=(10, 0))
        
    def browse_source(self):
        """浏览源文件夹"""
        folder = filedialog.askdirectory(title="选择源文件夹")
        if folder:
            self.source_var.set(folder)
            self.config_manager.add_recent_path(folder, 'source')
            self.update_path_history()
            
    def browse_target(self):
        """浏览目标文件夹"""
        folder = filedialog.askdirectory(title="选择目标文件夹")
        if folder:
            self.target_var.set(folder)
            self.config_manager.add_recent_path(folder, 'target')
            self.update_path_history()
            
    def update_path_history(self):
        """更新路径历史记录"""
        # 更新源路径历史
        recent_sources = self.config_manager.get_recent_paths('source')
        self.source_combo['values'] = recent_sources
        
        # 更新目标路径历史
        recent_targets = self.config_manager.get_recent_paths('target')
        self.target_combo['values'] = recent_targets
    
    def preview_file_associations(self):
        """预览文件关联关系"""
        if not self.source_var.get():
            messagebox.showwarning("提示", "请先选择源文件夹")
            return
        
        if not os.path.exists(self.source_var.get()):
            messagebox.showerror("错误", "源文件夹不存在")
            return
        
        try:
            from file_classifier_enhanced import EnhancedFileClassifier
            enhanced_classifier = EnhancedFileClassifier()
            
            associations = enhanced_classifier.preview_associations(self.source_var.get())
            
            # 创建预览窗口
            self.show_associations_preview(associations)
            
        except Exception as e:
            messagebox.showerror("错误", f"预览文件关联失败: {str(e)}")
    
    def show_associations_preview(self, associations):
        """显示文件关联预览窗口"""
        preview_window = tk.Toplevel(self.root)
        preview_window.title("文件关联预览")
        preview_window.geometry("900x700")
        preview_window.grab_set()
        
        # 设置窗口图标（如果有的话）
        try:
            preview_window.iconbitmap(self.root.iconbitmap())
        except:
            pass
        
        scroll_outer, _scroll_canvas, scroll_content = create_scrollable_container(preview_window, padding=10)
        scroll_outer.pack(fill=tk.BOTH, expand=True)

        # 创建主框架
        main_frame = ttk.Frame(scroll_content)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题和统计信息
        title_frame = ttk.Frame(main_frame)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(title_frame, text="文件关联分析结果", style="Title.TLabel")
        title_label.pack(side=tk.LEFT)
        
        stats_label = ttk.Label(title_frame, 
                               text=f"总文件数: {associations['total_files']} | 关联组数: {associations['total_groups']}")
        stats_label.pack(side=tk.RIGHT)
        
        # 创建滚动文本框
        text_frame = ttk.Frame(main_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD)
        try:
            text_widget.configure(bg="#FAF3E0", fg="#333333")
        except Exception:
            pass
        scrollbar_y = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        scrollbar_x = ttk.Scrollbar(text_frame, orient=tk.HORIZONTAL, command=text_widget.xview)
        text_widget.configure(yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        
        # 填充关联信息
        content = ""
        for group_name, group_info in associations['groups'].items():
            if group_name == 'individual_files':
                content += f"📄 独立文件 ({group_info['file_count']} 个文件)\n"
                content += "    这些文件将按常规规则分类，不保持特殊关联\n"
                if group_info['file_count'] <= 10:  # 只显示前10个文件
                    for file_path in group_info['files']:
                        content += f"    • {Path(file_path).name}\n"
                else:
                    for file_path in group_info['files'][:10]:
                        content += f"    • {Path(file_path).name}\n"
                    content += f"    ... 还有 {group_info['file_count'] - 10} 个文件\n"
                content += "\n"
            else:
                group_type = "未知类型"
                group_desc = ""
                if group_name.startswith('project_'):
                    group_type = "🔧 项目文件夹"
                    group_desc = "包含项目源码、配置文件等，将保持完整性"
                elif group_name.startswith('program_'):
                    group_type = "⚙️ 程序文件组"
                    group_desc = "包含可执行文件及其依赖库、配置文件"
                elif group_name.startswith('web_'):
                    group_type = "🌐 网页文件组"
                    group_desc = "包含HTML文件及相关的CSS、JS、图片资源"
                elif group_name.startswith('media_'):
                    group_type = "🎬 媒体文件组"
                    group_desc = "包含视频文件及其字幕、海报等相关文件"
                elif group_name.startswith('samename_'):
                    group_type = "📋 同名文件组"
                    group_desc = "相同名称但不同扩展名的文件"
                
                content += f"{group_type} ({group_info['file_count']} 个文件)\n"
                content += f"    {group_desc}\n"
                content += f"    主文件: {Path(group_info['main_file']).name}\n"
                content += "    包含文件:\n"
                for file_path in group_info['files']:
                    content += f"      • {Path(file_path).name}\n"
                content += "\n"
        
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)
        
        # 按钮框架
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 关闭按钮
        close_btn = ttk.Button(button_frame, text="关闭", command=preview_window.destroy)
        close_btn.pack(side=tk.RIGHT)
        
        # 导出按钮
        export_btn = ttk.Button(button_frame, text="导出报告", 
                               command=lambda: self.export_association_report(associations))
        export_btn.pack(side=tk.RIGHT, padx=(0, 10))
    
    def export_association_report(self, associations):
        """导出关联分析报告"""
        try:
            from tkinter import filedialog
            
            file_path = filedialog.asksaveasfilename(
                title="保存关联分析报告",
                defaultextension=".txt",
                filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
            )
            
            if not file_path:
                return
            
            # 生成报告内容
            report_content = f"文件关联分析报告\n{'='*50}\n\n"
            report_content += f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            report_content += f"总文件数: {associations['total_files']}\n"
            report_content += f"关联组数: {associations['total_groups']}\n\n"
            
            for group_name, group_info in associations['groups'].items():
                if group_name == 'individual_files':
                    report_content += f"独立文件 ({group_info['file_count']} 个文件)\n"
                    report_content += "这些文件将按常规规则分类\n\n"
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
                    
                    report_content += f"{group_type} ({group_info['file_count']} 个文件)\n"
                    report_content += f"主文件: {Path(group_info['main_file']).name}\n"
                    report_content += "包含文件:\n"
                    for file_path in group_info['files']:
                        report_content += f"  - {Path(file_path).name}\n"
                    report_content += "\n"
            
            # 写入文件
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(report_content)
            
            messagebox.showinfo("成功", f"关联分析报告已保存到:\n{file_path}")
            
        except Exception as e:
            messagebox.showerror("错误", f"导出报告失败: {str(e)}")
        
    def start_classification(self):
        """开始分类"""
        if not self.validate_inputs():
            return

        if not self.validate_ai_ready_if_needed():
            return
            
        if self.processing:
            messagebox.showwarning("警告", "正在处理中，请稍候...")
            return
            
        # 确认操作
        if self.confirm_var.get():
            operation_text = {"move": "移动", "copy": "复制", "link": "链接"}[self.operation_var.get()]
            if not messagebox.askyesno("确认操作", 
                                     f"确定要{operation_text}文件吗？\n\n"
                                     f"源文件夹: {self.source_var.get()}\n"
                                     f"目标文件夹: {self.target_var.get()}"):
                return
        
        # 在新线程中执行分类
        thread = threading.Thread(target=self._classify_files_thread, daemon=True)
        thread.start()
        
    def _classify_files_thread(self):
        """在后台线程中执行文件分类"""
        try:
            self.processing = True
            self.message_queue.put(('status', '正在分类文件...'))
            self.message_queue.put(('disable_buttons', True))
            
            source_path = self.source_var.get()
            target_path = self.target_var.get()
            
            # 获取启用的规则
            enabled_rules = [rule for rule, var in self.rule_vars.items() if var.get()]
            
            # 获取配置
            custom_rules = self.config_manager.get_custom_rules()
            type_mapping = self.config_manager.get_file_type_mapping()
            operation = self.operation_var.get()
            
            # 过滤启用的自定义规则
            enabled_custom_rules = [rule for rule in custom_rules if rule.get('enabled', True)]
            
            # 执行分类 - 使用增强版分类器或原版分类器
            if self.preserve_associations.get():
                # 使用增强版分类器
                if hasattr(self.classifier, 'classify_files_with_associations'):
                    results = self.classifier.classify_files_with_associations(
                        source_path, target_path, enabled_rules, operation,
                        enabled_custom_rules, type_mapping, preserve_associations=True
                    )
                    self.message_queue.put(('status', '正在分析文件关联关系...'))
                else:
                    # 如果当前分类器不支持关联功能，回退到标准分类
                    self.message_queue.put(('status', '增强功能不可用，使用标准分类...'))
                    results = self.classifier.classify_files(
                        source_path, target_path, enabled_rules, operation,
                        enabled_custom_rules, type_mapping
                    )
            else:
                # 使用原版分类器
                results = self.classifier.classify_files(
                    source_path, target_path, enabled_rules, operation,
                    enabled_custom_rules, type_mapping
                )
            
            # 更新结果显示
            self.message_queue.put(('update_results', results))
            
            # 统计关联保护信息
            association_count = sum(1 for r in results if r.get('association_preserved', False))
            if association_count > 0:
                self.message_queue.put(('status', 
                    f'分类完成，共处理 {len(results)} 个文件（其中 {association_count} 个文件保持了关联关系）'))
            else:
                self.message_queue.put(('status', f'分类完成，共处理 {len(results)} 个文件'))
            
        except Exception as e:
            self.message_queue.put(('error', f"分类过程中发生错误: {str(e)}"))
        finally:
            self.processing = False
            self.message_queue.put(('disable_buttons', False))
            
    def preview_classification(self):
        """预览分类结果"""
        if not self.validate_inputs():
            return

        if not self.validate_ai_ready_if_needed():
            return
            
        thread = threading.Thread(target=self._preview_classification_thread, daemon=True)
        thread.start()
        
    def _preview_classification_thread(self):
        """在后台线程中生成预览"""
        try:
            self.message_queue.put(('status', '正在生成预览...'))
            
            source_path = self.source_var.get()
            target_path = self.target_var.get()
            
            enabled_rules = [rule for rule, var in self.rule_vars.items() if var.get()]
            custom_rules = self.config_manager.get_custom_rules()
            type_mapping = self.config_manager.get_file_type_mapping()
            
            enabled_custom_rules = [rule for rule in custom_rules if rule.get('enabled', True)]
            
            # 生成预览 - 使用增强版或原版分类器
            if self.preserve_associations.get():
                if hasattr(self.classifier, 'classify_files_with_associations'):
                    # 增强版分类器暂时使用复制模式生成预览
                    preview_results = self.classifier.classify_files_with_associations(
                        source_path, target_path, enabled_rules, 'copy',
                        enabled_custom_rules, type_mapping, preserve_associations=True
                    )
                    # 将结果标记为预览模式
                    for result in preview_results:
                        result['preview_mode'] = True
                else:
                    # 回退到原版分类器
                    preview_results = self.classifier.preview_classification(
                        source_path, target_path, enabled_rules, 
                        enabled_custom_rules, type_mapping
                    )
            else:
                # 使用原版分类器
                preview_results = self.classifier.preview_classification(
                    source_path, target_path, enabled_rules, 
                    enabled_custom_rules, type_mapping
                )
            
            self.message_queue.put(('update_results', preview_results, True))
            self.message_queue.put(('status', f'预览完成，共 {len(preview_results)} 个文件'))
            
        except Exception as e:
            self.message_queue.put(('error', f"预览过程中发生错误: {str(e)}"))
            
    def toggle_monitoring(self):
        """切换监控状态"""
        if not self.monitoring:
            self.start_monitoring()
        else:
            self.stop_monitoring()
            
    def start_monitoring(self):
        """开始文件夹监控"""
        if not self.source_var.get():
            messagebox.showwarning("警告", "请先选择源文件夹")
            return

        if not self.validate_ai_ready_if_needed():
            return
            
        try:
            source_path = self.source_var.get()
            target_path = self.target_var.get() or source_path
            enabled_rules = [rule for rule, var in self.rule_vars.items() if var.get()]
            operation = self.operation_var.get()
            
            # 创建监控器
            self.file_monitor = FileMonitor(
                source_path, target_path, enabled_rules, 
                operation, self.on_file_processed, self.config_manager
            )
            
            if self.file_monitor.start():
                self.monitoring = True
                self.monitor_btn.config(text="停止监控")
                self.monitor_status_label.config(foreground="green")
                self.status_var.set(f"正在监控文件夹: {source_path}")
                
                # 启动监控统计更新
                self.update_monitor_stats()
            else:
                messagebox.showerror("错误", "启动监控失败")
                
        except Exception as e:
            messagebox.showerror("错误", f"启动监控失败: {str(e)}")

    def validate_ai_ready_if_needed(self) -> bool:
        try:
            if not self.rule_vars.get('by_ai') or not self.rule_vars['by_ai'].get():
                return True

            ai_cfg = self.config_manager.get_setting('ai_service', {}) or {}
            if not isinstance(ai_cfg, dict) or not ai_cfg.get('enabled', False):
                messagebox.showwarning(
                    "提示",
                    "已选择AI智能分类，但AI服务未启用。\n请前往：高级设置 → AI服务 → 密钥管理 开启并配置API密钥。"
                )
                return False

            from secure_storage import SecureKeyStore

            api_key = SecureKeyStore().get_secret('ai_api_key')
            if not api_key:
                messagebox.showwarning(
                    "提示",
                    "已选择AI智能分类，但未检测到API密钥。\n请前往：高级设置 → AI服务 → 密钥管理 输入并保存密钥。"
                )
                return False

            return True
        except Exception:
            messagebox.showwarning(
                "提示",
                "AI分类服务初始化失败，请检查AI配置与网络连接。"
            )
            return False
            
    def stop_monitoring(self):
        """停止文件夹监控"""
        if self.file_monitor:
            self.file_monitor.stop()
            self.file_monitor = None
            
        self.monitoring = False
        self.monitor_btn.config(text="开始监控")
        self.monitor_status_label.config(foreground="red")
        self.monitor_stats_var.set("")
        self.status_var.set("停止监控")
        
    def on_file_processed(self, file_info):
        """文件处理回调"""
        self.message_queue.put(('add_result_item', file_info))
        
    def update_monitor_stats(self):
        """更新监控统计信息"""
        if self.monitoring and self.file_monitor:
            stats = self.file_monitor.get_statistics()
            stats_text = f"已处理: {stats['files_processed']} | "
            stats_text += f"成功: {stats['files_moved'] + stats['files_copied']} | "
            stats_text += f"失败: {stats['files_failed']}"
            
            self.monitor_stats_var.set(stats_text)
            
            # 5秒后再次更新
            self.root.after(5000, self.update_monitor_stats)
            
    def validate_inputs(self):
        """验证输入"""
        if not self.source_var.get():
            messagebox.showwarning("警告", "请选择源文件夹")
            return False
            
        if not os.path.exists(self.source_var.get()):
            messagebox.showerror("错误", "源文件夹不存在")
            return False
            
        if not any(var.get() for var in self.rule_vars.values()):
            messagebox.showwarning("警告", "请至少选择一种分类规则")
            return False
            
        # 验证目标路径
        target_path = self.target_var.get()
        if target_path:
            target_parent = Path(target_path).parent
            if not target_parent.exists():
                messagebox.showerror("错误", "目标文件夹的父目录不存在")
                return False
                
        return True
        
    def update_results(self, results, is_preview=False):
        """更新结果显示"""
        # 清空现有结果
        for item in self.result_tree.get_children():
            self.result_tree.delete(item)
            
        # 添加新结果
        for result in results:
            self.add_result_item(result, is_preview)
            
        # 更新统计信息
        self.update_statistics(results, is_preview)
        
    def add_result_item(self, file_info, is_preview=False):
        """添加单个结果项"""
        try:
            # 格式化文件大小
            size = file_info.get('size', 0)
            if size > 0:
                size_str = self.format_file_size(size)
            else:
                size_str = "未知"
                
            # 格式化时间
            timestamp = file_info.get('timestamp', '')
            if timestamp:
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    time_str = dt.strftime('%H:%M:%S')
                except:
                    time_str = timestamp
            else:
                time_str = datetime.now().strftime('%H:%M:%S')
                
            # 确定状态颜色
            status = file_info.get('status', '')
            success = file_info.get('success', True)
            
            if is_preview:
                status = "预览"
                tags = ("preview",)
            elif success:
                tags = ("success",)
            else:
                tags = ("error",)
                
            # 插入项目
            item = self.result_tree.insert('', 'end', values=(
                file_info.get('filename', ''),
                file_info.get('source', ''),
                file_info.get('target', ''),
                file_info.get('operation', ''),
                status,
                size_str,
                time_str
            ), tags=tags)
            
            # 配置标签样式
            self.result_tree.tag_configure("success", foreground="green")
            self.result_tree.tag_configure("error", foreground="red")
            self.result_tree.tag_configure("preview", foreground="blue")
            
            # 自动滚动到最新项目
            self.result_tree.see(item)
            
        except Exception as e:
            print(f"添加结果项失败: {e}")
            
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0B"
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        while size_bytes >= 1024 and i < len(size_names) - 1:
            size_bytes /= 1024.0
            i += 1
        return f"{size_bytes:.1f}{size_names[i]}"
        
    def update_statistics(self, results, is_preview=False):
        """更新统计信息"""
        total_files = len(results)
        if total_files == 0:
            self.stats_label.config(text="没有文件需要处理")
            return
            
        if is_preview:
            self.stats_label.config(text=f"预览: 共 {total_files} 个文件待处理")
        else:
            success_count = sum(1 for r in results if r.get('success', False))
            failed_count = total_files - success_count
            total_size = sum(r.get('size', 0) for r in results if r.get('success', False))
            
            stats_text = f"完成: {success_count} 成功, {failed_count} 失败, "
            stats_text += f"总大小: {self.format_file_size(total_size)}"
            self.stats_label.config(text=stats_text)
            
    def sort_results(self, column):
        """排序结果"""
        # TODO: 实现结果排序功能
        pass
        
    def show_context_menu(self, event):
        """显示右键菜单"""
        item = self.result_tree.selection()
        if item:
            self.context_menu.post(event.x_root, event.y_root)
            
    def open_source_folder(self):
        """打开源文件夹"""
        item = self.result_tree.selection()
        if item:
            source_path = self.result_tree.item(item[0])['values'][1]
            if source_path:
                self.open_folder_in_explorer(str(Path(source_path).parent))
                
    def open_target_folder(self):
        """打开目标文件夹"""
        item = self.result_tree.selection()
        if item:
            target_path = self.result_tree.item(item[0])['values'][2]
            if target_path:
                self.open_folder_in_explorer(str(Path(target_path).parent))
                
    def open_folder_in_explorer(self, path):
        """在文件管理器中打开文件夹"""
        try:
            if os.name == 'nt':  # Windows
                os.startfile(path)
            elif os.name == 'posix':  # macOS and Linux
                os.system(f'open "{path}"' if sys.platform == 'darwin' else f'xdg-open "{path}"')
        except Exception as e:
            messagebox.showerror("错误", f"无法打开文件夹: {e}")
            
    def copy_path(self):
        """复制路径到剪贴板"""
        item = self.result_tree.selection()
        if item:
            target_path = self.result_tree.item(item[0])['values'][2]
            if target_path:
                self.root.clipboard_clear()
                self.root.clipboard_append(target_path)
                self.status_var.set("路径已复制到剪贴板")
                
    def delete_record(self):
        """删除记录"""
        item = self.result_tree.selection()
        if item:
            if messagebox.askyesno("确认", "确定要删除这条记录吗？"):
                self.result_tree.delete(item[0])
                
    def clear_results(self):
        """清空结果"""
        if messagebox.askyesno("确认", "确定要清空所有结果吗？"):
            for item in self.result_tree.get_children():
                self.result_tree.delete(item)
            self.stats_label.config(text="准备就绪")
            self.progress_var.set(0)
            
    def open_settings_dialog(self):
        """打开设置对话框"""
        try:
            from settings_dialog import SettingsDialog
            dialog = SettingsDialog(self.root, self.config_manager)
            # 设置更改后重新加载配置
            self.load_config()
        except ImportError:
            messagebox.showinfo("提示", "设置功能正在开发中...")
    
    def open_recommendations_dialog(self):
        """打开智能推荐对话框"""
        if not RECOMMENDATIONS_AVAILABLE:
            messagebox.showinfo("提示", "智能推荐功能不可用，请检查依赖是否正确安装")
            return
            
        source_path = self.source_var.get().strip()
        if not source_path:
            # 如果没有设置源路径，提示用户选择
            result = messagebox.askyesno("选择目录", 
                                       "未设置源文件夹。是否选择一个目录进行智能分析？")
            if result:
                folder = filedialog.askdirectory(title="选择要分析的目录")
                if folder:
                    source_path = folder
                else:
                    return
            else:
                return
        
        try:
            # 打开智能推荐对话框
            show_recommendations_dialog(self.root, source_path)
        except Exception as e:
            messagebox.showerror("错误", f"打开智能推荐失败: {str(e)}")
    
    def open_hierarchical_settings(self):
        """打开多层级分类设置对话框"""
        try:
            from hierarchical_settings_dialog import show_hierarchical_settings_dialog
            show_hierarchical_settings_dialog(self.root, self.config_manager)
        except ImportError:
            messagebox.showinfo("提示", "多层级分类设置功能不可用")
        except Exception as e:
            messagebox.showerror("错误", f"打开分类设置失败: {str(e)}")
            
    def undo_last_operation(self):
        """撤销上次操作"""
        try:
            success, message = self.classifier.undo_last_operation()
            if success:
                messagebox.showinfo("成功", message)
                self.status_var.set(message)
            else:
                messagebox.showinfo("提示", message)
        except Exception as e:
            messagebox.showerror("错误", f"撤销操作失败: {str(e)}")
            
    def load_config(self):
        """加载配置"""
        config = self.config_manager.load_config()
        
        # 加载标志文件设置
        if hasattr(self.classifier, 'respect_flag_file'):
            flag_file_config = config.get('flag_file', {
                'enabled': True,
                'name': '.noclassify'
            })
            self.classifier.respect_flag_file = flag_file_config.get('enabled', True)
            self.classifier.flag_file_name = flag_file_config.get('name', '.noclassify')
        
        # 设置路径
        self.source_var.set(config.get('source_path', ''))
        self.target_var.set(config.get('target_path', ''))
        
        # 设置规则状态
        for rule, enabled in config.get('rules', {}).items():
            if rule in self.rule_vars:
                self.rule_vars[rule].set(enabled)
                
        # 设置操作类型
        self.operation_var.set(config.get('operation', 'move'))
        self.preview_var.set(config.get('preview_mode', True))
        self.confirm_var.set(config.get('confirm_operations', True))
        
        # 更新路径历史
        self.update_path_history()
        
        # 设置窗口几何
        geometry = config.get('window_geometry', '1000x750')
        self.root.geometry(geometry)
        
    def save_config(self):
        """保存配置"""
        config = self.config_manager.load_config()
        
        # 保存标志文件设置
        if hasattr(self.classifier, 'respect_flag_file'):
            config['flag_file'] = {
                'enabled': self.classifier.respect_flag_file,
                'name': self.classifier.flag_file_name
            }
        
        # 更新配置
        config['source_path'] = self.source_var.get()
        config['target_path'] = self.target_var.get()
        config['rules'] = {rule: var.get() for rule, var in self.rule_vars.items()}
        config['operation'] = self.operation_var.get()
        config['preview_mode'] = self.preview_var.get()
        config['confirm_operations'] = self.confirm_var.get()
        config['window_geometry'] = self.root.geometry()
        
        self.config_manager.save_config(config)
        
    def process_messages(self):
        """处理消息队列"""
        try:
            while True:
                message = self.message_queue.get_nowait()
                message_type = message[0]
                
                if message_type == 'status':
                    self.status_var.set(message[1])
                elif message_type == 'error':
                    messagebox.showerror("错误", message[1])
                elif message_type == 'update_results':
                    is_preview = len(message) > 2 and message[2]
                    self.update_results(message[1], is_preview)
                elif message_type == 'add_result_item':
                    self.add_result_item(message[1])
                elif message_type == 'disable_buttons':
                    self.set_buttons_enabled(not message[1])
                    
        except queue.Empty:
            pass
        finally:
            # 100ms后再次检查消息队列
            self.root.after(100, self.process_messages)
            
    def set_buttons_enabled(self, enabled):
        """设置按钮可用状态"""
        state = 'normal' if enabled else 'disabled'
        self.classify_btn.config(state=state)
        self.preview_btn.config(state=state)
        if not self.monitoring:  # 只有在不监控时才能改变监控按钮状态
            self.monitor_btn.config(state=state)
            
    def on_closing(self):
        """程序关闭时的清理工作"""
        self.stop_monitoring()
        self.save_config()
        self.root.destroy()

def main():
    """主函数"""
    root = tk.Tk()

    try:
        apply_wabi_sabi_theme(root)
    except Exception:
        pass
    
    # 设置应用图标
    try:
        icon_path = os.path.join('resources', 'icon.ico')
        if os.path.exists(icon_path):
            root.iconbitmap(icon_path)
    except Exception as e:
        print(f"设置图标失败: {e}")
    
    app = FileClassifierApp(root)
    
    # 绑定关闭事件
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # 启动主循环
    root.mainloop()

if __name__ == "__main__":
    main() 