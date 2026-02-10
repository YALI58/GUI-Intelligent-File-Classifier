#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件监控模块
提供实时文件监控和自动分类功能
"""

import os
import time
import threading
from pathlib import Path
from typing import List, Callable, Dict, Any, Optional, Set
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent, FileMovedEvent
from concurrent.futures import ThreadPoolExecutor

class FileClassifierHandler(FileSystemEventHandler):
    """优化后的文件分类事件处理器"""
    
    def __init__(self, classifier, target_path: str, rules: List[str], 
                 operation: str, callback: Callable, config_manager,
                 delay: float = 1.0, batch_size: int = 10):
        self.classifier = classifier
        self.target_path = target_path
        self.rules = rules
        self.operation = operation
        self.callback = callback
        self.config_manager = config_manager
        self.delay = delay
        self.batch_size = batch_size
        
        # 使用集合提高查找性能
        self.processing_files: Set[str] = set()
        self.processed_files: Set[str] = set()
        
        # 批量处理队列
        self.batch_queue: List[str] = []
        self.batch_lock = threading.Lock()
        self.batch_timer = None
        
        # 线程池用于并行处理
        self.executor = ThreadPoolExecutor(max_workers=4)
        
    def on_created(self, event):
        """文件创建事件"""
        if not event.is_directory:
            self._add_to_batch_queue(event.src_path)
            
    def on_moved(self, event):
        """文件移动事件"""
        if not event.is_directory:
            self._add_to_batch_queue(event.dest_path)
            
    def _add_to_batch_queue(self, file_path: str):
        """添加到批量处理队列"""
        file_path = str(Path(file_path).resolve())
        
        # 检查排除规则
        if self._should_exclude_file(file_path):
            return
            
        # 防止重复处理
        if file_path in self.processing_files or file_path in self.processed_files:
            return
            
        with self.batch_lock:
            self.batch_queue.append(file_path)
            
            # 达到批量大小立即处理
            if len(self.batch_queue) >= self.batch_size:
                self._process_batch()
            elif not self.batch_timer:
                # 设置延迟处理定时器
                self.batch_timer = threading.Timer(
                    self.delay, 
                    self._process_batch
                )
                self.batch_timer.start()
                
    def _process_batch(self):
        """处理批量文件"""
        with self.batch_lock:
            if not self.batch_queue:
                return
                
            # 获取当前批次并清空队列
            current_batch = self.batch_queue.copy()
            self.batch_queue.clear()
            
            # 重置定时器
            if self.batch_timer:
                self.batch_timer.cancel()
                self.batch_timer = None
        
        # 标记为处理中
        self.processing_files.update(current_batch)
        
        # 并行处理批量文件
        futures = []
        for file_path in current_batch:
            futures.append(self.executor.submit(
                self._process_single_file,
                file_path
            ))
            
        # 等待所有任务完成
        for future in futures:
            try:
                future.result()
            except Exception as e:
                print(f"文件处理失败: {e}")
        
        # 标记为已处理
        self.processed_files.update(current_batch)
        self.processing_files.difference_update(current_batch)
        
    def _process_single_file(self, file_path: str):
        """处理单个文件"""
        try:
            file_path = Path(file_path)
            
            # 优化后的文件稳定性检测
            if not self._wait_for_file_stable_optimized(file_path):
                return
                
            # 获取配置
            custom_rules = self.config_manager.get_custom_rules()
            type_mapping = self.config_manager.get_file_type_mapping()
            
            # 分类文件
            result = self.classifier.classify_single_file(
                str(file_path), self.target_path, self.rules, self.operation,
                [rule for rule in custom_rules if rule.get('enabled', True)],
                type_mapping
            )
            
            # 添加监控处理标记
            result['monitor_processed'] = True
            result['processing_time'] = time.time()
            
            # 回调通知
            if self.callback:
                self.callback(result)
                
        except Exception as e:
            error_result = {
                'filename': file_path.name if hasattr(file_path, 'name') else '未知',
                'source': str(file_path) if file_path else '',
                'target': '',
                'operation': self.operation,
                'status': f'监控处理错误: {str(e)}',
                'success': False,
                'monitor_processed': True,
                'processing_time': time.time()
            }
            if self.callback:
                self.callback(error_result)
    
    def _wait_for_file_stable_optimized(self, file_path: Path, timeout: int = 10) -> bool:
        """优化后的文件稳定性检测"""
        if not file_path.exists():
            return False
            
        try:
            # 初始状态
            last_size = -1
            last_mtime = 0
            stable_checks = 0
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                try:
                    stat = file_path.stat()
                    current_size = stat.st_size
                    current_mtime = stat.st_mtime
                    
                    # 检查大小和修改时间是否稳定
                    if current_size == last_size and current_mtime == last_mtime:
                        stable_checks += 1
                        if stable_checks >= 2:  # 连续2次检测稳定
                            return True
                    else:
                        stable_checks = 0
                        last_size = current_size
                        last_mtime = current_mtime
                        
                    time.sleep(0.3)  # 适当缩短检测间隔
                except (OSError, FileNotFoundError):
                    return False
                    
            return False
        except Exception:
            return False
            
    def cleanup(self):
        """清理资源"""
        with self.batch_lock:
            if self.batch_timer:
                self.batch_timer.cancel()
            self.batch_queue.clear()
        
        self.executor.shutdown(wait=False)

class FileMonitor:
    """文件监控器主类"""
    
    def __init__(self, watch_path: str, target_path: str, rules: List[str], 
                 operation: str, callback: Callable, config_manager):
        self.watch_path = Path(watch_path).resolve()
        self.target_path = target_path
        self.rules = rules
        self.operation = operation
        self.callback = callback
        self.config_manager = config_manager
        
        self.observer = None
        self.handler = None
        self.is_running = False
        self.start_time = None
        
        # 统计信息
        self.stats = {
            'files_processed': 0,
            'files_moved': 0,
            'files_copied': 0,
            'files_failed': 0,
            'total_size': 0,
            'start_time': None
        }
        
        # 导入分类器
        from file_classifier import FileClassifier
        self.classifier = FileClassifier()
        
    def start(self) -> bool:
        """开始监控"""
        if self.is_running:
            return True
            
        try:
            if not self.watch_path.exists():
                raise FileNotFoundError(f"监控路径不存在: {self.watch_path}")
                
            if not self.watch_path.is_dir():
                raise ValueError(f"监控路径不是目录: {self.watch_path}")
                
            # 获取监控延迟
            delay = self.config_manager.get_setting('monitor_delay', 1.0)
            
            # 创建事件处理器
            self.handler = FileClassifierHandler(
                self.classifier, self.target_path, self.rules, 
                self.operation, self._on_file_processed, 
                self.config_manager, delay
            )
            
            # 创建观察器
            self.observer = Observer()
            
            # 检查是否监控子文件夹
            recursive = self.config_manager.get_setting('monitor_subfolders', True)
            
            self.observer.schedule(
                self.handler, str(self.watch_path), recursive=recursive
            )
            
            self.observer.start()
            self.is_running = True
            self.start_time = time.time()
            self.stats['start_time'] = self.start_time
            
            return True
            
        except Exception as e:
            print(f"启动文件监控失败: {e}")
            return False
            
    def stop(self) -> bool:
        """停止监控"""
        if not self.is_running:
            return True
            
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)  # 等待最多5秒
                
            if self.handler:
                self.handler.cleanup()
                
            self.is_running = False
            return True
            
        except Exception as e:
            print(f"停止文件监控失败: {e}")
            return False
            
    def restart(self) -> bool:
        """重启监控"""
        self.stop()
        time.sleep(0.5)  # 短暂等待
        return self.start()
        
    def _on_file_processed(self, file_info: Dict[str, Any]):
        """文件处理回调"""
        # 更新统计信息
        self.stats['files_processed'] += 1
        
        if file_info.get('success', False):
            operation = file_info.get('operation', '')
            if operation == 'move':
                self.stats['files_moved'] += 1
            elif operation == 'copy':
                self.stats['files_copied'] += 1
                
            size = file_info.get('size', 0)
            self.stats['total_size'] += size
        else:
            self.stats['files_failed'] += 1
            
        # 转发到外部回调
        if self.callback:
            self.callback(file_info)
            
    def is_monitoring(self) -> bool:
        """检查是否正在监控"""
        return self.is_running and self.observer and self.observer.is_alive()
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取监控统计信息"""
        current_stats = self.stats.copy()
        
        if self.start_time:
            current_stats['uptime'] = time.time() - self.start_time
            
        current_stats['is_running'] = self.is_running
        current_stats['watch_path'] = str(self.watch_path)
        current_stats['target_path'] = self.target_path
        
        return current_stats
        
    def reset_statistics(self):
        """重置统计信息"""
        self.stats = {
            'files_processed': 0,
            'files_moved': 0,
            'files_copied': 0,
            'files_failed': 0,
            'total_size': 0,
            'start_time': time.time() if self.is_running else None
        }
        
    def update_settings(self, target_path: str = None, rules: List[str] = None,
                       operation: str = None):
        """更新监控设置"""
        if target_path:
            self.target_path = target_path
            if self.handler:
                self.handler.target_path = target_path
                
        if rules:
            self.rules = rules
            if self.handler:
                self.handler.rules = rules
                
        if operation:
            self.operation = operation
            if self.handler:
                self.handler.operation = operation
                
    def get_pending_files_count(self) -> int:
        """获取待处理文件数量"""
        if self.handler:
            return len(self.handler.batch_queue) # Changed from pending_files to batch_queue
        return 0
        
    def get_processing_files_count(self) -> int:
        """获取正在处理的文件数量"""
        if self.handler:
            return len(self.handler.processing_files)
        return 0

