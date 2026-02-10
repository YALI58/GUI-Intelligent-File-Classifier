#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多层级分类设置对话框
允许用户配置智能分类参数
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Any, List

from ui_theme import create_scrollable_container

class HierarchicalSettingsDialog:
    """多层级分类设置对话框"""
    
    def __init__(self, parent, config_manager):
        self.parent = parent
        self.config_manager = config_manager
        
        # 创建对话框窗口
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("多层级分类设置")
        self.dialog.geometry("600x500")
        self.dialog.resizable(True, True)
        
        # 设置窗口属性
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 加载当前配置
        self.current_config = self._load_hierarchical_config()
        
        self.setup_ui()
        self.load_settings()
    
    def _load_hierarchical_config(self) -> Dict[str, Any]:
        """加载多层级分类配置"""
        config = self.config_manager.load_config()
        return config.get('hierarchical_classification', {
            'enabled': True,
            'max_files_per_folder': 50,
            'date_granularity': 'month',
            'enable_project_detection': True,
            'filename_pattern_recognition': True,
            'max_depth': 4,
            'min_files_for_subdivision': 20,
            'auto_create_subfolders': True,
            'enable_smart_size_classification': True,
            'enable_usage_based_classification': True
        })
    
    def setup_ui(self):
        """设置用户界面"""
        scroll_outer, _scroll_canvas, scroll_content = create_scrollable_container(self.dialog, padding=10)
        scroll_outer.pack(fill=tk.BOTH, expand=True)

        # 主框架
        main_frame = ttk.Frame(scroll_content)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建笔记本控件
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 基本设置页面
        self.setup_basic_tab()
        
        # 高级设置页面
        self.setup_advanced_tab()
        
        # 分类规则页面
        self.setup_rules_tab()
        
        # 按钮框架
        self.setup_button_frame(main_frame)
    
    def setup_basic_tab(self):
        """设置基本配置页面"""
        basic_frame = ttk.Frame(self.notebook)
        self.notebook.add(basic_frame, text="基本设置")
        
        # 启用多层级分类
        enable_frame = ttk.LabelFrame(basic_frame, text="多层级分类", padding="10")
        enable_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.enabled_var = tk.BooleanVar()
        ttk.Checkbutton(enable_frame, text="启用多层级智能分类", 
                       variable=self.enabled_var,
                       command=self.on_enable_changed).pack(anchor=tk.W)
        
        ttk.Label(enable_frame, text="启用后，系统将创建更详细的文件夹结构，便于文件查找", 
                 font=("微软雅黑", 9), foreground="gray").pack(anchor=tk.W, pady=(5, 0))
        
        # 分类深度设置
        depth_frame = ttk.LabelFrame(basic_frame, text="分类深度", padding="10")
        depth_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(depth_frame, text="最大分类深度:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_depth_var = tk.StringVar()
        depth_combo = ttk.Combobox(depth_frame, textvariable=self.max_depth_var, 
                                  values=["2", "3", "4", "5", "6"], width=10, state="readonly")
        depth_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        ttk.Label(depth_frame, text="层", font=("微软雅黑", 9)).grid(row=0, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 文件数量阈值
        threshold_frame = ttk.LabelFrame(basic_frame, text="智能阈值", padding="10")
        threshold_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(threshold_frame, text="每个文件夹最大文件数:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.max_files_var = tk.StringVar()
        ttk.Entry(threshold_frame, textvariable=self.max_files_var, width=10).grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(threshold_frame, text="个", font=("微软雅黑", 9)).grid(row=0, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        ttk.Label(threshold_frame, text="启用细分的最小文件数:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.min_files_var = tk.StringVar()
        ttk.Entry(threshold_frame, textvariable=self.min_files_var, width=10).grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(threshold_frame, text="个", font=("微软雅黑", 9)).grid(row=1, column=2, sticky=tk.W, padx=(5, 0), pady=5)
        
        # 自动创建文件夹
        auto_frame = ttk.LabelFrame(basic_frame, text="自动化设置", padding="10")
        auto_frame.pack(fill=tk.X)
        
        self.auto_create_var = tk.BooleanVar()
        ttk.Checkbutton(auto_frame, text="自动创建子文件夹", 
                       variable=self.auto_create_var).pack(anchor=tk.W)
        
        ttk.Label(auto_frame, text="当文件数量超过阈值时，自动创建更详细的分类文件夹", 
                 font=("微软雅黑", 9), foreground="gray").pack(anchor=tk.W, pady=(5, 0))
    
    def setup_advanced_tab(self):
        """设置高级配置页面"""
        advanced_frame = ttk.Frame(self.notebook)
        self.notebook.add(advanced_frame, text="高级设置")
        
        # 时间分类设置
        time_frame = ttk.LabelFrame(advanced_frame, text="时间分类", padding="10")
        time_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(time_frame, text="时间分类粒度:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.date_granularity_var = tk.StringVar()
        granularity_combo = ttk.Combobox(time_frame, textvariable=self.date_granularity_var,
                                       values=["year", "quarter", "month", "week"], 
                                       width=15, state="readonly")
        granularity_combo.grid(row=0, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        granularity_info = {
            "year": "按年份分类 (2024/)",
            "quarter": "按季度分类 (2024/Q1/)",
            "month": "按月份分类 (2024/Q1/01-January/)",
            "week": "按周分类 (2024/Q1/01-January/Week01/)"
        }
        
        self.granularity_info_var = tk.StringVar()
        ttk.Label(time_frame, textvariable=self.granularity_info_var, 
                 font=("微软雅黑", 9), foreground="blue").grid(row=1, column=0, columnspan=2, 
                                                             sticky=tk.W, pady=(5, 0))
        
        def on_granularity_changed(*args):
            selected = self.date_granularity_var.get()
            self.granularity_info_var.set(granularity_info.get(selected, ""))
        
        self.date_granularity_var.trace('w', on_granularity_changed)
        
        # 智能识别设置
        recognition_frame = ttk.LabelFrame(advanced_frame, text="智能识别", padding="10")
        recognition_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.pattern_recognition_var = tk.BooleanVar()
        ttk.Checkbutton(recognition_frame, text="启用文件名模式识别", 
                       variable=self.pattern_recognition_var).pack(anchor=tk.W)
        ttk.Label(recognition_frame, text="自动识别截图、照片、报告等文件类型", 
                 font=("微软雅黑", 9), foreground="gray").pack(anchor=tk.W, padx=(20, 0))
        
        self.project_detection_var = tk.BooleanVar()
        ttk.Checkbutton(recognition_frame, text="启用项目结构检测", 
                       variable=self.project_detection_var).pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(recognition_frame, text="自动识别Web、Python、Java等项目结构", 
                 font=("微软雅黑", 9), foreground="gray").pack(anchor=tk.W, padx=(20, 0))
        
        self.smart_size_var = tk.BooleanVar()
        ttk.Checkbutton(recognition_frame, text="启用智能大小分类", 
                       variable=self.smart_size_var).pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(recognition_frame, text="根据文件类型调整大小分类阈值", 
                 font=("微软雅黑", 9), foreground="gray").pack(anchor=tk.W, padx=(20, 0))
        
        self.usage_classification_var = tk.BooleanVar()
        ttk.Checkbutton(recognition_frame, text="启用使用频率分类", 
                       variable=self.usage_classification_var).pack(anchor=tk.W, pady=(10, 0))
        ttk.Label(recognition_frame, text="基于文件访问时间进行分类", 
                 font=("微软雅黑", 9), foreground="gray").pack(anchor=tk.W, padx=(20, 0))
    
    def setup_rules_tab(self):
        """设置分类规则页面"""
        rules_frame = ttk.Frame(self.notebook)
        self.notebook.add(rules_frame, text="分类规则")
        
        # 分类示例
        example_frame = ttk.LabelFrame(rules_frame, text="分类效果示例", padding="10")
        example_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 创建树形视图显示分类示例
        self.example_tree = ttk.Treeview(example_frame, show="tree")
        example_scrollbar = ttk.Scrollbar(example_frame, orient="vertical", command=self.example_tree.yview)
        self.example_tree.configure(yscrollcommand=example_scrollbar.set)
        
        self.example_tree.pack(side="left", fill="both", expand=True)
        example_scrollbar.pack(side="right", fill="y")
        
        # 刷新示例按钮
        refresh_frame = ttk.Frame(rules_frame)
        refresh_frame.pack(fill=tk.X)
        
        ttk.Button(refresh_frame, text="预览分类效果", 
                  command=self.update_classification_preview).pack(side=tk.LEFT)
        
        ttk.Label(refresh_frame, text="根据当前设置预览文件分类结构", 
                 font=("微软雅黑", 9), foreground="gray").pack(side=tk.LEFT, padx=(10, 0))
    
    def setup_button_frame(self, parent):
        """设置按钮框架"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X)
        
        # 左侧按钮
        left_buttons = ttk.Frame(button_frame)
        left_buttons.pack(side=tk.LEFT)
        
        ttk.Button(left_buttons, text="恢复默认", command=self.restore_defaults).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(left_buttons, text="测试配置", command=self.test_configuration).pack(side=tk.LEFT)
        
        # 右侧按钮
        right_buttons = ttk.Frame(button_frame)
        right_buttons.pack(side=tk.RIGHT)
        
        ttk.Button(right_buttons, text="取消", command=self.dialog.destroy).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(right_buttons, text="应用", command=self.apply_settings).pack(side=tk.RIGHT, padx=(5, 0))
        ttk.Button(right_buttons, text="确定", command=self.save_and_close).pack(side=tk.RIGHT, padx=(5, 0))
    
    def load_settings(self):
        """加载设置到界面"""
        config = self.current_config
        
        self.enabled_var.set(config.get('enabled', True))
        self.max_depth_var.set(str(config.get('max_depth', 4)))
        self.max_files_var.set(str(config.get('max_files_per_folder', 50)))
        self.min_files_var.set(str(config.get('min_files_for_subdivision', 20)))
        self.auto_create_var.set(config.get('auto_create_subfolders', True))
        self.date_granularity_var.set(config.get('date_granularity', 'month'))
        self.pattern_recognition_var.set(config.get('filename_pattern_recognition', True))
        self.project_detection_var.set(config.get('enable_project_detection', True))
        self.smart_size_var.set(config.get('enable_smart_size_classification', True))
        self.usage_classification_var.set(config.get('enable_usage_based_classification', True))
        
        # 触发状态更新
        self.on_enable_changed()
        
        # 更新分类预览
        self.update_classification_preview()
    
    def on_enable_changed(self):
        """当启用状态改变时"""
        enabled = self.enabled_var.get()
        
        # 根据启用状态控制其他控件
        state = "normal" if enabled else "disabled"
        
        # 这里可以添加控件状态控制逻辑
        # 例如：禁用/启用相关的设置项
    
    def update_classification_preview(self):
        """更新分类效果预览"""
        # 清除现有项目
        for item in self.example_tree.get_children():
            self.example_tree.delete(item)
        
        if not self.enabled_var.get():
            self.example_tree.insert('', 'end', text="多层级分类已禁用", tags=('disabled',))
            return
        
        # 生成示例分类结构
        examples = self._generate_classification_examples()
        
        for example in examples:
            self._add_tree_node('', example)
    
    def _generate_classification_examples(self) -> List[Dict]:
        """生成分类示例"""
        max_depth = int(self.max_depth_var.get())
        granularity = self.date_granularity_var.get()
        
        examples = []
        
        # 文档示例
        doc_example = {
            'text': 'documents',
            'children': []
        }
        
        if max_depth > 1:
            doc_example['children'].extend([
                {'text': 'work', 'children': [
                    {'text': 'reports', 'children': []},
                    {'text': 'presentations', 'children': []},
                ]},
                {'text': 'personal', 'children': [
                    {'text': 'notes', 'children': []},
                    {'text': 'diaries', 'children': []},
                ]}
            ])
            
            # 添加时间分类示例
            if 'by_date' in ['by_date']:  # 模拟启用时间分类
                time_parts = []
                if granularity == 'year':
                    time_parts = ['2024']
                elif granularity == 'quarter':
                    time_parts = ['2024', 'Q1']
                elif granularity == 'month':
                    time_parts = ['2024', 'Q1', '01-January']
                elif granularity == 'week':
                    time_parts = ['2024', 'Q1', '01-January', 'Week01']
                
                for part in time_parts:
                    doc_example['children'][0]['children'][0]['children'].append({'text': part, 'children': []})
        
        examples.append(doc_example)
        
        # 图片示例
        img_example = {
            'text': 'images',
            'children': [
                {'text': 'photos', 'children': [
                    {'text': 'mobile_photos', 'children': []},
                    {'text': 'screenshots', 'children': []},
                ]},
                {'text': 'graphics', 'children': [
                    {'text': 'icons', 'children': []},
                    {'text': 'logos', 'children': []},
                ]}
            ]
        }
        examples.append(img_example)
        
        # 媒体示例
        media_example = {
            'text': 'media',
            'children': [
                {'text': 'videos', 'children': [
                    {'text': 'movies', 'children': []},
                    {'text': 'clips', 'children': []},
                ]},
                {'text': 'audio', 'children': [
                    {'text': 'music', 'children': []},
                    {'text': 'podcasts', 'children': []},
                ]}
            ]
        }
        examples.append(media_example)
        
        return examples
    
    def _add_tree_node(self, parent, node_data):
        """递归添加树节点"""
        node_id = self.example_tree.insert(parent, 'end', text=node_data['text'])
        
        for child in node_data.get('children', []):
            self._add_tree_node(node_id, child)
    
    def test_configuration(self):
        """测试配置"""
        try:
            # 验证配置参数
            max_depth = int(self.max_depth_var.get())
            max_files = int(self.max_files_var.get())
            min_files = int(self.min_files_var.get())
            
            if max_depth < 2 or max_depth > 6:
                raise ValueError("分类深度必须在2-6之间")
            if max_files < 10 or max_files > 1000:
                raise ValueError("每文件夹最大文件数必须在10-1000之间")
            if min_files < 5 or min_files > 100:
                raise ValueError("最小细分文件数必须在5-100之间")
            
            messagebox.showinfo("测试成功", "配置参数验证通过！")
            
        except ValueError as e:
            messagebox.showerror("配置错误", str(e))
    
    def restore_defaults(self):
        """恢复默认设置"""
        result = messagebox.askyesno("确认", "是否恢复所有设置为默认值？")
        if result:
            self.current_config = {
                'enabled': True,
                'max_files_per_folder': 50,
                'date_granularity': 'month',
                'enable_project_detection': True,
                'filename_pattern_recognition': True,
                'max_depth': 4,
                'min_files_for_subdivision': 20,
                'auto_create_subfolders': True,
                'enable_smart_size_classification': True,
                'enable_usage_based_classification': True
            }
            self.load_settings()
    
    def apply_settings(self):
        """应用设置"""
        try:
            # 收集设置
            config = {
                'enabled': self.enabled_var.get(),
                'max_depth': int(self.max_depth_var.get()),
                'max_files_per_folder': int(self.max_files_var.get()),
                'min_files_for_subdivision': int(self.min_files_var.get()),
                'auto_create_subfolders': self.auto_create_var.get(),
                'date_granularity': self.date_granularity_var.get(),
                'filename_pattern_recognition': self.pattern_recognition_var.get(),
                'enable_project_detection': self.project_detection_var.get(),
                'enable_smart_size_classification': self.smart_size_var.get(),
                'enable_usage_based_classification': self.usage_classification_var.get()
            }
            
            # 保存到配置管理器
            full_config = self.config_manager.load_config()
            full_config['hierarchical_classification'] = config
            self.config_manager.save_config(full_config)
            
            messagebox.showinfo("成功", "设置已应用！")
            
        except ValueError as e:
            messagebox.showerror("设置错误", f"请检查输入的数值: {e}")
        except Exception as e:
            messagebox.showerror("错误", f"保存设置失败: {e}")
    
    def save_and_close(self):
        """保存设置并关闭"""
        self.apply_settings()
        self.dialog.destroy()

def show_hierarchical_settings_dialog(parent, config_manager):
    """显示多层级分类设置对话框"""
    dialog = HierarchicalSettingsDialog(parent, config_manager)
    return dialog 