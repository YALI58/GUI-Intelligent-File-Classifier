#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强的多层级文件分类器
提供更精细、更智能的文件分类方案，解决文件查找困难问题
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
        # 精细化的文件类型映射
        self.detailed_type_mapping = {
            # 图片类型 - 按用途和格式细分
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
            
            # 文档类型 - 按用途和内容细分
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
            
            # 媒体文件 - 按内容和质量细分
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
            
            # 开发相关 - 按语言和项目类型细分
            'development': {
                'source_code': {
                    'web_frontend': ('.html', '.css', '.js', '.jsx', '.ts', '.tsx', '.vue', '.svelte'),
                    'web_backend': ('.php', '.py', '.rb', '.go', '.rs', '.java', '.kt'),
                    'mobile': ('.swift', '.m', '.java', '.kt', '.dart'),
                    'desktop': ('.cpp', '.c', '.h', '.cs', '.vb'),
                    'scripts': ('.sh', '.bat', '.ps1', '.fish', '.zsh'),
                    'data': ('.sql', '.json', '.xml', '.yaml', '.yml', '.toml')
                },
                'projects': {
                    'web_projects': ('package.json', 'yarn.lock', 'webpack.config.js'),
                    'mobile_apps': ('Podfile', 'build.gradle', 'pubspec.yaml'),
                    'desktop_apps': ('CMakeLists.txt', '.vcxproj', '.sln'),
                    'libraries': ('setup.py', 'Cargo.toml', 'composer.json')
                },
                'resources': {
                    'documentation': ('.md', '.rst', '.txt'),
                    'configs': ('.gitignore', '.dockerignore', '.env'),
                    'databases': ('.db', '.sqlite', '.sqlite3')
                }
            },
            
            # 系统和工具文件
            'system': {
                'executables': {
                    'installers': ('.msi', '.exe', '.dmg', '.pkg', '.deb', '.rpm'),
                    'portable': ('.exe', '.app'),
                    'scripts': ('.bat', '.sh', '.ps1')
                },
                'archives': {
                    'compressed': ('.zip', '.rar', '.7z', '.tar', '.gz'),
                    'disk_images': ('.iso', '.img', '.dmg'),
                    'backups': ('.bak', '.backup')
                },
                'fonts': ('.ttf', '.otf', '.woff', '.woff2', '.eot'),
                'drivers': ('.inf', '.sys', '.kext')
            }
        }
        
        # 文件名模式识别规则
        self.filename_patterns = {
            'screenshots': [
                r'screenshot.*',
                r'screen.*shot.*',
                r'capture.*',
                r'snap.*\d+',
                r'屏幕截图.*',
                r'截图.*',
                r'snipaste.*'
            ],
            'mobile_photos': [
                r'img_\d+',
                r'photo_\d+',
                r'dsc\d+',
                r'p\d{8}_\d+',
                r'wp_\d+',
                r'mmexport\d+',
                r'wechat.*'
            ],
            'logos': [
                r'.*logo.*',
                r'.*brand.*',
                r'.*icon.*',
                r'favicon.*'
            ],
            'reports': [
                r'.*report.*',
                r'.*分析.*',
                r'.*报告.*',
                r'.*汇报.*',
                r'.*总结.*',
                r'.*summary.*'
            ],
            'notes': [
                r'.*note.*',
                r'.*笔记.*',
                r'.*记录.*',
                r'.*备忘.*',
                r'memo.*',
                r'.*日记.*'
            ],
            'manuals': [
                r'.*manual.*',
                r'.*guide.*',
                r'.*handbook.*',
                r'.*说明.*',
                r'.*手册.*',
                r'.*指南.*'
            ],
            'tutorials': [
                r'.*tutorial.*',
                r'.*教程.*',
                r'.*学习.*',
                r'.*课程.*',
                r'how.*to.*'
            ],
            'tv_shows': [
                r'.*s\d+e\d+.*',
                r'.*第.*季.*集.*',
                r'.*ep\d+.*',
                r'.*episode.*'
            ],
            'movies': [
                r'.*\d{4}.*',  # 包含年份
                r'.*bluray.*',
                r'.*1080p.*',
                r'.*4k.*',
                r'.*电影.*'
            ],
            'backups': [
                r'.*backup.*',
                r'.*bak.*',
                r'.*备份.*',
                r'.*copy.*',
                r'.*副本.*',
                r'.*\(\d+\).*'  # 文件(1), 文件(2)等
            ],
            'temp_files': [
                r'^~.*',
                r'.*\.tmp$',
                r'.*\.temp$',
                r'temp.*',
                r'临时.*'
            ]
        }
        
        # 分类配置
        self.classification_config = {
            'max_files_per_folder': 50,
            'auto_create_subfolders': True,
            'date_granularity': 'month',  # year/quarter/month/week
            'enable_content_analysis': False,
            'enable_project_detection': True,
            'filename_pattern_recognition': True,
            'max_depth': 5,
            'min_files_for_subdivision': 20
        }
    
    def classify_file_hierarchical(self, file_path: Path, rules: List[str] = None, 
                                 max_depth: int = None) -> List[str]:
        """
        对文件进行多层级分类
        
        Args:
            file_path: 文件路径
            rules: 分类规则列表
            max_depth: 最大分类深度
            
        Returns:
            分类路径列表，如 ['documents', 'work', 'reports', '2024', 'Q1']
        """
        if rules is None:
            rules = ['by_type', 'by_pattern', 'by_date', 'by_usage']
        
        if max_depth is None:
            max_depth = self.classification_config['max_depth']
        
        classification_path = []
        
        # 第一层：基础类型分类
        if 'by_type' in rules and len(classification_path) < max_depth:
            primary_type = self._get_primary_type(file_path)
            classification_path.append(primary_type)
            
            # 第二层：细分类型
            if len(classification_path) < max_depth:
                secondary_type = self._get_secondary_type(file_path, primary_type)
                if secondary_type:
                    classification_path.append(secondary_type)
                    
                    # 第三层：更细致的分类
                    if len(classification_path) < max_depth:
                        tertiary_type = self._get_tertiary_type(file_path, primary_type, secondary_type)
                        if tertiary_type:
                            classification_path.append(tertiary_type)
        
        # 应用文件名模式识别
        if 'by_pattern' in rules and len(classification_path) < max_depth:
            pattern_type = self._classify_by_filename_pattern(file_path)
            if pattern_type and pattern_type not in classification_path:
                classification_path.append(pattern_type)
        
        # 应用项目结构检测
        if 'by_project' in rules and len(classification_path) < max_depth:
            project_path = self._detect_project_structure(file_path)
            if project_path:
                classification_path.extend(project_path.split('/'))
        
        # 应用时间分类
        if 'by_date' in rules and len(classification_path) < max_depth:
            date_parts = self._get_detailed_date_path(file_path)
            needed_parts = max_depth - len(classification_path)
            classification_path.extend(date_parts[:needed_parts])
        
        # 应用使用频率分类
        if 'by_usage' in rules and len(classification_path) < max_depth:
            usage_type = self._classify_by_usage(file_path)
            if usage_type and len(classification_path) < max_depth:
                classification_path.append(usage_type)
        
        return classification_path[:max_depth]
    
    def _get_primary_type(self, file_path: Path) -> str:
        """获取文件的主要类型"""
        extension = file_path.suffix.lower()
        
        # 遍历详细类型映射
        for primary_type, subtypes in self.detailed_type_mapping.items():
            if self._extension_in_subtypes(extension, subtypes):
                return primary_type
        
        # 根据MIME类型判断
        mime_type, _ = mimetypes.guess_type(str(file_path))
        if mime_type:
            if mime_type.startswith('image/'):
                return 'images'
            elif mime_type.startswith('video/'):
                return 'media'
            elif mime_type.startswith('audio/'):
                return 'media'
            elif mime_type.startswith('text/'):
                return 'documents'
            elif mime_type.startswith('application/'):
                if 'pdf' in mime_type:
                    return 'documents'
                elif any(x in mime_type for x in ['zip', 'tar', 'gzip', 'rar']):
                    return 'system'
        
        return 'others'
    
    def _get_secondary_type(self, file_path: Path, primary_type: str) -> Optional[str]:
        """获取文件的二级分类"""
        if primary_type not in self.detailed_type_mapping:
            return None
        
        extension = file_path.suffix.lower()
        filename = file_path.name.lower()
        
        subtypes = self.detailed_type_mapping[primary_type]
        
        # 先通过文件名模式识别
        pattern_match = self._classify_by_filename_pattern(file_path)
        if pattern_match:
            # 找到匹配的二级分类
            for subtype_name, subtype_data in subtypes.items():
                if isinstance(subtype_data, dict):
                    if pattern_match in subtype_data or any(pattern_match in k for k in subtype_data.keys()):
                        return subtype_name
                elif pattern_match in subtype_name:
                    return subtype_name
        
        # 通过扩展名匹配
        for subtype_name, subtype_data in subtypes.items():
            if isinstance(subtype_data, dict):
                if self._extension_in_subtypes(extension, subtype_data):
                    return subtype_name
            elif isinstance(subtype_data, tuple):
                if extension in subtype_data:
                    return subtype_name
        
        # 返回第一个可用的子类型
        return list(subtypes.keys())[0] if subtypes else None
    
    def _get_tertiary_type(self, file_path: Path, primary_type: str, secondary_type: str) -> Optional[str]:
        """获取文件的三级分类"""
        if primary_type not in self.detailed_type_mapping:
            return None
        
        subtypes = self.detailed_type_mapping[primary_type]
        if secondary_type not in subtypes:
            return None
        
        subtype_data = subtypes[secondary_type]
        if not isinstance(subtype_data, dict):
            return None
        
        extension = file_path.suffix.lower()
        filename = file_path.name.lower()
        
        # 通过文件名模式识别
        pattern_match = self._classify_by_filename_pattern(file_path)
        if pattern_match:
            for tertiary_name in subtype_data.keys():
                if pattern_match in tertiary_name or tertiary_name in pattern_match:
                    return tertiary_name
        
        # 通过扩展名匹配
        for tertiary_name, extensions in subtype_data.items():
            if isinstance(extensions, tuple) and extension in extensions:
                return tertiary_name
        
        # 基于文件大小的智能分类（针对媒体文件）
        if primary_type == 'media':
            return self._classify_media_by_size(file_path, secondary_type)
        
        return None
    
    def _extension_in_subtypes(self, extension: str, subtypes: Dict) -> bool:
        """检查扩展名是否在子类型中"""
        for subtype_data in subtypes.values():
            if isinstance(subtype_data, tuple):
                if extension in subtype_data:
                    return True
            elif isinstance(subtype_data, dict):
                if self._extension_in_subtypes(extension, subtype_data):
                    return True
        return False
    
    def _classify_by_filename_pattern(self, file_path: Path) -> Optional[str]:
        """基于文件名模式分类"""
        filename = file_path.name.lower()
        
        for category, patterns in self.filename_patterns.items():
            for pattern in patterns:
                if re.match(pattern, filename):
                    return category
        return None
    
    def _detect_project_structure(self, file_path: Path) -> Optional[str]:
        """检测是否在项目目录中"""
        if not self.classification_config['enable_project_detection']:
            return None
        
        parent_dirs = [p.name.lower() for p in file_path.parents[:5]]
        
        # Web项目识别
        if any(indicator in parent_dirs for indicator in ['src', 'public', 'node_modules']):
            project_root = self._find_project_root(file_path, ['package.json', 'yarn.lock'])
            if project_root:
                return f'projects/web/{project_root.name}'
        
        # Python项目识别
        elif any(indicator in parent_dirs for indicator in ['src', 'lib', '__pycache__']):
            project_root = self._find_project_root(file_path, ['requirements.txt', 'setup.py', 'pyproject.toml'])
            if project_root:
                return f'projects/python/{project_root.name}'
        
        # Java项目识别
        elif any(indicator in parent_dirs for indicator in ['src', 'target', 'build']):
            project_root = self._find_project_root(file_path, ['pom.xml', 'build.gradle'])
            if project_root:
                return f'projects/java/{project_root.name}'
        
        return None
    
    def _get_detailed_date_path(self, file_path: Path) -> List[str]:
        """获取详细的时间分类路径"""
        try:
            mtime = file_path.stat().st_mtime
            date = datetime.fromtimestamp(mtime)
            
            parts = []
            granularity = self.classification_config['date_granularity']
            
            # 年份
            parts.append(str(date.year))
            
            if granularity in ['quarter', 'month', 'week']:
                # 季度
                quarter = f"Q{(date.month - 1) // 3 + 1}"
                parts.append(quarter)
            
            if granularity in ['month', 'week']:
                # 月份
                month = f"{date.month:02d}-{date.strftime('%B')}"
                parts.append(month)
            
            if granularity == 'week':
                # 周
                week = f"Week{date.isocalendar()[1]:02d}"
                parts.append(week)
            
            return parts
            
        except Exception:
            return ['unknown_date']
    
    def _classify_by_usage(self, file_path: Path) -> Optional[str]:
        """基于使用频率和最近访问时间分类"""
        try:
            stat = file_path.stat()
            access_time = stat.st_atime
            current_time = datetime.now().timestamp()
            
            days_since_access = (current_time - access_time) / (24 * 3600)
            
            if days_since_access < 7:
                return 'recent'
            elif days_since_access < 30:
                return 'this_month'
            elif days_since_access < 365:
                return 'this_year'
            else:
                return 'archive'
                
        except Exception:
            return None
    
    def _classify_media_by_size(self, file_path: Path, media_type: str) -> Optional[str]:
        """基于大小对媒体文件进行分类"""
        try:
            size = file_path.stat().st_size
            
            if media_type == 'videos':
                if size > 1 * 1024 * 1024 * 1024:  # >1GB
                    return 'movies'
                elif size > 100 * 1024 * 1024:  # >100MB
                    return 'long_videos'
                else:
                    return 'clips'
            elif media_type == 'audio':
                if size > 50 * 1024 * 1024:  # >50MB
                    return 'albums'
                elif size > 10 * 1024 * 1024:  # >10MB
                    return 'long_tracks'
                else:
                    return 'singles'
            
        except Exception:
            pass
        
        return None
    
    def _find_project_root(self, file_path: Path, indicators: List[str]) -> Optional[Path]:
        """查找项目根目录"""
        current = file_path.parent
        while current != current.parent:  # 直到根目录
            for indicator in indicators:
                if (current / indicator).exists():
                    return current
            current = current.parent
        return None
    
    def calculate_optimal_depth(self, file_count: int, file_type: str = None) -> int:
        """根据文件数量计算最优分类深度"""
        if file_count < self.classification_config['min_files_for_subdivision']:
            return 2  # 简单分类：类型/其他
        elif file_count < 100:
            return 3  # 中等分类：类型/子类型/时间
        elif file_count < 500:
            return 4  # 详细分类：类型/子类型/时间/用途
        else:
            return self.classification_config['max_depth']  # 最详细分类
    
    def get_classification_suggestions(self, file_path: Path, 
                                     max_suggestions: int = 5) -> List[Dict[str, Any]]:
        """获取多个分类建议"""
        suggestions = []
        
        # 基础分类
        basic_path = self.classify_file_hierarchical(file_path, ['by_type'], max_depth=3)
        suggestions.append({
            'path': basic_path,
            'path_str': '/'.join(basic_path),
            'confidence': 0.9,
            'reason': '基于文件类型的标准分类',
            'type': 'basic'
        })
        
        # 模式识别分类
        pattern_path = self.classify_file_hierarchical(file_path, ['by_type', 'by_pattern'], max_depth=4)
        if pattern_path != basic_path:
            suggestions.append({
                'path': pattern_path,
                'path_str': '/'.join(pattern_path),
                'confidence': 0.8,
                'reason': '基于文件名模式的分类',
                'type': 'pattern'
            })
        
        # 项目导向分类
        project_path = self.classify_file_hierarchical(file_path, ['by_type', 'by_project'], max_depth=4)
        if project_path not in [basic_path, pattern_path]:
            suggestions.append({
                'path': project_path,
                'path_str': '/'.join(project_path),
                'confidence': 0.7,
                'reason': '基于项目结构的分类',
                'type': 'project'
            })
        
        # 时间导向分类
        date_path = self.classify_file_hierarchical(file_path, ['by_type', 'by_date'], max_depth=5)
        if date_path not in [s['path'] for s in suggestions]:
            suggestions.append({
                'path': date_path,
                'path_str': '/'.join(date_path),
                'confidence': 0.6,
                'reason': '基于时间的详细分类',
                'type': 'temporal'
            })
        
        # 使用频率分类
        usage_path = self.classify_file_hierarchical(file_path, ['by_type', 'by_usage'], max_depth=4)
        if usage_path not in [s['path'] for s in suggestions]:
            suggestions.append({
                'path': usage_path,
                'path_str': '/'.join(usage_path),
                'confidence': 0.5,
                'reason': '基于使用频率的分类',
                'type': 'usage'
            })
        
        return suggestions[:max_suggestions]
    
    def analyze_directory_structure(self, directory_path: Path) -> Dict[str, Any]:
        """分析目录结构，提供优化建议"""
        analysis = {
            'total_files': 0,
            'type_distribution': defaultdict(int),
            'depth_analysis': defaultdict(int),
            'large_directories': [],
            'optimization_suggestions': [],
            'recommended_depth': 3
        }
        
        if not directory_path.exists():
            return analysis
        
        file_count_by_type = defaultdict(int)
        
        # 分析所有文件
        for file_path in directory_path.rglob('*'):
            if file_path.is_file():
                analysis['total_files'] += 1
                
                # 类型分布
                primary_type = self._get_primary_type(file_path)
                analysis['type_distribution'][primary_type] += 1
                file_count_by_type[primary_type] += 1
                
                # 深度分析
                depth = len(file_path.relative_to(directory_path).parts) - 1
                analysis['depth_analysis'][depth] += 1
        
        # 找出大目录
        for item in directory_path.iterdir():
            if item.is_dir():
                file_count = sum(1 for _ in item.rglob('*') if _.is_file())
                if file_count > self.classification_config['max_files_per_folder']:
                    analysis['large_directories'].append({
                        'path': item.name,
                        'file_count': file_count
                    })
        
        # 计算推荐的分类深度
        max_type_count = max(file_count_by_type.values()) if file_count_by_type else 0
        analysis['recommended_depth'] = self.calculate_optimal_depth(max_type_count)
        
        # 生成优化建议
        self._generate_optimization_suggestions(analysis)
        
        return analysis
    
    def _generate_optimization_suggestions(self, analysis: Dict[str, Any]):
        """生成优化建议"""
        suggestions = analysis['optimization_suggestions']
        
        # 文件数量过多的建议
        if analysis['total_files'] > 1000:
            suggestions.append({
                'type': 'high_volume',
                'message': f'检测到{analysis["total_files"]}个文件，建议启用{analysis["recommended_depth"]}层分类',
                'priority': 'high',
                'recommended_depth': analysis['recommended_depth']
            })
        
        # 深度问题的建议
        max_depth = max(analysis['depth_analysis'].keys()) if analysis['depth_analysis'] else 0
        if max_depth > 6:
            suggestions.append({
                'type': 'deep_nesting',
                'message': f'文件夹嵌套深度达到{max_depth}层，建议重新组织结构',
                'priority': 'medium'
            })
        elif max_depth < 2:
            suggestions.append({
                'type': 'shallow_structure',
                'message': f'文件夹结构过于扁平，建议增加分类层次',
                'priority': 'low'
            })
        
        # 类型分布不均的建议
        type_counts = list(analysis['type_distribution'].values())
        if type_counts and max(type_counts) > sum(type_counts) * 0.7:
            dominant_type = max(analysis['type_distribution'], key=analysis['type_distribution'].get)
            suggestions.append({
                'type': 'type_imbalance',
                'message': f'{dominant_type}类型文件占比过高({analysis["type_distribution"][dominant_type]}个)，建议进一步细分',
                'priority': 'medium',
                'dominant_type': dominant_type
            })
        
        # 大目录的建议
        for large_dir in analysis['large_directories']:
            suggestions.append({
                'type': 'large_directory',
                'message': f'目录"{large_dir["path"]}"包含{large_dir["file_count"]}个文件，建议细分',
                'priority': 'high',
                'directory': large_dir["path"],
                'file_count': large_dir["file_count"]
            })
    
    def update_config(self, config: Dict[str, Any]):
        """更新分类配置"""
        self.classification_config.update(config)
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return self.classification_config.copy() 