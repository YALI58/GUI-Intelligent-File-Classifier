# 贡献指南

感谢你考虑为智能文件分类器项目做出贡献！

## 🌟 如何贡献

### 报告问题

1. 使用 [GitHub Issues](https://github.com/YALI58/Intelligent-Document-Classifier/issues) 提交问题
2. 请尽可能详细地描述问题，包括：
   - 问题的具体表现
   - 复现步骤
   - 期望的行为
   - 系统环境信息
   - 相关的日志或截图

### 提交代码

1. Fork 项目到自己的账号
2. 创建你的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的修改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到你的分支 (`git push origin feature/AmazingFeature`)
5. 创建一个 Pull Request

### 代码风格

- 遵循 PEP 8 Python 代码规范
- 使用有意义的变量名和函数名
- 添加必要的注释
- 保持代码简洁清晰

### 提交信息规范

提交信息格式：
```
<类型>: <描述>

[可选的详细描述]

[可选的关闭 issue]
```

类型包括：
- feat: 新功能
- fix: 修复问题
- docs: 文档更新
- style: 代码格式调整
- refactor: 代码重构
- test: 测试相关
- chore: 构建过程或辅助工具的变动

示例：
```
feat: 添加文件类型自动识别功能

- 支持通过文件头识别真实类型
- 添加常见文件类型的识别规则
- 优化识别速度

Closes #123
```

### 文档贡献

- 改进现有文档
- 添加使用示例
- 修正文档错误
- 翻译文档

## 🔍 开发设置

1. 克隆项目
```bash
git clone https://github.com/YALI58/Intelligent-Document-Classifier.git
cd Intelligent-Document-Classifier
```

2. 创建虚拟环境
```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. 安装依赖
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # 开发依赖
```

4. 运行测试
```bash
python -m pytest
```

## 📝 开发流程

1. 选择或创建一个 issue
2. 在自己的分支上开发
3. 编写测试用例
4. 确保所有测试通过
5. 提交 Pull Request

## ⚠️ 注意事项

- 不要提交敏感信息
- 保持向后兼容性
- 更新相关文档
- 添加必要的测试
- 遵循现有的代码风格

## 🙏 感谢

再次感谢你的贡献！如果你有任何问题，欢迎在 Issues 中讨论。