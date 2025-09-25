# Android UI XML 分析工具 (含OCR文字识别功能)

这是一个用于分析Android UI XML文件的工具，主要用于移动应用自动化测试和UI元素分析。集成了智能OCR文字识别功能，可自动识别图片中的文字并与XML元素进行匹配。**现已支持Web版操作界面！**

## 项目概述

本项目包含多个功能模块，用于生成HTML格式的可视化标注文件，支持在浏览器中查看标注效果。提供了**命令行版本**和**Web版本**两种使用方式，满足不同场景的需求。

## 功能模块

### 核心工具
- **xml_html_annotator.py** - 主标注生成器（含OCR功能）
- **ocr_processor.py** - OCR文字识别处理模块
- **web_annotator.py** - Web版标注服务
- **start_web_service.py** - Web服务启动脚本

## 使用方法

### 🌐 Web版本（推荐）

```bash
# 启动Web服务
python3 start_web_service.py

# 或直接运行
python3 web_annotator.py

# 访问Web界面
# 浏览器打开: http://localhost:5000
```

### 💻 命令行版本

```bash
# 生成HTML标注（自动包含OCR功能）
python xml_html_annotator.py <xml_file> <image_file> <output_html>

# 单独测试OCR功能
python ocr_processor.py <image_file> --output <json_file>
```

### 示例

#### Web版本示例
1. 启动服务：`python3 start_web_service.py`
2. 访问：`http://localhost:5000`
3. 上传XML和图片文件到`ui-xml`目录
4. 在Web界面选择文件对并生成标注
5. 在浏览器中查看标注结果

#### 命令行示例
```bash
# 生成带OCR标注的HTML文件
python xml_html_annotator.py ui-xml/example.xml ui-xml/example.jpg result/annotated.html

# 测试OCR文字识别
python ocr_processor.py ui-xml/example.jpg --output result/ocr_result.json
```

## OCR功能特性

### 支持的OCR引擎
1. **Tesseract OCR** - 轻量级，准确率高
2. **EasyOCR** - 易于使用，开箱即用
3. **PaddleOCR** - 百度飞桨OCR，精度最佳

### OCR功能亮点
- 🎯 **智能文字识别**：自动识别图片中的所有文字内容
- 🔤 **多引擎支持**：支持多种OCR引擎，自动选择最佳可用引擎
- 📝 **智能匹配**：将OCR识别的文字与XML元素进行智能匹配
- 🎨 **可视化标注**：在HTML中用橙色边框标注OCR识别结果
- 📊 **匹配统计**：显示OCR文字块数量和匹配成功率
- 🖱️ **交互功能**：支持点击交互和高亮显示

### 安装OCR依赖
请参考 `OCR_INSTALLATION.md` 文件了解详细的安装步骤。

## 目录结构
```
├── ui-xml/                  # 输入文件（XML和截图）
├── result/                  # 生成结果和标注文件
├── templates/               # Web界面模板
├── xml_html_annotator.py    # 主标注生成器（含OCR功能）
├── ocr_processor.py         # OCR文字识别处理模块
├── web_annotator.py         # Web版标注服务
├── start_web_service.py      # Web服务启动脚本
├── test_web_service.py      # Web服务测试脚本
├── requirements.txt         # Python依赖
├── OCR_INSTALLATION.md      # OCR安装指南
├── WEB_SERVICE.md          # Web版使用指南
├── README.md               # 项目文档
└── CLAUDE.md               # Claude代码助手配置
```

## 技术栈
- **Python 3** - 主要编程语言
- **Flask** - Web框架
- **xml.etree.ElementTree** - XML解析
- **OCR引擎** - Tesseract/EasyOCR/PaddleOCR
- **前端技术** - HTML5, CSS3, JavaScript
- **标准库** - argparse, re, typing, dataclass, json, base64等

## 注意事项

### 通用注意事项
- 基础XML标注功能无需安装额外依赖
- OCR功能需要安装对应的OCR引擎（详见安装指南）
- 文件编码统一使用UTF-8
- 支持中文界面和输出
- 坐标系统基于Android屏幕坐标系
- 首次使用OCR引擎时会自动下载模型文件

### Web版注意事项
- Web服务需要安装Flask依赖
- 支持文件拖拽上传功能
- 单个文件最大50MB
- 支持异步处理多个任务
- 提供完整的文件管理功能

### 命令行版注意事项
- 适合批量处理和自动化脚本
- 参数配置灵活
- 可集成到其他工作流中

## 输出文件特性

生成的HTML文件包含：
- 📱 **XML元素标注** - 红色边框标注XML解析的UI元素
- 🔤 **OCR文字标注** - 橙色边框标注OCR识别的文字内容
- 📊 **统计信息** - 显示坐标元素、可见区域、OCR文字块等统计
- 🎛️ **交互控制** - 可控制不同类型标注的显示/隐藏
- 🖱️ **点击交互** - 支持标注与列表项的双向交互

## 🆚 版本对比

| 功能 | Web版本 | 命令行版本 |
|------|---------|-----------|
| 使用方式 | 图形界面 | 命令行 |
| 文件管理 | 拖拽上传 | 手动放置 |
| 批量处理 | 交互式 | 脚本化 |
| 实时预览 | ✅ 支持 | ❌ 不支持 |
| 进度显示 | ✅ 可视化 | ❌ 控制台 |
| API接口 | ✅ 提供 | ❌ 不提供 |
| 依赖需求 | Flask | 标准库 |
| 适用场景 | 交互式使用 | 自动化脚本 |

## 📚 相关文档

- [OCR安装指南](OCR_INSTALLATION.md) - OCR引擎安装说明
- [Web版使用指南](WEB_SERVICE.md) - Web版详细使用方法
- [项目配置](CLAUDE.md) - Claude代码助手配置