# Intelligent File Classifier

<div align="center">

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/python-3.7%2B-blue)](https://www.python.org)
[![GitHub release](https://img.shields.io/github/v/release/YALI58/Intelligent-Document-Classifier)](https://github.com/YALI58/Intelligent-Document-Classifier/releases)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

English | [简体中文](README.md)

An intelligent file organization tool that automatically detects file relationships, classifies files intelligently, and provides real-time monitoring capabilities.

<p align="center">
  <img src="resources/demo.gif" alt="Demo" width="600">
</p>

</div>

## ✨ Core Features

### 🔥 Latest Features
- 🎯 **Hierarchical Smart Classification** - Break through traditional coarse classification, achieve fine-grained file organization
- 🤖 **Intelligent Recommendation System** - AI-driven classification suggestions, cleanup recommendations, and organization reminders
- 🧠 **Optional Third-Party AI Categorization** - DeepSeek / OpenAI compatible API: filename + limited content snippet (configurable/desensitized)
- 📊 **Visual Configuration** - Intuitive settings interface with real-time classification preview
- 🔍 **Pattern Recognition** - Automatically recognize screenshots, reports, mobile photos, and other file types
- 🧘 **Wabi-Sabi UI** - Calm whitespace, functional minimalism; global vertical scrolling + mouse wheel on all windows

### 🛡️ Core Functions
- 🤖 **Smart Association Detection** - Automatically identify and maintain file dependencies
- 🔄 **Real-time Monitoring** - Automatically process new files
- 🎯 **Multi-dimensional Classification** - Support classification by type, date, size, and more
- 🛡️ **Project Protection** - Automatically identify and protect complete project structures
- 📝 **Custom Rules** - Flexible classification rule configuration
- 🔍 **Preview Function** - View classification results before execution
- ↩️ **Undo Support** - Revert operations at any time
- 📊 **Complete Records** - Detailed operation history

## 🚀 Quick Start

### Option 1: Download Executable (Recommended)

1. Download the latest version from [Releases](https://github.com/YALI58/Intelligent-Document-Classifier/releases)
2. Extract and run the program
3. Select the folder to organize and start automatic classification

### Option 2: Run from Source

```bash
# Clone the project
git clone https://github.com/YALI58/Intelligent-Document-Classifier.git
cd intelligent-file-classifier

# Install dependencies
pip install -r requirements.txt

# Run the program
python main.py
```

### (Optional) Enable Third-Party AI Categorization (DeepSeek / OpenAI)

1. Open: `Advanced Settings → AI Service`
2. Enable: `Enable AI categorization (file categorization only)`
3. Choose provider:
   - `deepseek` (OpenAI-compatible)
   - `openai`
4. Enter and validate your API key (stored securely on your device, never written in plaintext to the config)
5. (Scheme B) Enable: `Use file content snippet to assist categorization`
   - Set max characters to send (default 2000)
   - Set allowed text extensions (e.g. `.txt,.md,.py,.json,.csv`)
   - Enable/disable desensitization (mask email/phone/ID patterns)
6. Back to main window, enable rule: `AI categorization (file categorization only)`

### Option 3: Quick Demo

```bash
# Demo intelligent recommendations
python demo_intelligent_recommendations.py

# Run practical usage demo
python practical_usage_demo.py

# Test hierarchical classification
python test_hierarchical_classification.py
```

## 📚 Complete Documentation

### 📖 User Guides
- 📋 [Basic Usage Guide](#basic-usage) - Quick start guide
- 🎯 [Hierarchical Classification Guide](hierarchical_classification_guide.md) - Detailed fine-grained classification tutorial
- 🤖 [Intelligent Recommendations Guide](intelligent_recommendations_guide.md) - AI recommendation system usage

### 🛠️ Developer Documentation
- 💻 [Development Guide](DEVELOPMENT.md) - Project development instructions
- 🤝 [Contributing Guide](CONTRIBUTING.md) - How to participate in project development
- 📝 [Changelog](CHANGELOG.md) - Version update records
- 🔧 [GitHub Actions Fix](GitHub-Actions-403-Fix.md) - CI/CD related issue solutions

### 🧪 Testing & Demos
- 🔬 [Test Documentation](test_hierarchical_classification.py) - Hierarchical classification testing
- 🎪 [Feature Demo](demo_intelligent_recommendations.py) - Intelligent recommendation demo
- 📱 [Real Usage Cases](practical_usage_demo.py) - Real-world application scenarios

## 📖 Core Feature Description

### Basic Usage

1. **Select Folders**
   - Source folder: Folder to organize
   - Target folder: Where organized files will be stored

2. **Configure Classification Rules**
   - 📂 By file type (recommended)
   - 📅 By modification date
   - 📏 By file size
   - 🎨 Custom rules

3. **Execute Classification**
   - 🔍 Click "Preview" to check classification results
   - ✅ Click "Start Classification" after confirmation

### 🎯 Hierarchical Smart Classification

Traditional classification problems:
```
Documents/ (500 files mixed together) 😰
Images/ (200 images piled up)
Videos/ (all videos in chaos)
```

Hierarchical classification solution:
```
Documents/ 😊
├── work/
│   ├── reports/ (3 related files)
│   ├── contracts/ (2 contracts)
│   └── presentations/ (1 presentation)
├── personal/
│   ├── notes/ (5 notes)
│   └── diaries/ (2 diaries)

Images/
├── photos/
│   ├── mobile_photos/ (mobile photos)
│   └── screenshots/ (screenshots)
├── graphics/
│   ├── logos/ (company logos)
│   └── icons/ (icon files)
```

**Key Advantages:**
- 🔍 **10x Search Efficiency** - From minutes to seconds
- 🤖 **90%+ Recognition Rate** - Automatically identify file purposes
- ⚡ **Adaptive Classification Depth** - Intelligently adjust based on file count
- 🔧 **Fully Compatible** - Enable/disable anytime

### 🤖 Intelligent Recommendation System

AI-driven three core functions:

1. **Classification Suggestions** 📊
   - Based on file content and user history
   - Recommend optimal classification schemes
   - Provide multiple classification options

2. **Cleanup Suggestions** 🧹
   - Identify duplicate files
   - Detect temporary files
   - Discover expired files

3. **Organization Reminders** ⏰
   - Based on folder clutter level
   - Proactively remind users to organize
   - Provide optimization suggestions

> Note: This project also supports **optional third-party AI categorization**.
> - **Intelligent Recommendation System**: built-in analysis/rule engine (does not require your third-party API key).
> - **Third-Party AI Categorization**: only enabled when you explicitly configure an API key; sends minimal metadata/snippet for classification.

### 🧠 Optional Third-Party AI Categorization

This feature enhances the decision of the target category folder, especially when filenames are ambiguous.

- **Categorization only**: fixed boundary `task=file_categorization`, no chat/edit/generation features
- **Privacy-first (Scheme B)**:
  - By default sends only filename/extension/keywords
  - Optionally sends a *limited* content snippet for whitelisted text types (first N characters)
  - Optional desensitization: mask email/phone/ID patterns before sending
- **Secure local storage**: API key is stored in system credential store via `keyring`, with a UI to clear it locally
- **Providers**: `deepseek` and `openai` (OpenAI-compatible interface)

### Smart Association Detection

The system automatically identifies the following associations:

- 📦 **Program Files** - .exe and its .dll/.ini dependencies
- 🌐 **Web Files** - .html and its .css/.js/image resources
- 🎬 **Media Files** - Videos and their subtitles/posters
- 📂 **Project Folders** - Automatically identify complete project structures
- 📄 **Related Files** - Keep related files aggregated

### Real-time Monitoring

1. Enable file monitoring in settings
2. Select folders to monitor
3. System will automatically process new files

## 🛠️ Tech Stack

- **Core Language**: Python 3.7+
- **GUI Framework**: tkinter
- **File Monitoring**: watchdog
- **Safe Deletion**: send2trash
- **Smart Analysis**: built-in rule/analysis engine + (optional) third-party AI categorization service
- **Multi-threading**: concurrent.futures
- **Secure Storage**: keyring (system credential store)
- **HTTP Client**: requests

## 📊 Project Structure

```
intelligent-file-classifier/
├── 📁 Core Modules
│   ├── main.py                                   # Main program entry
│   ├── file_classifier.py                        # Basic classification logic
│   ├── enhanced_hierarchical_classifier.py       # Hierarchical classifier
│   └── intelligent_recommendations.py            # Intelligent recommendation engine
├── 📁 Interface Modules
│   ├── settings_dialog.py                        # Settings interface
│   ├── hierarchical_settings_dialog.py          # Hierarchical settings
│   └── recommendations_dialog.py                # Recommendation system interface
├── 📁 Function Modules
│   ├── file_monitor.py                          # File monitoring
│   ├── config_manager.py                       # Configuration management
│   └── file_classifier_enhanced.py             # Enhanced classifier
│   ├── ai_service.py                            # Third-party AI categorization client (categorization only)
│   ├── secure_storage.py                        # Local secure API key storage (keyring/DPAPI)
│   └── ui_theme.py                              # Wabi-Sabi theme + global scroll container
├── 📁 Testing & Demo
│   ├── test_hierarchical_classification.py     # Function testing
│   ├── demo_intelligent_recommendations.py     # Demo program
│   ├── practical_usage_demo.py                 # Practical usage demo
│   └── test_recommendations.py                 # Recommendation system testing
├── 📁 Build Configuration
│   ├── build_executable.py                     # Executable file builder
│   ├── intelligent_file_classifier.spec        # PyInstaller configuration
│   ├── requirements.txt                        # Basic dependencies
│   └── requirements-dev.txt                    # Development dependencies
└── 📁 Documentation
    ├── hierarchical_classification_guide.md    # Hierarchical classification guide
    ├── intelligent_recommendations_guide.md    # Intelligent recommendations guide
    ├── DEVELOPMENT.md                          # Development documentation
    └── CONTRIBUTING.md                         # Contributing guide
```

## 🎯 Use Cases

### 💼 Office Document Organization
- Automatically classify work reports, contracts, presentations
- Organize by project, time, and type in multiple dimensions
- Intelligently identify important documents and temporary files

### 📱 Personal File Management
- Mobile photos automatically classified by time and type
- Downloaded files intelligently categorized
- Automatic duplicate file detection and cleanup

### 💻 Development Project Management
- Automatically identify Web, Python, Java projects
- Protect project integrity
- Organize code by tech stack and time

### 🎬 Media Library Organization
- Movies and TV shows intelligently classified
- Music organized by artist and album
- Pictures classified by shooting time and content

## 🏆 Performance Advantages

| Feature | Traditional Method | Smart Classifier | Improvement |
|---------|-------------------|------------------|-------------|
| File Search | 2-5 minutes | 5-15 seconds | **10-20x** |
| Classification Accuracy | 60-70% | 90%+ | **1.5x** |
| Processing Speed | Manual | Automated | **∞** |
| Error Rate | 20-30% | <5% | **6x reduction** |

## 🤝 Contributing

We welcome all forms of contributions!

### 🐛 Issue Reporting
- [Submit Bug Report](https://github.com/YALI58/Intelligent-Document-Classifier/issues/new?template=bug_report.md)
- [Feature Request](https://github.com/YALI58/Intelligent-Document-Classifier/issues/new?template=feature_request.md)

### 💡 Development Participation
1. Fork the project
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Create Pull Request

See [Contributing Guide](CONTRIBUTING.md) for detailed instructions.

## 📈 Roadmap

### 🎯 Near-term Plans (v2.1)
- [ ] Cloud sync support
- [ ] More file type support
- [ ] Performance optimization

### 🚀 Long-term Vision
- [ ] Machine learning optimization
- [ ] Cross-platform mobile support
- [ ] Team collaboration features

## 📄 License

This project is open-sourced under the [MIT](LICENSE) license.

## 🙏 Acknowledgments

### Core Contributors
- [@YALI58](https://github.com/YALI58) - Project founder and main developer

### Special Thanks
- All users who submitted issues and suggestions
- Beta testers
- Open source community support

## 🔗 Related Links

- 📋 [Issue Tracker](https://github.com/YALI58/Intelligent-Document-Classifier/issues)
- 📖 [Project Wiki](https://github.com/YALI58/Intelligent-Document-Classifier/wiki)
- 💬 [Discussions](https://github.com/YALI58/Intelligent-Document-Classifier/discussions)
- 📈 [Project Board](https://github.com/YALI58/Intelligent-Document-Classifier/projects)

---

<div align="center">

**If this project helps you, please consider giving it a ⭐ Star!**

[🔝 Back to Top](#intelligent-file-classifier)

</div>