#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件分类器测试模块
Tests for File Classifier
"""

import unittest
from pathlib import Path
import tempfile
import shutil

from src.core.file_classifier import FileClassifier
from src.core.enhanced_classifier import EnhancedFileClassifier
from src.core.hierarchical_classifier import HierarchicalFileClassifier


class TestFileClassifier(unittest.TestCase):
    """文件分类器基础测试"""
    
    def setUp(self):
        """测试前准备"""
        self.classifier = FileClassifier()
        self.test_dir = tempfile.mkdtemp()
        self.target_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.target_dir, ignore_errors=True)
    
    def test_init(self):
        """测试初始化"""
        self.assertIsNotNone(self.classifier.default_type_mapping)
        self.assertEqual(self.classifier.max_history, 50)
    
    def test_classify_by_type(self):
        """测试按类型分类"""
        test_file = Path(self.test_dir) / "test.txt"
        test_file.write_text("test content")
        
        results = self.classifier.classify_files(
            str(self.test_dir),
            str(self.target_dir),
            rules=['by_type'],
            operation='copy'
        )
        
        self.assertTrue(len(results) > 0)
        self.assertTrue(any(r.get('success') for r in results))


class TestEnhancedClassifier(unittest.TestCase):
    """增强版分类器测试"""
    
    def setUp(self):
        self.classifier = EnhancedFileClassifier()
        self.test_dir = tempfile.mkdtemp()
        self.target_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)
        shutil.rmtree(self.target_dir, ignore_errors=True)
    
    def test_association_detection(self):
        """测试文件关联检测"""
        file1 = Path(self.test_dir) / "document.pdf"
        file2 = Path(self.test_dir) / "document.txt"
        file1.write_text("pdf content")
        file2.write_text("txt content")
        
        results = self.classifier.classify_files(
            str(self.test_dir),
            str(self.target_dir),
            rules=['by_type'],
            operation='copy'
        )
        
        self.assertTrue(len(results) >= 2)


class TestHierarchicalClassifier(unittest.TestCase):
    """多层级分类器测试"""
    
    def setUp(self):
        self.classifier = HierarchicalFileClassifier()
    
    def test_category_determination(self):
        """测试类别确定"""
        test_file = Path("test.jpg")
        category = self.classifier._determine_hierarchical_category(test_file)
        self.assertIn('images', category)
    
    def test_config(self):
        """测试配置"""
        config = self.classifier.get_config()
        self.assertIn('max_depth', config)
        
        self.classifier.set_config(max_depth=5)
        config = self.classifier.get_config()
        self.assertEqual(config['max_depth'], 5)


if __name__ == '__main__':
    unittest.main()
