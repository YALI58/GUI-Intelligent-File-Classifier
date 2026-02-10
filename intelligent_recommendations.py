#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能推荐系统模块
提供基于文件内容和用户历史的智能分类建议、清理建议和整理提醒功能
"""

import os
import hashlib
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import defaultdict, Counter
import mimetypes

class IntelligentRecommendationEngine:
    """智能推荐引擎"""
    
    def __init__(self):
        self.config_dir = Path.home() / '.file_classifier_ai'
        self.config_dir.mkdir(exist_ok=True)
        
        # 用户行为历史文件
        self.user_behavior_file = self.config_dir / 'user_behavior.json'
        self.file_analysis_cache = self.config_dir / 'file_analysis_cache.json'
        self.recommendations_history = self.config_dir / 'recommendations_history.json'
        
        # 用户行为数据
        self.user_behavior = self._load_user_behavior()
        self.file_cache = self._load_file_cache()
        
        # 临时文件模式
        self.temp_patterns = {
            'extensions': {'.tmp', '.temp', '.bak', '.backup', '.old', '.orig', '.cache'},
            'prefixes': {'~', '.~', 'temp_', 'tmp_', 'backup_'},
            'folders': {'temp', 'tmp', 'cache', 'backup', 'trash', '$RECYCLE.BIN', '.Trash'}
        }
        
        # 重复文件阈值（字节）
        self.duplicate_size_threshold = 1024  # 1KB以上才检查重复
        
    def _load_user_behavior(self) -> Dict[str, Any]:
        """加载用户行为历史"""
        if self.user_behavior_file.exists():
            try:
                with open(self.user_behavior_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            'classification_history': [],  # 分类历史
            'manual_adjustments': [],      # 手动调整记录
            'folder_preferences': {},      # 文件夹偏好
            'file_type_preferences': {},   # 文件类型偏好
            'usage_patterns': {},          # 使用模式
            'rejection_history': []        # 拒绝的建议历史
        }
    
    def _load_file_cache(self) -> Dict[str, Any]:
        """加载文件分析缓存"""
        if self.file_analysis_cache.exists():
            try:
                with open(self.file_analysis_cache, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {}
    
    def _save_user_behavior(self):
        """保存用户行为数据"""
        try:
            with open(self.user_behavior_file, 'w', encoding='utf-8') as f:
                json.dump(self.user_behavior, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存用户行为数据失败: {e}")
    
    def _save_file_cache(self):
        """保存文件分析缓存"""
        try:
            with open(self.file_analysis_cache, 'w', encoding='utf-8') as f:
                json.dump(self.file_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存文件缓存失败: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值（用于重复文件检测）"""
        hash_md5 = hashlib.md5()
        try:
            with open(file_path, "rb") as f:
                # 只读取文件的开头和结尾部分，提高性能
                chunk_size = 65536  # 64KB
                chunk = f.read(chunk_size)
                hash_md5.update(chunk)
                
                # 如果文件较大，还读取中间和结尾部分
                file_size = file_path.stat().st_size
                if file_size > chunk_size * 2:
                    f.seek(file_size // 2)
                    chunk = f.read(chunk_size)
                    hash_md5.update(chunk)
                    
                    f.seek(-min(chunk_size, file_size))
                    chunk = f.read(chunk_size)
                    hash_md5.update(chunk)
        except Exception:
            return ""
        return hash_md5.hexdigest()
    
    def _analyze_file_content(self, file_path: Path) -> Dict[str, Any]:
        """分析文件内容特征"""
        try:
            stat = file_path.stat()
            mime_type, _ = mimetypes.guess_type(str(file_path))
            
            analysis = {
                'size': stat.st_size,
                'created_time': stat.st_ctime,
                'modified_time': stat.st_mtime,
                'accessed_time': stat.st_atime,
                'mime_type': mime_type,
                'extension': file_path.suffix.lower(),
                'is_hidden': file_path.name.startswith('.'),
                'file_hash': self._get_file_hash(file_path) if stat.st_size > self.duplicate_size_threshold else "",
                'keywords': self._extract_keywords(file_path)
            }
            
            return analysis
        except Exception as e:
            print(f"分析文件 {file_path} 失败: {e}")
            return {}
    
    def _extract_keywords(self, file_path: Path) -> List[str]:
        """从文件名和路径中提取关键词"""
        keywords = []
        
        # 从文件名提取
        name_parts = file_path.stem.lower().replace('_', ' ').replace('-', ' ').split()
        keywords.extend(name_parts)
        
        # 从路径提取
        path_parts = [p.lower() for p in file_path.parts[:-1]]
        keywords.extend(path_parts)
        
        # 过滤常见无意义词汇
        stop_words = {'and', 'or', 'the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
        keywords = [k for k in keywords if k not in stop_words and len(k) > 1]
        
        return list(set(keywords))
    
    def record_user_action(self, action_type: str, file_path: str, 
                          original_suggestion: str, final_location: str):
        """记录用户行为"""
        action = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,  # 'accept', 'reject', 'modify'
            'file_path': file_path,
            'original_suggestion': original_suggestion,
            'final_location': final_location
        }
        
        if action_type == 'accept':
            self.user_behavior['classification_history'].append(action)
        elif action_type == 'modify':
            self.user_behavior['manual_adjustments'].append(action)
        elif action_type == 'reject':
            self.user_behavior['rejection_history'].append(action)
        
        # 更新偏好统计
        self._update_preferences(action)
        self._save_user_behavior()
    
    def _update_preferences(self, action: Dict[str, Any]):
        """更新用户偏好统计"""
        file_path = Path(action['file_path'])
        extension = file_path.suffix.lower()
        final_location = action['final_location']
        
        # 更新文件类型偏好
        if extension not in self.user_behavior['file_type_preferences']:
            self.user_behavior['file_type_preferences'][extension] = {}
        
        location_prefs = self.user_behavior['file_type_preferences'][extension]
        location_prefs[final_location] = location_prefs.get(final_location, 0) + 1
        
        # 更新文件夹偏好（基于关键词）
        keywords = self._extract_keywords(file_path)
        for keyword in keywords:
            if keyword not in self.user_behavior['folder_preferences']:
                self.user_behavior['folder_preferences'][keyword] = {}
            
            keyword_prefs = self.user_behavior['folder_preferences'][keyword]
            keyword_prefs[final_location] = keyword_prefs.get(final_location, 0) + 1
    
    def get_classification_suggestions(self, file_path: str, 
                                     possible_locations: List[str]) -> List[Dict[str, Any]]:
        """基于文件内容和用户历史推荐分类方案"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            return []
        
        # 分析文件
        file_analysis = self._analyze_file_content(file_path)
        
        # 缓存分析结果
        cache_key = f"{file_path}_{file_analysis.get('modified_time', 0)}"
        self.file_cache[cache_key] = file_analysis
        
        suggestions = []
        
        # 基于文件类型的历史偏好
        extension = file_path.suffix.lower()
        if extension in self.user_behavior['file_type_preferences']:
            type_prefs = self.user_behavior['file_type_preferences'][extension]
            for location, count in sorted(type_prefs.items(), key=lambda x: x[1], reverse=True):
                if location in possible_locations:
                    confidence = min(count / 10.0, 1.0)  # 最多10次记录达到100%置信度
                    suggestions.append({
                        'location': location,
                        'confidence': confidence,
                        'reason': f'基于{extension}文件的历史分类偏好（{count}次）',
                        'type': 'type_preference'
                    })
        
        # 基于关键词的偏好
        keywords = file_analysis.get('keywords', [])
        keyword_scores = defaultdict(float)
        
        for keyword in keywords:
            if keyword in self.user_behavior['folder_preferences']:
                keyword_prefs = self.user_behavior['folder_preferences'][keyword]
                for location, count in keyword_prefs.items():
                    if location in possible_locations:
                        keyword_scores[location] += count * 0.1
        
        for location, score in keyword_scores.items():
            if score > 0:
                suggestions.append({
                    'location': location,
                    'confidence': min(score, 1.0),
                    'reason': f'基于文件名关键词的历史偏好',
                    'type': 'keyword_preference'
                })
        
        # 基于文件大小的建议
        file_size = file_analysis.get('size', 0)
        if file_size > 100 * 1024 * 1024:  # 大于100MB
            large_file_locations = [loc for loc in possible_locations if 'large' in loc.lower() or 'media' in loc.lower()]
            for location in large_file_locations:
                suggestions.append({
                    'location': location,
                    'confidence': 0.7,
                    'reason': '大文件建议存放在专门位置',
                    'type': 'size_based'
                })
        
        # 基于时间的建议
        file_age_days = (time.time() - file_analysis.get('modified_time', time.time())) / (24 * 3600)
        if file_age_days > 365:  # 超过一年的文件
            archive_locations = [loc for loc in possible_locations if 'archive' in loc.lower() or 'old' in loc.lower()]
            for location in archive_locations:
                suggestions.append({
                    'location': location,
                    'confidence': 0.6,
                    'reason': '旧文件建议归档',
                    'type': 'time_based'
                })
        
        # 去重并排序
        location_seen = set()
        unique_suggestions = []
        for suggestion in sorted(suggestions, key=lambda x: x['confidence'], reverse=True):
            if suggestion['location'] not in location_seen:
                location_seen.add(suggestion['location'])
                unique_suggestions.append(suggestion)
        
        return unique_suggestions[:5]  # 返回前5个建议
    
    def get_cleanup_suggestions(self, directory_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """识别重复文件、临时文件、过期文件等"""
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            return {}
        
        suggestions = {
            'duplicates': [],
            'temp_files': [],
            'large_files': [],
            'old_files': [],
            'empty_files': []
        }
        
        # 收集所有文件
        all_files = []
        file_hashes = defaultdict(list)
        
        for file_path in directory.rglob('*'):
            if file_path.is_file():
                try:
                    stat = file_path.stat()
                    file_info = {
                        'path': str(file_path),
                        'size': stat.st_size,
                        'modified_time': stat.st_mtime,
                        'created_time': stat.st_ctime,
                        'name': file_path.name
                    }
                    all_files.append(file_info)
                    
                    # 检查重复文件
                    if stat.st_size > self.duplicate_size_threshold:
                        file_hash = self._get_file_hash(file_path)
                        if file_hash:
                            file_hashes[file_hash].append(file_info)
                except Exception as e:
                    print(f"处理文件 {file_path} 时出错: {e}")
                    continue
        
        # 识别重复文件
        for hash_value, files in file_hashes.items():
            if len(files) > 1:
                # 按修改时间排序，最新的保留，其他的标记为重复
                files_sorted = sorted(files, key=lambda x: x['modified_time'], reverse=True)
                for duplicate_file in files_sorted[1:]:
                    suggestions['duplicates'].append({
                        'path': duplicate_file['path'],
                        'size': duplicate_file['size'],
                        'reason': f'与 {files_sorted[0]["path"]} 重复',
                        'can_delete': True,
                        'original': files_sorted[0]['path']
                    })
        
        # 识别临时文件
        for file_info in all_files:
            file_path = Path(file_info['path'])
            is_temp = False
            reason = ""
            
            # 检查扩展名
            if file_path.suffix.lower() in self.temp_patterns['extensions']:
                is_temp = True
                reason = f"临时文件扩展名: {file_path.suffix}"
            
            # 检查前缀
            for prefix in self.temp_patterns['prefixes']:
                if file_path.name.startswith(prefix):
                    is_temp = True
                    reason = f"临时文件前缀: {prefix}"
                    break
            
            # 检查路径中的临时文件夹
            for part in file_path.parts:
                if part.lower() in self.temp_patterns['folders']:
                    is_temp = True
                    reason = f"位于临时目录: {part}"
                    break
            
            if is_temp:
                suggestions['temp_files'].append({
                    'path': file_info['path'],
                    'size': file_info['size'],
                    'reason': reason,
                    'can_delete': True
                })
        
        # 识别大文件（超过100MB）
        large_files = [f for f in all_files if f['size'] > 100 * 1024 * 1024]
        for file_info in sorted(large_files, key=lambda x: x['size'], reverse=True)[:20]:
            suggestions['large_files'].append({
                'path': file_info['path'],
                'size': file_info['size'],
                'size_mb': round(file_info['size'] / (1024 * 1024), 1),
                'reason': '占用大量存储空间',
                'can_archive': True
            })
        
        # 识别旧文件（超过2年未修改）
        two_years_ago = time.time() - (2 * 365 * 24 * 3600)
        old_files = [f for f in all_files if f['modified_time'] < two_years_ago]
        for file_info in old_files:
            days_old = int((time.time() - file_info['modified_time']) / (24 * 3600))
            suggestions['old_files'].append({
                'path': file_info['path'],
                'size': file_info['size'],
                'days_old': days_old,
                'reason': f'{days_old}天未修改，可能已过期',
                'can_archive': True
            })
        
        # 识别空文件
        empty_files = [f for f in all_files if f['size'] == 0]
        for file_info in empty_files:
            suggestions['empty_files'].append({
                'path': file_info['path'],
                'reason': '空文件，可能无用',
                'can_delete': True
            })
        
        return suggestions
    
    def get_organization_reminders(self, directory_path: str) -> List[Dict[str, Any]]:
        """根据文件夹混乱程度主动提醒用户整理"""
        directory = Path(directory_path)
        if not directory.exists() or not directory.is_dir():
            return []
        
        reminders = []
        
        try:
            # 统计文件夹信息
            all_items = list(directory.iterdir())
            files = [item for item in all_items if item.is_file()]
            folders = [item for item in all_items if item.is_dir()]
            
            # 检查文件数量过多
            if len(files) > 50:
                reminders.append({
                    'type': 'too_many_files',
                    'priority': 'high',
                    'message': f'该文件夹包含{len(files)}个文件，建议进行分类整理',
                    'suggestion': '考虑按文件类型或项目创建子文件夹',
                    'file_count': len(files)
                })
            
            # 检查文件类型混乱
            file_types = defaultdict(int)
            for file_path in files:
                extension = file_path.suffix.lower()
                file_types[extension] += 1
            
            if len(file_types) > 10:
                reminders.append({
                    'type': 'mixed_file_types',
                    'priority': 'medium',
                    'message': f'该文件夹包含{len(file_types)}种不同类型的文件',
                    'suggestion': '建议按文件类型分类整理',
                    'type_count': len(file_types),
                    'top_types': dict(Counter(file_types).most_common(5))
                })
            
            # 检查深度嵌套
            max_depth = self._calculate_max_depth(directory)
            if max_depth > 6:
                reminders.append({
                    'type': 'deep_nesting',
                    'priority': 'medium',
                    'message': f'文件夹嵌套深度达到{max_depth}层，可能影响访问效率',
                    'suggestion': '考虑重新组织文件夹结构，减少嵌套层数',
                    'max_depth': max_depth
                })
            
            # 检查文件名混乱
            messy_names = []
            for file_path in files:
                name = file_path.name
                if any(char in name for char in ['(1)', '(2)', '副本', 'copy', 'Copy']):
                    messy_names.append(name)
            
            if len(messy_names) > 5:
                reminders.append({
                    'type': 'messy_filenames',
                    'priority': 'low',
                    'message': f'发现{len(messy_names)}个可能是重复或临时的文件',
                    'suggestion': '检查并清理重复文件',
                    'messy_count': len(messy_names),
                    'examples': messy_names[:3]
                })
            
            # 检查大文件占比
            total_size = sum(file_path.stat().st_size for file_path in files)
            if total_size > 1024 * 1024 * 1024:  # 超过1GB
                large_files = [f for f in files if f.stat().st_size > 50 * 1024 * 1024]
                if large_files:
                    reminders.append({
                        'type': 'large_directory',
                        'priority': 'medium',
                        'message': f'该文件夹占用{total_size/(1024**3):.1f}GB空间',
                        'suggestion': '考虑将大文件移动到专门的存储位置',
                        'total_size_gb': round(total_size/(1024**3), 1),
                        'large_file_count': len(large_files)
                    })
            
            # 基于用户历史的提醒
            last_organized = self._get_last_organization_time(str(directory))
            if last_organized:
                days_since = (datetime.now() - last_organized).days
                if days_since > 30:
                    reminders.append({
                        'type': 'time_based',
                        'priority': 'low',
                        'message': f'该文件夹已{days_since}天未整理',
                        'suggestion': '建议定期整理文件夹以保持良好的组织状态',
                        'days_since': days_since
                    })
        
        except Exception as e:
            print(f"分析文件夹 {directory_path} 时出错: {e}")
        
        # 按优先级排序
        priority_order = {'high': 3, 'medium': 2, 'low': 1}
        reminders.sort(key=lambda x: priority_order.get(x['priority'], 0), reverse=True)
        
        return reminders
    
    def _calculate_max_depth(self, directory: Path, current_depth: int = 0) -> int:
        """计算文件夹的最大嵌套深度"""
        max_depth = current_depth
        try:
            for item in directory.iterdir():
                if item.is_dir():
                    depth = self._calculate_max_depth(item, current_depth + 1)
                    max_depth = max(max_depth, depth)
        except PermissionError:
            pass
        return max_depth
    
    def _get_last_organization_time(self, directory_path: str) -> Optional[datetime]:
        """获取文件夹的最后整理时间"""
        for action in reversed(self.user_behavior['classification_history']):
            if directory_path in action.get('final_location', ''):
                return datetime.fromisoformat(action['timestamp'])
        return None
    
    def generate_recommendations_report(self, directory_path: str) -> Dict[str, Any]:
        """生成完整的推荐报告"""
        directory = Path(directory_path)
        if not directory.exists():
            return {}
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'directory': str(directory),
            'summary': {},
            'cleanup_suggestions': self.get_cleanup_suggestions(str(directory)),
            'organization_reminders': self.get_organization_reminders(str(directory)),
            'recommendations': []
        }
        
        # 生成汇总信息
        cleanup = report['cleanup_suggestions']
        summary = {
            'total_duplicates': len(cleanup.get('duplicates', [])),
            'total_temp_files': len(cleanup.get('temp_files', [])),
            'total_large_files': len(cleanup.get('large_files', [])),
            'total_old_files': len(cleanup.get('old_files', [])),
            'total_empty_files': len(cleanup.get('empty_files', [])),
            'reminder_count': len(report['organization_reminders'])
        }
        
        # 计算潜在节省的空间
        potential_savings = 0
        for duplicate in cleanup.get('duplicates', []):
            potential_savings += duplicate.get('size', 0)
        for temp_file in cleanup.get('temp_files', []):
            potential_savings += temp_file.get('size', 0)
        for empty_file in cleanup.get('empty_files', []):
            potential_savings += empty_file.get('size', 0)
        
        summary['potential_space_savings_mb'] = round(potential_savings / (1024 * 1024), 1)
        report['summary'] = summary
        
        # 生成具体的推荐操作
        recommendations = []
        
        if summary['total_duplicates'] > 0:
            recommendations.append({
                'action': 'remove_duplicates',
                'priority': 'high',
                'description': f'删除{summary["total_duplicates"]}个重复文件',
                'impact': f'可节省{round(sum(d.get("size", 0) for d in cleanup.get("duplicates", [])) / (1024*1024), 1)}MB空间'
            })
        
        if summary['total_temp_files'] > 0:
            recommendations.append({
                'action': 'clean_temp_files',
                'priority': 'medium',
                'description': f'清理{summary["total_temp_files"]}个临时文件',
                'impact': f'可节省{round(sum(t.get("size", 0) for t in cleanup.get("temp_files", [])) / (1024*1024), 1)}MB空间'
            })
        
        if summary['total_large_files'] > 5:
            recommendations.append({
                'action': 'organize_large_files',
                'priority': 'medium',
                'description': f'整理{summary["total_large_files"]}个大文件',
                'impact': '优化文件夹结构，提高访问效率'
            })
        
        report['recommendations'] = recommendations
        
        # 保存报告历史
        self._save_recommendation_report(report)
        
        return report
    
    def _save_recommendation_report(self, report: Dict[str, Any]):
        """保存推荐报告到历史记录"""
        try:
            history = []
            if self.recommendations_history.exists():
                with open(self.recommendations_history, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            
            # 只保留最近50个报告
            history.append(report)
            history = history[-50:]
            
            with open(self.recommendations_history, 'w', encoding='utf-8') as f:
                json.dump(history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存推荐报告失败: {e}") 