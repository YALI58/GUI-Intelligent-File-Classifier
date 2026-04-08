#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多层级文件分类器 - 精细化分类
Hierarchical File Classifier - Fine-grained Classification
"""

import os
import re
import mimetypes
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from collections import defaultdict
import fnmatch


class HierarchicalFileClassifier:
    """多层级文件分类器"""
    
    def __init__(self):
        self.detailed_type_mapping = {
            'images': {
                'photos': {
                    'mobile_photos': ('.jpg', '.jpeg', '.png', '.heic', '.heif'),
                    'raw_photos': ('.cr2', '.nef', '.arw', '.dng', '.raw'),
                    'high_quality': ('.tiff', '.tif', '.png'),
                    'web_optimized': ('.webp', '.svg'),
                },
                'graphics': {
                    'screenshots': ('.jpg', '.jpeg', '.png', '.bmp'),
                    'icons': ('.ico', '.icns', '.png'),
                    'logos': ('.svg', '.png', '.jpg', '.ai'),
                    'illustrations': ('.svg', '.ai', '.eps', '.pdf'),
                },
                'design': {
                    'mockups': ('.psd', '.sketch', '.fig', '.xd'),
                    'prototypes': ('.png', '.jpg', '.pdf'),
                    'assets': ('.png', '.svg', '.jpg'),
                },
                'animations': ('.gif', '.apng', '.webp'),
                'others': ('.bmp', '.tga', '.exr')
            },
            'documents': {
                'work': {
                    'reports': ('.pdf', '.doc', '.docx', '.ppt', '.pptx'),
                    'contracts': ('.pdf', '.doc', '.docx'),
                    'presentations': ('.ppt', '.pptx', '.odp', '.key'),
                    'spreadsheets': ('.xls', '.xlsx', '.csv', '.ods', '.numbers'),
                },
                'personal': {
                    'notes': ('.txt', '.md', '.rtf', '.odt'),
                    'diaries': ('.txt', '.doc', '.docx'),
                    'lists': ('.txt', '.md', '.csv'),
                },
                'reference': {
                    'manuals': ('.pdf', '.doc', '.docx'),
                    'guides': ('.pdf', '.txt', '.md'),
                    'documentation': ('.pdf', '.txt', '.md', '.rst'),
                },
                'technical': {
                    'logs': ('.log', '.out', '.txt'),
                    'configs': ('.ini', '.conf', '.cfg', '.toml', '.yaml', '.yml'),
                    'data': ('.json', '.xml', '.csv', '.tsv'),
                },
                'ebooks': ('.epub', '.mobi', '.azw', '.fb2', '.pdf'),
                'others': ('.pages', '.tex')
            },
            'media': {
                'audio': {
                    'music': {
                        'lossless': ('.flac', '.ape', '.wav', '.aiff'),
                        'compressed': ('.mp3', '.aac', '.ogg', '.wma', '.m4a'),
                        'streaming': ('.opus', '.webm')
                    },
                    'podcasts': ('.mp3', '.aac', '.ogg'),
                    'recordings': ('.wav', '.m4a', '.aac'),
                    'soundeffects': ('.wav', '.aiff', '.ogg')
                },
                'videos': {
                    'movies': ('.mkv', '.mp4', '.avi', '.mov'),
                    'tv_shows': ('.mkv', '.mp4', '.avi'),
                    'personal': ('.mp4', '.mov', '.avi'),
                    'tutorials': ('.mp4', '.mkv', '.webm'),
                    'clips': ('.mp4', '.mov', '.webm', '.gif'),
                    'streams': ('.flv', '.webm', '.ts')
                }
            },
            'development': {
                'source_code': {
                    'web_frontend': ('.html', '.css', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte'),
                    'web_backend': ('.php', '.py', '.rb', '.go', '.rs', '.java', '.kt'),
                    'mobile': ('.swift', '.m', '.java', '.kt', '.dart'),
                    'desktop': ('.cpp', '.c', '.h', '.cs', '.vb'),
                    'scripts': ('.sh', '.bat', '.ps1', '.py', '.rb', '.pl'),
                },
                'config': {
                    'project': ('.json', '.yaml', '.yml', '.toml', '.xml'),
                    'environment': ('.env', '.ini', '.conf', '.cfg'),
                },
                'database': ('.sql', '.db', '.sqlite', '.mdb'),
                'documentation': ('.md', '.rst', '.txt')
            }
        }
        
        self.config = {
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
    
    def classify(self, files: List[Path], target_path: Path) -> Dict[str, List[Path]]:
        """
        多层级分类
        
        Args:
            files: 待分类文件列表
            target_path: 目标路径
            
        Returns:
            分类结果字典 {category_path: [files]}
        """
        results = defaultdict(list)
        
        for file_path in files:
            category_path = self._determine_hierarchical_category(file_path)
            dest_path = target_path / category_path / file_path.name
            results[str(dest_path)].append(file_path)
        
        return dict(results)
    
    def _determine_hierarchical_category(self, file_path: Path) -> str:
        """确定文件的多层级分类路径"""
        ext = file_path.suffix.lower()
        filename = file_path.name
        stem = file_path.stem
        
        categories = []
        
        primary_category = self._find_primary_category(ext)
        if primary_category:
            categories.append(primary_category[0])
            
            sub_category = self._find_sub_category(ext, primary_category[1])
            if sub_category:
                categories.append(sub_category)
                
                detail_category = self._find_detail_category(
                    ext, filename, primary_category[1], sub_category
                )
                if detail_category:
                    categories.append(detail_category)
        
        if not categories:
            return 'others'
        
        return '/'.join(categories)
    
    def _find_primary_category(self, ext: str) -> Optional[Tuple[str, Dict]]:
        """查找主类别"""
        for category, subcategories in self.detailed_type_mapping.items():
            if isinstance(subcategories, dict):
                for sub_name, sub_items in subcategories.items():
                    if isinstance(sub_items, tuple) and ext in sub_items:
                        return (category, subcategories)
                    elif isinstance(sub_items, dict):
                        for detail_name, detail_items in sub_items.items():
                            if isinstance(detail_items, tuple) and ext in detail_items:
                                return (category, subcategories)
        return None
    
    def _find_sub_category(self, ext: str, parent: Dict) -> Optional[str]:
        """查找子类别"""
        for name, items in parent.items():
            if isinstance(items, tuple) and ext in items:
                return name
            elif isinstance(items, dict):
                for detail_items in items.values():
                    if isinstance(detail_items, tuple) and ext in detail_items:
                        return name
        return None
    
    def _find_detail_category(self, ext: str, filename: str, 
                             parent: Dict, sub_category: str) -> Optional[str]:
        """查找详细类别"""
        sub_items = parent.get(sub_category, {})
        if isinstance(sub_items, dict):
            for name, items in sub_items.items():
                if isinstance(items, tuple) and ext in items:
                    if self.config['filename_pattern_recognition']:
                        refined = self._refine_by_filename(name, filename)
                        return refined or name
                    return name
        elif isinstance(sub_items, tuple) and ext in sub_items:
            return sub_category
        return None
    
    def _refine_by_filename(self, category: str, filename: str) -> Optional[str]:
        """根据文件名细化分类"""
        filename_lower = filename.lower()
        
        patterns = {
            'screenshot': ['screenshot', '截图', 'screen', 'capture'],
            'logo': ['logo', '图标', 'icon'],
            'report': ['report', '报告', 'summary', '总结'],
            'backup': ['backup', '备份', 'bak', 'old'],
            'temp': ['temp', 'tmp', '临时'],
        }
        
        for pattern_name, keywords in patterns.items():
            if any(keyword in filename_lower for keyword in keywords):
                return f"{category}_{pattern_name}"
        
        return category
    
    def set_config(self, **kwargs):
        """设置配置参数"""
        self.config.update(kwargs)
    
    def get_config(self) -> Dict[str, Any]:
        """获取配置参数"""
        return self.config.copy()
