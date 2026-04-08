#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件分类器核心模块 - 内存优化版
File Classifier Core Module - Memory Optimized Version
"""

import os
import shutil
import json
import fnmatch
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import send2trash
from concurrent.futures import ThreadPoolExecutor, as_completed


class FileClassifier:
    """内存优化的文件分类器核心类"""
    
    __slots__ = ['operation_history', 'max_history', 'history_file', 'default_type_mapping', 
                 'hierarchical_classifier', 'use_hierarchical', 'ai_client', 'ai_filename_only',
                 'ai_usage_loaded']
    
    def __init__(self):
        self.operation_history = []
        self.max_history = 50
        self.history_file = Path.home() / '.file_classifier_history.json'
        self.ai_client = None
        self.ai_filename_only = True
        self.ai_usage_loaded = False
        
        self.hierarchical_classifier = None
        self.use_hierarchical = False
        
        self.default_type_mapping = {
            'images': ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.tif', 
                      '.svg', '.webp', '.ico', '.raw', '.heic', '.heif'),
            'documents': ('.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.pages',
                         '.md', '.tex', '.epub', '.mobi'),
            'spreadsheets': ('.xls', '.xlsx', '.csv', '.ods', '.numbers', '.tsv'),
            'presentations': ('.ppt', '.pptx', '.odp', '.key'),
            'audio': ('.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a',
                     '.opus', '.ape', '.ac3', '.dts'),
            'videos': ('.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm',
                      '.m4v', '.3gp', '.ogv', '.ts', '.vob'),
            'archives': ('.zip', '.rar', '.7z', '.tar', '.gz', '.bz2', '.xz',
                        '.cab', '.ace', '.arj', '.lzh'),
            'code': ('.py', '.js', '.html', '.css', '.java', '.cpp', '.c', '.h',
                    '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.ts', '.jsx',
                    '.vue', '.sql', '.sh', '.bat', '.ps1', '.xml', '.json', '.yaml'),
            'executables': ('.exe', '.msi', '.deb', '.rpm', '.dmg', '.app', '.pkg',
                           '.run', '.bin', '.jar'),
            'fonts': ('.ttf', '.otf', '.woff', '.woff2', '.eot'),
            'others': ()
        }
    
    def classify_files(self, source_path: str, target_path: str, 
                      rules: List[str], operation: str = 'move',
                      custom_rules: List[Dict] = None,
                      type_mapping: Dict[str, List[str]] = None) -> List[Dict]:
        """
        内存优化的批量分类方法
        
        Args:
            source_path: 源文件路径
            target_path: 目标路径
            rules: 分类规则列表
            operation: 操作类型 (move/copy/link)
            custom_rules: 自定义规则
            type_mapping: 文件类型映射
            
        Returns:
            分类结果列表
        """
        def file_generator(source: Path):
            if source.is_file():
                yield source
            elif source.is_dir():
                for f in source.rglob('*'):
                    if f.is_file():
                        yield f
        
        results = []
        current_operation = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'source_path': str(source_path),
            'target_path': str(target_path),
            'rules': rules,
            'files': []
        }
        
        try:
            source_path = Path(source_path)
            target_path = Path(target_path)
            target_path.mkdir(parents=True, exist_ok=True)
            
            type_map = type_mapping or self.default_type_mapping
            custom_rules = custom_rules or []
            
            for file_path in file_generator(source_path):
                result = self._classify_single_file(
                    file_path, target_path, rules, 
                    operation, custom_rules, type_map
                )
                if result:
                    results.append(result)
                    current_operation['files'].append(result)
            
            self.operation_history.append(current_operation)
            if len(self.operation_history) > self.max_history:
                self.operation_history.pop(0)
            
            self._save_history()
            
        except Exception as e:
            raise Exception(f"分类失败：{str(e)}")
        
        return results
    
    def _classify_single_file(self, file_path: Path, target_path: Path,
                             rules: List[str], operation: str,
                             custom_rules: List[Dict],
                             type_map: Dict[str, tuple]) -> Optional[Dict]:
        """分类单个文件"""
        try:
            category = self._determine_category(
                file_path, rules, custom_rules, type_map
            )
            
            if not category:
                return None
            
            dest_folder = target_path / category
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest_path = dest_folder / file_path.name
            
            if operation == 'move':
                send2trash.send2trash(str(file_path)) if self._use_recycle_bin() else file_path.unlink()
                shutil.move(str(dest_folder / file_path.name), str(dest_path)) if file_path.exists() else None
                shutil.move(str(file_path), str(dest_path))
            elif operation == 'copy':
                shutil.copy2(str(file_path), str(dest_path))
            elif operation == 'link':
                os.symlink(str(file_path), str(dest_path))
            
            return {
                'file': str(file_path),
                'destination': str(dest_path),
                'category': category,
                'operation': operation,
                'success': True,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'file': str(file_path),
                'error': str(e),
                'success': False,
                'timestamp': datetime.now().isoformat()
            }
    
    def _determine_category(self, file_path: Path, rules: List[str],
                           custom_rules: List[Dict],
                           type_map: Dict[str, tuple]) -> Optional[str]:
        """确定文件类别"""
        ext = file_path.suffix.lower()
        filename = file_path.name
        
        for rule in custom_rules:
            if rule.get('enabled', False):
                pattern = rule.get('pattern', '')
                if fnmatch.fnmatch(filename, pattern):
                    return rule.get('target_folder')
        
        if 'by_type' in rules:
            for category, extensions in type_map.items():
                if ext in extensions:
                    return category
        
        return 'others'
    
    def _use_recycle_bin(self) -> bool:
        """检查是否使用回收站"""
        return True
    
    def _save_history(self):
        """保存操作历史"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.operation_history, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
    
    def load_history(self) -> List[Dict]:
        """加载操作历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.operation_history = json.load(f)
            except Exception:
                self.operation_history = []
        return self.operation_history
    
    def undo_last_operation(self) -> bool:
        """撤销最后一次操作"""
        if not self.operation_history:
            return False
        
        last_op = self.operation_history.pop()
        self._save_history()
        
        for file_info in last_op.get('files', []):
            if file_info.get('success'):
                try:
                    src = Path(file_info['destination'])
                    original = Path(file_info['file'])
                    if src.exists():
                        original.parent.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(src), str(original))
                except Exception:
                    pass
        
        return True
