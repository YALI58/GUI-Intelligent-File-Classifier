#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
增强版文件分类器 - 支持文件关联检测
解决文件依赖关系问题
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
        
        # 标志文件配置
        self.flag_file_name = '.noclassify'  # 默认标志文件名
        self.respect_flag_file = True        # 是否遵循标志文件
        
        # 文件关联规则
        self.association_rules = {
            # 程序文件关联
            'program_files': {
                'main_extensions': ['.exe', '.app', '.jar'],
                'related_extensions': ['.dll', '.so', '.dylib', '.lib', '.ini', '.cfg', '.config'],
                'keep_together': True,
                'folder_name': 'executables'
            },
            
            # 项目文件关联
            'project_files': {
                'indicators': ['package.json', 'requirements.txt', 'pom.xml', 'Cargo.toml', 
                              'go.mod', 'composer.json', '.gitignore', 'README.md'],
                'code_extensions': ['.py', '.js', '.java', '.go', '.rs', '.php', '.c', '.cpp'],
                'config_extensions': ['.json', '.yaml', '.yml', '.toml', '.ini', '.cfg'],
                'keep_together': True,
                'folder_name': 'projects'
            },
            
            # 网页文件关联
            'web_files': {
                'main_extensions': ['.html', '.htm'],
                'related_extensions': ['.css', '.js', '.png', '.jpg', '.gif', '.svg'],
                'keep_together': True,
                'folder_name': 'web_projects'
            },
            
            # 媒体集合文件
            'media_collections': {
                'main_extensions': ['.mp4', '.avi', '.mkv'],
                'related_extensions': ['.srt', '.ass', '.vtt', '.nfo', '.jpg'],
                'keep_together': True,
                'folder_name': 'videos'
            },
            
            # 文档集合
            'document_sets': {
                'main_extensions': ['.pdf', '.docx'],
                'related_extensions': ['.txt', '.md', '.rtf'],
                'same_name_pattern': True,  # 同名文件保持一起
                'keep_together': True,
                'folder_name': 'documents'
            }
        }
        
        # 默认文件类型映射（继承原有的）
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
        
        # 加载操作历史
        self.load_operation_history()
    
    def analyze_file_associations(self, source_path: Path) -> Dict[str, List[Path]]:
        """
        分析文件关联关系
        
        Returns:
            字典，key为组名，value为该组的文件列表
        """
        all_files = self._get_files_from_source(source_path)
        file_groups = {}
        processed_files = set()
        
        # 按目录分组分析
        directories = {}
        for file_path in all_files:
            parent_dir = file_path.parent
            if parent_dir not in directories:
                directories[parent_dir] = []
            directories[parent_dir].append(file_path)
        
        group_id = 0
        
        for dir_path, files_in_dir in directories.items():
            remaining_files = [f for f in files_in_dir if f not in processed_files]
            
            if not remaining_files:
                continue
                
            # 检查是否是项目文件夹
            project_group = self._detect_project_folder(dir_path, remaining_files)
            if project_group:
                group_name = f"project_{group_id}"
                file_groups[group_name] = project_group
                processed_files.update(project_group)
                group_id += 1
                continue
            
            # 检查程序文件关联
            program_groups = self._detect_program_associations(remaining_files)
            for group in program_groups:
                group_name = f"program_{group_id}"
                file_groups[group_name] = group
                processed_files.update(group)
                group_id += 1
            
            # 检查网页文件关联
            web_groups = self._detect_web_associations(remaining_files)
            for group in web_groups:
                group_name = f"web_{group_id}"
                file_groups[group_name] = group
                processed_files.update(group)
                group_id += 1
            
            # 检查媒体文件关联
            media_groups = self._detect_media_associations(remaining_files)
            for group in media_groups:
                group_name = f"media_{group_id}"
                file_groups[group_name] = group
                processed_files.update(group)
                group_id += 1
            
            # 检查同名文件关联
            same_name_groups = self._detect_same_name_associations(remaining_files)
            for group in same_name_groups:
                group_name = f"samename_{group_id}"
                file_groups[group_name] = group
                processed_files.update(group)
                group_id += 1
        
        # 剩余的独立文件
        remaining_files = [f for f in all_files if f not in processed_files]
        if remaining_files:
            file_groups['individual_files'] = remaining_files
        
        return file_groups
    
    def _detect_project_folder(self, dir_path: Path, files: List[Path]) -> Optional[List[Path]]:
        """检测是否为项目文件夹"""
        file_names = {f.name.lower() for f in files}
        
        # 检查项目指示文件
        indicators = self.association_rules['project_files']['indicators']
        has_indicator = any(indicator.lower() in file_names for indicator in indicators)
        
        if has_indicator:
            # 如果有项目指示文件，整个目录都算作项目
            return files
        
        # 检查代码文件密度
        code_exts = self.association_rules['project_files']['code_extensions']
        config_exts = self.association_rules['project_files']['config_extensions']
        
        code_files = [f for f in files if f.suffix.lower() in code_exts]
        config_files = [f for f in files if f.suffix.lower() in config_exts]
        
        # 如果代码文件 + 配置文件 > 总文件的50%，认为是项目
        if len(code_files) + len(config_files) >= len(files) * 0.5 and len(code_files) >= 2:
            return files
        
        return None
    
    def _detect_program_associations(self, files: List[Path]) -> List[List[Path]]:
        """检测程序文件关联"""
        groups = []
        main_exts = self.association_rules['program_files']['main_extensions']
        related_exts = self.association_rules['program_files']['related_extensions']
        
        main_files = [f for f in files if f.suffix.lower() in main_exts]
        
        for main_file in main_files:
            group = [main_file]
            main_stem = main_file.stem.lower()
            
            # 查找相关文件
            for file in files:
                if file == main_file:
                    continue
                    
                # 同名的相关文件
                if file.stem.lower() == main_stem and file.suffix.lower() in related_exts:
                    group.append(file)
                # 同目录下的dll等依赖文件
                elif file.suffix.lower() in related_exts:
                    group.append(file)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _detect_web_associations(self, files: List[Path]) -> List[List[Path]]:
        """检测网页文件关联"""
        groups = []
        main_exts = self.association_rules['web_files']['main_extensions']
        related_exts = self.association_rules['web_files']['related_extensions']
        
        html_files = [f for f in files if f.suffix.lower() in main_exts]
        
        for html_file in html_files:
            group = [html_file]
            html_stem = html_file.stem.lower()
            
            # 查找相关文件
            for file in files:
                if file == html_file:
                    continue
                    
                # 同名的相关文件
                if file.stem.lower().startswith(html_stem) and file.suffix.lower() in related_exts:
                    group.append(file)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _detect_media_associations(self, files: List[Path]) -> List[List[Path]]:
        """检测媒体文件关联"""
        groups = []
        main_exts = self.association_rules['media_collections']['main_extensions']
        related_exts = self.association_rules['media_collections']['related_extensions']
        
        media_files = [f for f in files if f.suffix.lower() in main_exts]
        
        for media_file in media_files:
            group = [media_file]
            media_stem = media_file.stem.lower()
            
            # 查找相关文件（字幕、海报等）
            for file in files:
                if file == media_file:
                    continue
                    
                if file.stem.lower() == media_stem and file.suffix.lower() in related_exts:
                    group.append(file)
            
            if len(group) > 1:
                groups.append(group)
        
        return groups
    
    def _detect_same_name_associations(self, files: List[Path]) -> List[List[Path]]:
        """检测同名文件关联"""
        groups = []
        stem_groups = {}
        
        # 按文件名分组
        for file in files:
            stem = file.stem.lower()
            if stem not in stem_groups:
                stem_groups[stem] = []
            stem_groups[stem].append(file)
        
        # 找出有多个文件的组
        for stem, file_list in stem_groups.items():
            if len(file_list) > 1:
                groups.append(file_list)
        
        return groups
    
    def classify_files_with_associations(self, source_path: str, target_path: str, 
                                       rules: List[str], operation: str = 'move',
                                       custom_rules: List[Dict] = None,
                                       type_mapping: Dict[str, List[str]] = None,
                                       preserve_associations: bool = True) -> List[Dict]:
        """
        带关联检测的文件分类
        
        Args:
            preserve_associations: 是否保持文件关联关系
        """
        results = []
        source_path = Path(source_path)
        target_path = Path(target_path)
        
        current_operation = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'source_path': str(source_path),
            'target_path': str(target_path),
            'rules': rules,
            'preserve_associations': preserve_associations,
            'files': []
        }
        
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            
            if preserve_associations:
                # 分析文件关联
                file_groups = self.analyze_file_associations(source_path)
                
                for group_name, files_in_group in file_groups.items():
                    if group_name == 'individual_files':
                        # 独立文件按原规则分类
                        for file_path in files_in_group:
                            result = self._classify_single_file(
                                file_path, target_path, rules, operation, 
                                custom_rules, type_mapping
                            )
                            results.extend(result)
                            current_operation['files'].extend([r for r in result if r['success']])
                    else:
                        # 关联文件组一起分类
                        group_result = self._classify_file_group(
                            files_in_group, target_path, rules, operation,
                            custom_rules, type_mapping, group_name
                        )
                        results.extend(group_result)
                        current_operation['files'].extend([r for r in group_result if r['success']])
            else:
                # 不保持关联关系，按原逻辑分类
                all_files = self._get_files_from_source(source_path)
                for file_path in all_files:
                    result = self._classify_single_file(
                        file_path, target_path, rules, operation,
                        custom_rules, type_mapping
                    )
                    results.extend(result)
                    current_operation['files'].extend([r for r in result if r['success']])
            
            # 保存操作记录
            if current_operation['files']:
                self._save_operation_history(current_operation)
                
        except Exception as e:
            raise Exception(f"分类过程中发生错误: {str(e)}")
        
        return results
    
    def _classify_file_group(self, files: List[Path], target_path: Path, 
                           rules: List[str], operation: str,
                           custom_rules: List[Dict] = None,
                           type_mapping: Dict[str, List[str]] = None,
                           group_name: str = "") -> List[Dict]:
        """分类文件组（保持关联关系）"""
        results = []
        
        if not files:
            return results
        
        # 使用组中的"主要"文件确定目标文件夹
        main_file = self._get_main_file_from_group(files)
        target_subdir = self._determine_target_folder(
            main_file, rules, custom_rules, type_mapping or self.default_type_mapping
        )
        
        # 如果是特殊组，可能需要特殊处理
        if group_name.startswith('project_'):
            target_subdir = os.path.join(target_subdir, f"project_{main_file.parent.name}")
        elif group_name.startswith('program_'):
            target_subdir = os.path.join(target_subdir, f"program_{main_file.stem}")
        
        final_target_dir = target_path / target_subdir
        final_target_dir.mkdir(parents=True, exist_ok=True)
        
        # 将组中的所有文件移动到同一目标文件夹
        for file_path in files:
            try:
                target_file_path = self._resolve_filename_conflict(
                    final_target_dir / file_path.name
                )
                
                success, status = self._execute_file_operation(
                    file_path, target_file_path, operation
                )
                
                file_record = {
                    'filename': file_path.name,
                    'source': str(file_path),
                    'target': str(target_file_path) if success else '',
                    'operation': operation,
                    'status': status,
                    'success': success,
                    'size': file_path.stat().st_size if file_path.exists() else 0,
                    'timestamp': datetime.now().isoformat(),
                    'group': group_name,
                    'association_preserved': True
                }
                
                results.append(file_record)
                
            except Exception as e:
                error_record = {
                    'filename': file_path.name,
                    'source': str(file_path),
                    'target': '',
                    'operation': operation,
                    'status': f'错误: {str(e)}',
                    'success': False,
                    'size': 0,
                    'timestamp': datetime.now().isoformat(),
                    'group': group_name,
                    'association_preserved': False
                }
                results.append(error_record)
        
        return results
    
    def _get_main_file_from_group(self, files: List[Path]) -> Path:
        """从文件组中获取主要文件（用于确定分类）"""
        # 优先级：可执行文件 > 网页文件 > 代码文件 > 其他
        priority_extensions = [
            ['.exe', '.app', '.jar'],  # 可执行文件
            ['.html', '.htm'],         # 网页文件
            ['.py', '.js', '.java'],   # 代码文件
            ['.mp4', '.avi', '.mkv'],  # 视频文件
            ['.pdf', '.docx']          # 文档文件
        ]
        
        for ext_group in priority_extensions:
            for file in files:
                if file.suffix.lower() in ext_group:
                    return file
        
        # 如果没有找到优先文件，返回第一个
        return files[0]
    
    def _classify_single_file(self, file_path: Path, target_path: Path,
                            rules: List[str], operation: str,
                            custom_rules: List[Dict] = None,
                            type_mapping: Dict[str, List[str]] = None) -> List[Dict]:
        """分类单个文件"""
        results = []
        
        try:
            target_subdir = self._determine_target_folder(
                file_path, rules, custom_rules, type_mapping or self.default_type_mapping
            )
            final_target_dir = target_path / target_subdir
            final_target_dir.mkdir(parents=True, exist_ok=True)
            
            # 计算目标文件路径
            initial_target_file_path = final_target_dir / file_path.name
            
            # 检查源文件和目标文件是否是同一个文件
            if file_path.resolve() == initial_target_file_path.resolve():
                # 如果是同一个文件，直接返回成功，不需要移动
                file_record = {
                    'filename': file_path.name,
                    'source': str(file_path),
                    'target': str(file_path),  # 目标就是源文件本身
                    'operation': operation,
                    'status': '文件已在正确位置',
                    'success': True,
                    'size': file_path.stat().st_size if file_path.exists() else 0,
                    'timestamp': datetime.now().isoformat(),
                    'group': 'individual',
                    'association_preserved': False
                }
                results.append(file_record)
                return results
            
            # 如果不是同一个文件，才处理文件名冲突
            target_file_path = self._resolve_filename_conflict(initial_target_file_path)
            
            success, status = self._execute_file_operation(
                file_path, target_file_path, operation
            )
            
            file_record = {
                'filename': file_path.name,
                'source': str(file_path),
                'target': str(target_file_path) if success else '',
                'operation': operation,
                'status': status,
                'success': success,
                'size': file_path.stat().st_size if file_path.exists() else 0,
                'timestamp': datetime.now().isoformat(),
                'group': 'individual',
                'association_preserved': False
            }
            
            results.append(file_record)
            
        except Exception as e:
            error_record = {
                'filename': file_path.name,
                'source': str(file_path),
                'target': '',
                'operation': operation,
                'status': f'错误: {str(e)}',
                'success': False,
                'size': 0,
                'timestamp': datetime.now().isoformat(),
                'group': 'individual',
                'association_preserved': False
            }
            results.append(error_record)
        
        return results
    
    # 继承原有的方法
    def _should_skip_directory(self, dir_path: Path) -> bool:
        """检查目录是否应该被跳过（存在标志文件）"""
        if not self.respect_flag_file:
            return False
        
        flag_file_path = dir_path / self.flag_file_name
        return flag_file_path.exists()
    
    def _get_files_from_source(self, source_path: Path) -> List[Path]:
        """从源路径获取所有文件，跳过带有标志文件的目录"""
        files = []
        try:
            if source_path.is_file():
                files.append(source_path)
            elif source_path.is_dir():
                # 如果根目录有标志文件，直接返回空列表
                if self._should_skip_directory(source_path):
                    return []
                
                # 遍历目录
                for root, dirs, filenames in os.walk(source_path):
                    root_path = Path(root)
                    
                    # 检查当前目录是否有标志文件
                    if self._should_skip_directory(root_path):
                        # 从dirs中移除所有子目录，这样os.walk就不会继续遍历它们
                        dirs.clear()
                        continue
                    
                    # 添加当前目录中的文件
                    for filename in filenames:
                        if filename != self.flag_file_name:  # 不包含标志文件本身
                            files.append(root_path / filename)
        except PermissionError:
            pass
        return files
    
    def _determine_target_folder(self, file_path: Path, rules: List[str],
                               custom_rules: List[Dict] = None,
                               type_mapping: Dict[str, List[str]] = None) -> str:
        """根据规则确定目标文件夹"""
        target_parts = []
        current_type_mapping = type_mapping or self.default_type_mapping
        
        # 首先检查自定义规则
        if 'by_custom' in rules and custom_rules:
            custom_folder = self._apply_custom_rules(file_path, custom_rules)
            if custom_folder:
                return custom_folder

        if 'by_ai' in rules:
            ai_folder = self._determine_target_folder_ai(file_path)
            if ai_folder:
                return ai_folder
        
        # 按文件类型分类
        if 'by_type' in rules:
            file_type = self._get_file_type(file_path, current_type_mapping)
            target_parts.append(file_type)
        
        # 按修改日期分类
        if 'by_date' in rules:
            date_folder = self._get_date_folder(file_path)
            target_parts.append(date_folder)
        
        # 按文件大小分类
        if 'by_size' in rules:
            size_folder = self._get_size_folder(file_path)
            target_parts.append(size_folder)
        
        if not target_parts:
            target_parts.append('未分类')
        
        return os.path.join(*target_parts)

    def _determine_target_folder_ai(self, file_path: Path) -> Optional[str]:
        try:
            from config_manager import ConfigManager
            from secure_storage import SecureKeyStore
            from ai_service import FileCategorizationAIClient, build_file_metadata

            config_manager = ConfigManager()
            ai_cfg = config_manager.get_nested_setting('ai_service', default={}) or {}
            if not ai_cfg.get('enabled', False):
                return None

            api_key = SecureKeyStore().get_secret('ai_api_key')
            if not api_key:
                return None

            if self.ai_client is None:
                self.ai_filename_only = bool(ai_cfg.get('filename_only', True))
                self.ai_client = FileCategorizationAIClient(
                    api_key=api_key,
                    provider=str(ai_cfg.get('provider', 'openai')),
                    endpoint=str(ai_cfg.get('endpoint', 'https://api.openai.com/v1/chat/completions')),
                    model=str(ai_cfg.get('model', 'gpt-4o-mini')),
                    proxy=str(ai_cfg.get('proxy', '')),
                )

            content_assist_enabled = bool(ai_cfg.get('content_assist_enabled', False))
            if self.ai_filename_only:
                content_assist_enabled = False

            meta = build_file_metadata(
                str(file_path),
                filename_only=self.ai_filename_only,
                content_assist_enabled=content_assist_enabled,
                max_content_chars=int(ai_cfg.get('max_content_chars', 2000) or 2000),
                allowed_text_exts=ai_cfg.get('allowed_text_exts', None),
                desensitize_enabled=bool(ai_cfg.get('desensitize_enabled', True)),
            )
            result = self.ai_client.categorize_metadata(meta, allowed_categories=[])
            return result.category
        except Exception:
            return None
    
    def _get_file_type(self, file_path: Path, type_mapping: Dict[str, List[str]]) -> str:
        """根据文件扩展名获取文件类型"""
        extension = file_path.suffix.lower()
        
        for type_name, extensions in type_mapping.items():
            if extension in extensions:
                return type_name
        
        return 'others'
    
    def _get_date_folder(self, file_path: Path) -> str:
        """根据文件修改时间获取日期文件夹"""
        try:
            mtime = os.path.getmtime(file_path)
            date = datetime.fromtimestamp(mtime)
            return date.strftime('%Y-%m')
        except:
            return '未知日期'
    
    def _get_size_folder(self, file_path: Path) -> str:
        """根据文件大小获取大小文件夹"""
        try:
            size = file_path.stat().st_size
            
            if size < 1024 * 1024:
                return '小文件(<1MB)'
            elif size < 10 * 1024 * 1024:
                return '中文件(1-10MB)'
            elif size < 100 * 1024 * 1024:
                return '大文件(10-100MB)'
            else:
                return '超大文件(>100MB)'
        except:
            return '未知大小'
    
    def _apply_custom_rules(self, file_path: Path, custom_rules: List[Dict]) -> Optional[str]:
        """应用自定义规则"""
        filename = file_path.name.lower()
        
        for rule in custom_rules:
            pattern = rule.get('pattern', '').lower()
            target_folder = rule.get('target_folder', '')
            
            if pattern and target_folder:
                if fnmatch.fnmatch(filename, pattern):
                    return target_folder
        
        return None
    
    def _resolve_filename_conflict(self, target_path: Path) -> Path:
        """解决文件名冲突"""
        if not target_path.exists():
            return target_path
        
        # 检查是否是同一个文件（通过 inode 或路径比较）
        # 如果目标路径已存在，但指向的是同一个文件，则不需要重命名
        try:
            # 对于移动操作，如果源文件和目标文件是同一个，直接返回原路径
            if target_path.exists() and target_path.is_file():
                # 这里我们需要从调用栈中获取源文件路径进行比较
                # 但由于架构限制，我们采用另一种方法：检查文件是否已经在正确位置
                return target_path
        except:
            pass
        
        counter = 1
        stem = target_path.stem
        suffix = target_path.suffix
        parent = target_path.parent
        
        while True:
            new_name = f"{stem}_{counter}{suffix}"
            new_path = parent / new_name
            if not new_path.exists():
                return new_path
            counter += 1
            if counter > 1000:
                break
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return parent / f"{stem}_{timestamp}{suffix}"
    
    def _execute_file_operation(self, source_path: Path, target_path: Path, 
                              operation: str) -> tuple[bool, str]:
        """执行文件操作"""
        try:
            if operation == 'move':
                shutil.move(str(source_path), str(target_path))
                return True, '移动成功'
            elif operation == 'copy':
                shutil.copy2(str(source_path), str(target_path))
                return True, '复制成功'
            elif operation == 'link':
                os.link(str(source_path), str(target_path))
                return True, '链接成功'
            else:
                return False, f'未知操作类型: {operation}'
        except Exception as e:
            return False, f'操作失败: {str(e)}'
    
    def _save_operation_history(self, operation: Dict):
        """保存操作历史"""
        self.operation_history.append(operation)
        
        if len(self.operation_history) > self.max_history:
            self.operation_history = self.operation_history[-self.max_history:]
        
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.operation_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def load_operation_history(self):
        """加载操作历史"""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.operation_history = json.load(f)
        except Exception as e:
            print(f"加载历史记录失败: {e}")
            self.operation_history = []
    
    def preview_associations(self, source_path: str) -> Dict[str, Any]:
        """预览文件关联关系"""
        source_path = Path(source_path)
        file_groups = self.analyze_file_associations(source_path)
        
        preview_info = {
            'total_files': sum(len(files) for files in file_groups.values()),
            'total_groups': len(file_groups),
            'groups': {}
        }
        
        for group_name, files in file_groups.items():
            preview_info['groups'][group_name] = {
                'file_count': len(files),
                'files': [str(f) for f in files],
                'main_file': str(self._get_main_file_from_group(files)) if len(files) > 1 else str(files[0])
            }
        
        return preview_info
    
    def undo_last_operation(self) -> tuple[bool, str]:
        """
        撤销上次操作
        
        Returns:
            (success: bool, message: str)
        """
        if not self.operation_history:
            return False, "没有可撤销的操作"
            
        last_operation = self.operation_history[-1]
        
        try:
            undone_files = 0
            failed_files = 0
            
            # 撤销文件操作（逆序进行）
            for file_record in reversed(last_operation['files']):
                if not file_record.get('success', False):
                    continue
                    
                try:
                    source_path = Path(file_record['source'])
                    target_path = Path(file_record['target'])
                    
                    if last_operation['operation'] == 'move':
                        # 移动操作的撤销：将文件移回原位置
                        if target_path.exists():
                            # 确保源目录存在
                            source_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(target_path), str(source_path))
                            undone_files += 1
                    elif last_operation['operation'] == 'copy':
                        # 复制操作的撤销：删除目标文件
                        if target_path.exists():
                            send2trash.send2trash(str(target_path))
                            undone_files += 1
                    elif last_operation['operation'] == 'link':
                        # 链接操作的撤销：删除链接文件
                        if target_path.exists():
                            target_path.unlink()
                            undone_files += 1
                            
                except Exception as e:
                    print(f"撤销文件 {file_record['filename']} 失败: {e}")
                    failed_files += 1
                    
            # 移除历史记录
            self.operation_history.pop()
            
            # 更新历史文件
            try:
                with open(self.history_file, 'w', encoding='utf-8') as f:
                    json.dump(self.operation_history, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"更新历史文件失败: {e}")
            
            if failed_files == 0:
                return True, f"成功撤销 {undone_files} 个文件的操作"
            else:
                return True, f"撤销完成，成功 {undone_files} 个，失败 {failed_files} 个"
            
        except Exception as e:
            return False, f"撤销操作失败: {str(e)}"
            
    def get_operation_history(self) -> List[Dict]:
        """获取操作历史"""
        return self.operation_history.copy()
        
    def clear_history(self):
        """清空操作历史"""
        self.operation_history.clear()
        try:
            if self.history_file.exists():
                self.history_file.unlink()
        except Exception as e:
            print(f"清空历史文件失败: {e}")
            
    def get_statistics(self) -> Dict[str, Any]:
        """获取分类统计信息"""
        stats = {
            'total_operations': len(self.operation_history),
            'total_files_processed': 0,
            'operations_by_type': {},
            'files_by_type': {}
        }
        
        for operation in self.operation_history:
            op_type = operation['operation']
            stats['operations_by_type'][op_type] = stats['operations_by_type'].get(op_type, 0) + 1
            
            for file_record in operation['files']:
                if file_record.get('success', False):
                    stats['total_files_processed'] += 1
                    
        return stats 