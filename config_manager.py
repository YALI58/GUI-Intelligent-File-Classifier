#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置管理模块
负责应用程序设置的保存、加载和管理
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

class ConfigManager:
    """配置管理器类"""
    
    def __init__(self):
        self.config_file = Path.home() / '.file_classifier_config.json'
        self.default_config = self._get_default_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            # 基本设置
            'version': '1.0.0',
            'source_path': '',
            'target_path': '',
            
            # 分类规则设置
            'rules': {
                'by_type': True,
                'by_date': False,
                'by_size': False,
                'by_custom': False,
                'by_ai': False
            },
            
            # 操作设置
            'operation': 'move',  # move, copy, link
            'preview_mode': True,
            
            # 重复文件处理
            'handle_duplicates': 'rename',  # rename, skip, overwrite
            
            # 监控设置
            'monitor_subfolders': True,
            'auto_start_monitoring': False,
            'monitor_delay': 1.0,  # 秒
            
            # 界面设置
            'window_geometry': '900x700',
            'theme': 'default',
            'auto_save_config': True,
            'show_tooltips': True,
            
            # 文件操作设置
            'auto_create_folders': True,
            'preserve_timestamps': True,
            'confirm_operations': True,
            'use_recycle_bin': True,
            
            # 自定义规则
            'custom_rules': [
                {
                    'name': '示例规则',
                    'pattern': '*.backup',
                    'target_folder': '备份文件',
                    'description': '匹配所有备份文件',
                    'enabled': False
                }
            ],
            
            # 文件类型映射
            'file_type_mapping': {
                'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', 
                          '.svg', '.webp', '.ico', '.raw', '.heic', '.heif'],
                'documents': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages',
                             '.md', '.tex', '.epub', '.mobi'],
                'spreadsheets': ['.xls', '.xlsx', '.csv', '.ods', '.numbers', '.tsv'],
                'presentations': ['.ppt', '.pptx', '.odp', '.key'],
                'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
                         '.opus', '.ape', '.ac3', '.dts'],
                'videos': ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
                          '.m4v', '.3gp', '.ogv', '.ts', '.vob'],
                'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
                            '.cab', '.ace', '.arj', '.lzh'],
                'code': ['.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h',
                        '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.ts', '.jsx',
                        '.vue', '.sql', '.sh', '.bat', '.ps1', '.xml', '.json', '.yaml'],
                'executables': ['.exe', '.msi', '.deb', '.rpm', '.dmg', '.app', '.pkg',
                               '.run', '.bin', '.jar'],
                'fonts': ['.ttf', '.otf', '.woff', '.woff2', '.eot'],
                'others': []
            },
            
            # 排除设置
            'exclude_patterns': [
                '.*',  # 隐藏文件
                'Thumbs.db',
                'Desktop.ini',
                '.DS_Store',
                '__pycache__',
                '*.tmp',
                '*.temp'
            ],
            
            # 高级设置
            'max_file_size': 1024 * 1024 * 1024,  # 1GB
            'min_file_size': 0,
            'parallel_processing': True,
            'max_workers': 4,
            'log_level': 'INFO',

            'ai_service': {
                'enabled': False,
                'provider': 'openai',
                'endpoint': 'https://api.openai.com/v1/chat/completions',
                'model': 'gpt-4o-mini',
                'filename_only': True,
                'content_assist_enabled': False,
                'max_content_chars': 2000,
                'allowed_text_exts': ['.txt', '.md', '.py', '.json', '.csv', '.log', '.yaml', '.yml', '.ini', '.cfg', '.xml'],
                'desensitize_enabled': True,
                'proxy': '',
                'usage_used_calls': 0
            },
            
            # 最近使用的路径
            'recent_sources': [],
            'recent_targets': [],
            'max_recent_items': 10
        }
        
    def load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # 合并默认配置，确保所有必要的键都存在
                merged_config = self._merge_configs(self.default_config, config)
                
                # 验证配置
                validated_config = self._validate_config(merged_config)
                
                return validated_config
            else:
                # 如果配置文件不存在，创建默认配置文件
                self.save_config(self.default_config)
                return self.default_config.copy()
                
        except Exception as e:
            print(f"加载配置失败: {e}")
            return self.default_config.copy()
            
    def save_config(self, config: Dict[str, Any]) -> bool:
        """保存配置文件"""
        try:
            # 验证配置
            validated_config = self._validate_config(config)
            
            # 确保配置目录存在
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存配置
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(validated_config, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"保存配置失败: {e}")
            return False
            
    def _merge_configs(self, default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
        """递归合并配置字典"""
        merged = default.copy()
        
        for key, value in user.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                merged[key] = self._merge_configs(merged[key], value)
            else:
                merged[key] = value
                
        return merged
        
    def _validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """验证配置的有效性"""
        # 确保必要的键存在
        if 'rules' not in config:
            config['rules'] = self.default_config['rules'].copy()
        else:
            if 'by_ai' not in config['rules']:
                config['rules']['by_ai'] = False
            
        if 'file_type_mapping' not in config:
            config['file_type_mapping'] = self.default_config['file_type_mapping'].copy()

        if 'ai_service' not in config or not isinstance(config.get('ai_service'), dict):
            config['ai_service'] = self.default_config['ai_service'].copy()
        else:
            for k, v in self.default_config['ai_service'].items():
                if k not in config['ai_service']:
                    config['ai_service'][k] = v
            
        # 验证路径
        for path_key in ['source_path', 'target_path']:
            if path_key in config and config[path_key]:
                try:
                    path = Path(config[path_key])
                    config[path_key] = str(path.resolve())
                except Exception:
                    config[path_key] = ''
                    
        # 验证数值范围
        if 'max_recent_items' in config:
            config['max_recent_items'] = max(1, min(50, config['max_recent_items']))
            
        if 'max_workers' in config:
            config['max_workers'] = max(1, min(16, config['max_workers']))

        try:
            used = int(config.get('ai_service', {}).get('usage_used_calls', 0))
            config['ai_service']['usage_used_calls'] = max(0, used)
        except Exception:
            config['ai_service']['usage_used_calls'] = 0
            
        return config
        
    def get_setting(self, key: str, default: Any = None) -> Any:
        """获取单个设置项"""
        config = self.load_config()
        return config.get(key, default)
        
    def set_setting(self, key: str, value: Any) -> bool:
        """设置单个设置项"""
        config = self.load_config()
        config[key] = value
        return self.save_config(config)
        
    def get_nested_setting(self, *keys, default: Any = None) -> Any:
        """获取嵌套设置项"""
        config = self.load_config()
        current = config
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
                
        return current
        
    def set_nested_setting(self, *keys_and_value) -> bool:
        """设置嵌套设置项"""
        if len(keys_and_value) < 2:
            return False
            
        keys = keys_and_value[:-1]
        value = keys_and_value[-1]
        
        config = self.load_config()
        current = config
        
        # 导航到目标位置
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
            
        # 设置值
        current[keys[-1]] = value
        
        return self.save_config(config)
        
    def get_custom_rules(self) -> List[Dict[str, Any]]:
        """获取自定义规则"""
        return self.get_setting('custom_rules', [])
        
    def save_custom_rules(self, rules: List[Dict[str, Any]]) -> bool:
        """保存自定义规则"""
        return self.set_setting('custom_rules', rules)
        
    def add_custom_rule(self, rule: Dict[str, Any]) -> bool:
        """添加自定义规则"""
        rules = self.get_custom_rules()
        rules.append(rule)
        return self.save_custom_rules(rules)
        
    def remove_custom_rule(self, index: int) -> bool:
        """删除自定义规则"""
        rules = self.get_custom_rules()
        if 0 <= index < len(rules):
            rules.pop(index)
            return self.save_custom_rules(rules)
        return False
        
    def get_file_type_mapping(self) -> Dict[str, List[str]]:
        """获取文件类型映射"""
        return self.get_setting('file_type_mapping', {})
        
    def save_file_type_mapping(self, mapping: Dict[str, List[str]]) -> bool:
        """保存文件类型映射"""
        return self.set_setting('file_type_mapping', mapping)
        
    def add_recent_path(self, path: str, path_type: str) -> bool:
        """添加最近使用的路径"""
        if path_type not in ['source', 'target']:
            return False
            
        key = f'recent_{path_type}s'
        recent_paths = self.get_setting(key, [])
        
        # 移除重复项
        if path in recent_paths:
            recent_paths.remove(path)
            
        # 添加到开头
        recent_paths.insert(0, path)
        
        # 限制数量
        max_items = self.get_setting('max_recent_items', 10)
        recent_paths = recent_paths[:max_items]
        
        return self.set_setting(key, recent_paths)
        
    def get_recent_paths(self, path_type: str) -> List[str]:
        """获取最近使用的路径"""
        if path_type not in ['source', 'target']:
            return []
            
        key = f'recent_{path_type}s'
        return self.get_setting(key, [])
        
    def clear_recent_paths(self, path_type: str = None) -> bool:
        """清空最近使用的路径"""
        if path_type:
            if path_type not in ['source', 'target']:
                return False
            key = f'recent_{path_type}s'
            return self.set_setting(key, [])
        else:
            # 清空所有
            config = self.load_config()
            config['recent_sources'] = []
            config['recent_targets'] = []
            return self.save_config(config)
            
    def reset_to_default(self) -> bool:
        """重置为默认配置"""
        return self.save_config(self.default_config.copy())
        
    def export_config(self, export_path: str) -> bool:
        """导出配置到指定路径"""
        try:
            config = self.load_config()
            export_file = Path(export_path)
            
            # 确保目录存在
            export_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
            
    def import_config(self, import_path: str) -> bool:
        """从指定路径导入配置"""
        try:
            import_file = Path(import_path)
            
            if not import_file.exists():
                raise FileNotFoundError(f"配置文件不存在: {import_path}")
                
            with open(import_file, 'r', encoding='utf-8') as f:
                imported_config = json.load(f)
                
            # 合并导入的配置和默认配置
            merged_config = self._merge_configs(self.default_config, imported_config)
            
            return self.save_config(merged_config)
            
        except Exception as e:
            print(f"导入配置失败: {e}")
            return False
            
    def backup_config(self, backup_path: str = None) -> bool:
        """备份当前配置"""
        try:
            if backup_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = self.config_file.parent / f"config_backup_{timestamp}.json"
            
            return self.export_config(str(backup_path))
            
        except Exception as e:
            print(f"备份配置失败: {e}")
            return False
            
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置文件信息"""
        try:
            if self.config_file.exists():
                stat = self.config_file.stat()
                return {
                    'path': str(self.config_file),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'exists': True
                }
            else:
                return {
                    'path': str(self.config_file),
                    'exists': False
                }
                
        except Exception as e:
            return {
                'path': str(self.config_file),
                'error': str(e),
                'exists': False
            }
            
    def validate_paths(self) -> Dict[str, bool]:
        """验证配置中的路径"""
        config = self.load_config()
        results = {}
        
        # 验证源路径
        source_path = config.get('source_path', '')
        if source_path:
            results['source_path'] = Path(source_path).exists()
        else:
            results['source_path'] = None
            
        # 验证目标路径
        target_path = config.get('target_path', '')
        if target_path:
            target_p = Path(target_path)
            results['target_path'] = target_p.exists() or target_p.parent.exists()
        else:
            results['target_path'] = None
            
        # 验证最近使用的路径
        recent_sources = config.get('recent_sources', [])
        results['recent_sources'] = [Path(p).exists() for p in recent_sources]
        
        recent_targets = config.get('recent_targets', [])
        results['recent_targets'] = [Path(p).exists() for p in recent_targets]
        
        return results 