class MultiPathMonitor:
    """多路径监控器"""
    
    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.monitors = {}  # path -> FileMonitor
        self.global_callback = None
        
    def add_monitor(self, monitor_id: str, watch_path: str, target_path: str,
                   rules: List[str], operation: str, callback: Callable = None) -> bool:
        """添加监控路径"""
        try:
            if monitor_id in self.monitors:
                # 停止现有监控
                self.remove_monitor(monitor_id)
                
            combined_callback = self._create_combined_callback(monitor_id, callback)
            
            monitor = FileMonitor(
                watch_path, target_path, rules, operation,
                combined_callback, self.config_manager
            )
            
            self.monitors[monitor_id] = monitor
            return True
            
        except Exception as e:
            print(f"添加监控失败: {e}")
            return False
            
    def remove_monitor(self, monitor_id: str) -> bool:
        """移除监控路径"""
        if monitor_id in self.monitors:
            monitor = self.monitors[monitor_id]
            monitor.stop()
            del self.monitors[monitor_id]
            return True
        return False
        
    def start_monitor(self, monitor_id: str) -> bool:
        """启动指定监控"""
        if monitor_id in self.monitors:
            return self.monitors[monitor_id].start()
        return False
        
    def stop_monitor(self, monitor_id: str) -> bool:
        """停止指定监控"""
        if monitor_id in self.monitors:
            return self.monitors[monitor_id].stop()
        return False
        
    def start_all(self) -> int:
        """启动所有监控"""
        started = 0
        for monitor in self.monitors.values():
            if monitor.start():
                started += 1
        return started
        
    def stop_all(self) -> int:
        """停止所有监控"""
        stopped = 0
        for monitor in self.monitors.values():
            if monitor.stop():
                stopped += 1
        return stopped
        
    def get_all_statistics(self) -> Dict[str, Dict[str, Any]]:
        """获取所有监控的统计信息"""
        return {
            monitor_id: monitor.get_statistics()
            for monitor_id, monitor in self.monitors.items()
        }
        
    def set_global_callback(self, callback: Callable):
        """设置全局回调函数"""
        self.global_callback = callback
        
    def _create_combined_callback(self, monitor_id: str, specific_callback: Callable = None):
        """创建组合回调函数"""
        def combined_callback(file_info):
            # 添加监控器ID
            file_info['monitor_id'] = monitor_id
            
            # 调用特定回调
            if specific_callback:
                specific_callback(file_info)
                
            # 调用全局回调
            if self.global_callback:
                self.global_callback(file_info)
                
        return combined_callback
        
    def get_monitor_count(self) -> int:
        """获取监控器数量"""
        return len(self.monitors)
        
    def get_active_monitor_count(self) -> int:
        """获取活跃监控器数量"""
        return sum(1 for monitor in self.monitors.values() if monitor.is_monitoring())
        
    def cleanup(self):
        """清理所有监控器"""
        self.stop_all()
        self.monitors.clear() 