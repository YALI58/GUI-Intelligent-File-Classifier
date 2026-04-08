#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版文件分类器 - 支持文件关联检测
Enhanced File Classifier - Support for File Association Detection
"""

import os
import shutil
import json
import fnmatch
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Set, Tuple
import send2trash


class EnhancedFileClassifier:
    """增强版文件分类器 - 支持文件关联检测"""
    
    def __init__(self):
        self.operation_history = []
        self.max_history = 50
        self.history_file = Path.home() / '.file_classifier_history.json'
        self.ai_client = None
        self.ai_filename_only = True
        
        self.flag_file_name = '.noclassify'
        self.respect_flag_file = True
        
        self.association_rules = {
            'program_files': {
                'main_extensions': ['.exe', '.app', '.jar'],
                'related_extensions': ['.dll', '.so', '.dylib', '.lib', '.ini', '.cfg', '.config'],
                'keep_together': True,
                'folder_name': 'executables'
            },
            'project_files': {
                'indicators': ['package.json', 'requirements.txt', 'pom.xml', 'Cargo.toml', 
                              'go.mod', 'composer.json', '.gitignore', 'README.md'],
                'code_extensions': ['.py', '.js', '.java', '.go', '.rs', '.php', '.c', '.cpp'],
                'config_extensions': ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'],
                'keep_together': True,
                'folder_name': 'projects'
            },
            'web_files': {
                'main_extensions': ['.html', '.htm'],
                'related_extensions': ['.css', '.js', '.png', '.jpg', '.gif', '.svg'],
                'keep_together': True,
                'folder_name': 'web_projects'
            },
            'media_collections': {
                'main_extensions': ['.mp4', '.avi', '.mkv'],
                'related_extensions': ['.srt', '.ass', '.vtt', '.nfo', '.jpg'],
                'keep_together': True,
                'folder_name': 'videos'
            },
            'document_sets': {
                'main_extensions': ['.pdf', '.docx'],
                'related_extensions': ['.txt', '.md', '.rtf'],
                'same_name_pattern': True,
                'keep_together': True,
                'folder_name': 'documents'
            }
        }
        
        self.default_type_mapping = {
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
        }
        
        self._load_history()
    
    def classify_files(self, source_path: str, target_path: str,
                      rules: List[str], operation: str = 'move',
                      custom_rules: List[Dict] = None,
                      type_mapping: Dict[str, List[str]] = None) -> List[Dict]:
        """
        增强版文件分类 - 考虑文件关联性
        
        Args:
            source_path: 源路径
            target_path: 目标路径
            rules: 分类规则
            operation: 操作类型
            custom_rules: 自定义规则
            type_mapping: 类型映射
            
        Returns:
            分类结果列表
        """
        source = Path(source_path)
        target = Path(target_path)
        target.mkdir(parents=True, exist_ok=True)
        
        results = []
        type_map = type_mapping or self.default_type_mapping
        
        files_to_process = list(source.rglob('*')) if source.is_dir() else [source]
        files_to_process = [f for f in files_to_process if f.is_file()]
        
        associated_groups = self._find_associated_files(files_to_process)
        processed_files: Set[str] = set()
        
        for group in associated_groups:
            group_results = self._process_file_group(
                group, target, rules, operation, custom_rules, type_map
            )
            results.extend(group_results)
            processed_files.update(str(f) for f in group)
        
        remaining_files = [f for f in files_to_process if str(f) not in processed_files]
        for file_path in remaining_files:
            result = self._classify_single_file(
                file_path, target, rules, operation, custom_rules, type_map
            )
            if result:
                results.append(result)
        
        self._save_history()
        return results
    
    def _find_associated_files(self, files: List[Path]) -> List[Set[Path]]:
        """查找关联文件组"""
        groups = []
        processed = set()
        
        for file_path in files:
            if str(file_path) in processed:
                continue
            
            group = self._find_related_files(file_path, files)
            if len(group) > 1:
                groups.append(group)
                processed.update(str(f) for f in group)
        
        return groups
    
    def _find_related_files(self, file_path: Path, all_files: List[Path]) -> Set[Path]:
        """查找与指定文件相关的文件"""
        related = {file_path}
        stem = file_path.stem
        parent = file_path.parent
        
        for other_file in all_files:
            if other_file == file_path:
                continue
            
            if other_file.stem == stem and other_file.parent == parent:
                related.add(other_file)
            
            for rule in self.association_rules.values():
                if rule.get('keep_together'):
                    main_exts = rule.get('main_extensions', [])
                    related_exts = rule.get('related_extensions', [])
                    
                    if (file_path.suffix.lower() in main_exts and 
                        other_file.suffix.lower() in related_exts and
                        other_file.stem.startswith(stem)):
                        related.add(other_file)
                    elif (file_path.suffix.lower() in related_exts and 
                          other_file.suffix.lower() in main_exts and
                          file_path.stem.startswith(other_file.stem)):
                        related.add(other_file)
        
        return related
    
    def _process_file_group(self, group: Set[Path], target_path: Path,
                           rules: List[str], operation: str,
                           custom_rules: List[Dict],
                           type_map: Dict[str, List[str]]) -> List[Dict]:
        """处理关联文件组"""
        results = []
        
        primary_file = max(group, key=lambda f: len(f.suffix))
        category = self._determine_category(primary_file, rules, custom_rules, type_map)
        
        if not category:
            category = 'others'
        
        dest_folder = target_path / category
        dest_folder.mkdir(parents=True, exist_ok=True)
        
        for file_path in group:
            try:
                dest_path = dest_folder / file_path.name
                
                if operation == 'move':
                    if self._should_use_recycle_bin():
                        try:
                            send2trash.send2trash(str(file_path))
                        except Exception:
                            file_path.unlink()
                    else:
                        file_path.unlink()
                    shutil.move(str(file_path), str(dest_path))
                elif operation == 'copy':
                    shutil.copy2(str(file_path), str(dest_path))
                
                results.append({
                    'file': str(file_path),
                    'destination': str(dest_path),
                    'category': category,
                    'operation': operation,
                    'success': True,
                    'timestamp': datetime.now().isoformat(),
                    'is_associated': len(group) > 1
                })
            except Exception as e:
                results.append({
                    'file': str(file_path),
                    'error': str(e),
                    'success': False,
                    'timestamp': datetime.now().isoformat()
                })
        
        return results
    
    def _classify_single_file(self, file_path: Path, target_path: Path,
                             rules: List[str], operation: str,
                             custom_rules: List[Dict],
                             type_map: Dict[str, List[str]]) -> Optional[Dict]:
        """分类单个文件"""
        try:
            category = self._determine_category(file_path, rules, custom_rules, type_map)
            if not category:
                category = 'others'
            
            dest_folder = target_path / category
            dest_folder.mkdir(parents=True, exist_ok=True)
            dest_path = dest_folder / file_path.name
            
            if operation == 'move':
                if self._should_use_recycle_bin():
                    try:
                        send2trash.send2trash(str(file_path))
                    except Exception:
                        file_path.unlink()
                else:
                    file_path.unlink()
                shutil.move(str(file_path), str(dest_path))
            elif operation == 'copy':
                shutil.copy2(str(file_path), str(dest_path))
            
            return {
                'file': str(file_path),
                'destination': str(dest_path),
                'category': category,
                'operation': operation,
                'success': True,
                'timestamp': datetime.now().isoformat(),
                'is_associated': False
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
                           type_map: Dict[str, List[str]]) -> Optional[str]:
        """确定文件类别"""
        ext = file_path.suffix.lower()
        filename = file_path.name
        
        for rule in custom_rules or []:
            if rule.get('enabled', False):
                pattern = rule.get('pattern', '')
                if fnmatch.fnmatch(filename, pattern):
                    return rule.get('target_folder')
        
        if 'by_type' in rules:
            for category, extensions in type_map.items():
                if ext in extensions:
                    return category
        
        return 'others'
    
    def _should_use_recycle_bin(self) -> bool:
        """检查是否使用回收站"""
        return True
    
    def _load_history(self):
        """加载操作历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.operation_history = json.load(f)
            except Exception:
                self.operation_history = []
    
    def _save_history(self):
        """保存操作历史"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.operation_history[-self.max_history:], f, 
                         ensure_ascii=False, indent=2)
        except Exception:
            pass
