# Android UI XML 分析工具集

这是一个用于分析Android UI XML文件的工具集，主要用于移动应用自动化测试和UI元素分析。

## 项目概述

本项目包含多个Python脚本，用于处理、验证和标注Android界面布局XML文件，支持坐标验证、文件对比、可视化标注等功能。

## 功能模块

### 核心工具
- **coordinate_validator.py** - 坐标验证工具
- **correction_validator.py** - 坐标修正验证工具
- **xml_comparator.py** - XML文件对比分析工具
- **xml_html_annotator.py** - HTML标注生成器
- **xml_screenshot_analyzer.py** - XML与截图对比分析工具
- **xml_visual_annotator.py** - 可视化标注工具

## 文件依赖关系分析

### 当前依赖结构

**特点：**
- ✅ **无循环依赖**
- ✅ **每个文件都可以独立运行**
- ✅ **第三方库依赖极少（只有Pillow）**

**问题：**
- ❌ **存在大量代码重复**
- ❌ **缺乏模块化设计**
- ❌ **维护成本高（修改需要在多个文件中同步）**

### 具体依赖情况

```python
# 所有文件的依赖关系
coordinate_validator.py     # 独立脚本，无本地依赖
├── 标准库：xml.etree.ElementTree, re

correction_validator.py      # 独立脚本，无本地依赖
├── 无外部依赖

xml_comparator.py           # 独立脚本，无本地依赖
├── 标准库：xml.etree.ElementTree, typing, dataclass, argparse, re

xml_html_annotator.py       # 独立脚本，无本地依赖
├── 标准库：xml.etree.ElementTree, typing, dataclass, argparse, json, base64

xml_screenshot_analyzer.py  # 独立脚本，无本地依赖
├── 标准库：xml.etree.ElementTree, re, typing, dataclass, argparse
├── 第三方库：Pillow

xml_visual_annotator.py     # 独立脚本，无本地依赖
├── 标准库：xml.etree.ElementTree, typing, dataclass, argparse, sys
```

### 代码重复问题

项目中存在大量重复的代码：
- `Bounds` 类定义在多个文件中重复
- `UIElement` 类定义在多个文件中重复
- XML解析逻辑在多个文件中重复
- 坐标处理函数在多个文件中重复

## 使用方法

### 基本命令
```bash
# 坐标验证
python coordinate_validator.py <xml_file>

# XML对比分析
python xml_comparator.py <xml_file1> <xml_file2>

# 生成HTML标注
python xml_html_annotator.py <xml_file> --screenshot <image_file>

# XML与截图对比分析
python xml_screenshot_analyzer.py <xml_file> <screenshot_file>

# 可视化标注
python xml_visual_annotator.py <xml_file> <screenshot_file> --output <output_file>

# 坐标修正验证
python correction_validator.py
```

## 目录结构
```
├── ui-xml/          # 输入文件（XML和截图）
├── result/          # 生成结果和标注文件
├── *.py            # Python脚本文件
├── *.txt           # 分析报告文件
└── README.md       # 项目文档
```

## 技术栈
- **Python 3** - 主要编程语言
- **xml.etree.ElementTree** - XML解析
- **Pillow** - 图像处理（仅在xml_screenshot_analyzer.py中使用）
- **标准库** - argparse, re, typing, dataclass, json, base64等

## 改进建议

### 模块化重构
建议创建共享的核心模块来减少代码重复：

```
common/
├── bounds.py          # Bounds类定义
├── ui_element.py      # UIElement类定义
├── xml_parser.py      # XML解析工具
└── coordinate_utils.py # 坐标处理工具
```

### 重构优势
1. **减少代码重复** - 公共功能统一管理
2. **提高可维护性** - 修改一处即可影响所有使用模块
3. **增强一致性** - 确保相同功能在各处的实现一致
4. **便于测试** - 共享模块可以独立测试

## 注意事项

- 所有脚本都设计为独立运行，无需安装额外依赖（除Pillow外）
- 文件编码统一使用UTF-8
- 支持中文界面和输出
- 坐标系统基于Android屏幕坐标系