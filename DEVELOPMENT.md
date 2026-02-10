# 智能文件分类器 - 开发指南

本文件为开发者提供“智能文件分类器”项目的技术细节、架构设计和贡献指南。

## 目录
- [项目架构](#-项目架构)
- [技术实现亮点](#-技术实现亮点)
- [构建与发行](#-构建与发行)
- [未来扩展建议](#-未来扩展建议)

---

## 🏗️ 项目架构

### 核心模块结构
```
智能文件分类器/
├── 核心功能模块
│   ├── main.py                      # 主程序和GUI界面
│   ├── file_classifier.py          # 文件分类核心逻辑
│   ├── file_classifier_enhanced.py # 增强版分类器
│   ├── config_manager.py           # 配置管理系统
│   ├── file_monitor.py             # 文件监控功能
│   └── settings_dialog.py          # 高级设置对话框
├── 启动和配置
│   ├── run.py                  # 智能启动脚本
│   ├── requirements.txt       # Python依赖包
│   ├── install.bat/.sh        # 自动安装脚本
│   └── start.bat/.sh          # 快速启动脚本
├── 构建和发行
│   ├── build_executable.py    # 可执行文件构建脚本
│   ├── build.bat/.sh          # 构建启动脚本
│   └── .github/workflows/     # GitHub Actions自动构建配置
└── 文档
    ├── README.md              # 项目说明
    ├── 使用指南.md           # 详细使用指南
    ├── CHANGELOG.md           # 更新日志
    └── DEVELOPMENT.md         # 开发指南
```

---

## 🛠️ 技术实现亮点

### 架构设计
- **模块化设计**: 清晰的职责分离，易于维护和扩展
- **事件驱动**: 使用消息队列实现线程间通信
- **配置持久化**: 完善的配置管理和状态保存
- **错误处理**: 全面的异常处理和用户友好的错误提示

### 核心技术
- **文件监控**: 基于`watchdog`的高效文件系统监控
- **并发处理**: 多线程处理避免界面冻结
- **模式匹配**: 灵活的文件名匹配系统
- **路径处理**: 跨平台的文件路径管理

---

## 📦 构建与发行

### 构建自己的可执行文件

如果您希望自己构建可执行文件，可以按照以下步骤操作：

#### 准备工作
1. 确保已安装Python 3.7+
2. 克隆或下载项目源码
3. 安装依赖：`pip install -r requirements.txt`

#### 使用构建脚本

- **Windows**:
  ```bash
  # 直接运行批处理文件
  build.bat
  ```
- **Linux/macOS**:
  ```bash
  # 添加执行权限
  chmod +x build.sh
  # 运行脚本
  ./build.sh
  ```

#### 手动构建
```bash
# 安装PyInstaller
pip install pyinstaller

# 构建可执行文件
pyinstaller --name="智能文件分类器" --onefile --windowed --clean --add-data="README.md:." --add-data="使用指南.md:." main.py
```
构建完成后，可执行文件将位于`dist`目录中。

### GitHub Actions 自动构建

本项目已配置GitHub Actions工作流，可在推送标签时自动构建并发布可执行文件。

#### 触发自动构建
```bash
# 创建新标签
git tag v1.2.0
# 推送标签到GitHub
git push origin v1.2.0
```
推送标签后，GitHub Actions将自动构建Windows、Linux和macOS版本的可执行文件，并创建新的Release。

---

## 🔮 未来扩展建议

### 功能增强
- [ ] 添加文件内容分析（如图片EXIF信息）
- [ ] 支持网络文件系统
- [ ] 增加文件重复检测
- [ ] 添加批处理脚本支持

### 界面优化
- [ ] 支持主题切换
- [ ] 添加文件预览功能
- [ ] 增强拖拽操作
- [ ] 添加进度动画

### 性能提升
- [ ] 实现增量备份
- [ ] 添加文件索引
- [ ] 优化大文件处理
- [ ] 支持云存储集成
