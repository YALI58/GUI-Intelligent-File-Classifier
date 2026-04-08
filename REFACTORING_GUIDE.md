# 智能文件分类器 - 重构版开发文档

## 项目结构

```
intelligent-file-classifier/
├── src/                          # 源代码目录
│   ├── __init__.py              # 包初始化
│   ├── main.py                  # 主程序入口
│   ├── core/                    # 核心分类模块
│   │   ├── __init__.py
│   │   ├── file_classifier.py           # 基础分类器
│   │   ├── enhanced_classifier.py       # 增强版分类器（支持关联检测）
│   │   └── hierarchical_classifier.py   # 多层级分类器
│   ├── ui/                      # 用户界面模块
│   │   ├── __init__.py
│   │   ├── main_window.py       # 主窗口
│   │   └── theme.py             # UI 主题
│   ├── services/                # 服务模块
│   │   ├── __init__.py
│   │   ├── config_manager.py    # 配置管理
│   │   ├── ai_service.py        # AI 服务
│   │   └── secure_storage.py    # 安全存储
│   ├── utils/                   # 工具模块
│   │   ├── __init__.py
│   │   └── file_monitor.py      # 文件监控
│   └── models/                  # 数据模型
├── tests/                       # 测试代码
│   ├── __init__.py
│   └── test_classifiers.py      # 分类器测试
├── requirements.txt             # 运行时依赖
├── requirements-dev.txt         # 开发依赖
└── README.md                    # 项目说明
```

## 模块说明

### 核心模块 (src/core)

- **FileClassifier**: 基础文件分类器，提供基本的按类型分类功能
- **EnhancedFileClassifier**: 增强版分类器，支持文件关联检测和保持
- **HierarchicalFileClassifier**: 多层级分类器，提供精细化的分类结构

### UI 模块 (src/ui)

- **FileClassifierApp**: 主应用程序类，提供完整的图形用户界面
- **theme**: Wabi-Sabi 风格主题，提供美观的界面效果

### 服务模块 (src/services)

- **ConfigManager**: 配置管理，负责保存和加载用户设置
- **AICategorizationService**: AI 分类服务，支持第三方 AI 集成
- **SecureStorage**: 安全存储，用于保护敏感信息如 API Key

### 工具模块 (src/utils)

- **FileMonitor**: 文件监控，提供实时文件变化和自动分类

## 使用示例

### 基础使用

```python
from src.core import FileClassifier

classifier = FileClassifier()
results = classifier.classify_files(
    source_path="/path/to/source",
    target_path="/path/to/target",
    rules=['by_type'],
    operation='move'
)
```

### 增强版使用

```python
from src.core import EnhancedFileClassifier

classifier = EnhancedFileClassifier()
results = classifier.classify_files(
    source_path="/path/to/source",
    target_path="/path/to/target",
    rules=['by_type'],
    operation='copy'
)
```

### 多层级分类

```python
from src.core import HierarchicalFileClassifier
from pathlib import Path

classifier = HierarchicalFileClassifier()
files = [Path("test.jpg"), Path("document.pdf")]
target = Path("/output")
results = classifier.classify(files, target)
```

## 运行测试

```bash
# 运行所有测试
python -m pytest tests/

# 运行特定测试
python -m pytest tests/test_classifiers.py -v
```

## 开发指南

### 添加新的分类器

1. 在 `src/core/` 目录下创建新的分类器文件
2. 继承基础分类器或实现统一接口
3. 在 `src/core/__init__.py` 中导出新类

### 添加新的 UI 组件

1. 在 `src/ui/` 目录下创建新的界面文件
2. 使用统一的 theme 样式
3. 在 `src/ui/__init__.py` 中导出新组件

### 代码规范

- 遵循 PEP 8 编码规范
- 所有公共方法必须有文档字符串
- 使用类型注解提高代码可读性
- 编写单元测试覆盖核心功能

## 迁移指南

### 从旧版本迁移

旧版本的代码仍然保留在项目根目录，新版本使用 `src/` 包结构。

**旧代码:**
```python
from file_classifier import FileClassifier
```

**新代码:**
```python
from src.core import FileClassifier
```

## 版本历史

- **v2.0.0** (重构版): 
  - 重新组织项目结构为包形式
  - 模块化设计，提高可维护性
  - 添加完整的测试套件
  - 改进代码注释和文档

- **v1.0.0** (原始版本):
  - 初始版本，所有代码在根目录
