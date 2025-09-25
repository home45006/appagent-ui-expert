# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述
这是一个用于分析Android UI XML文件的工具，主要用于移动应用自动化测试和UI元素分析。项目包含一个主要的Python脚本，用于生成HTML格式的可视化标注文件。

## 常用命令

### 生成HTML标注文件
```bash
python xml_html_annotator.py <xml_file> --screenshot <image_file>
```
生成HTML文件，在浏览器中显示标注效果。

## 项目架构

### 核心数据结构
- **Bounds**: 表示UI元素的边界框 (left, top, right, bottom)
- **UIElement**: 表示一个UI元素，包含节点ID、类名、文本、描述、资源ID、边界框等属性

### 主要模块

**xml_html_annotator.py**: HTML标注生成器
- 解析XML文件
- 生成带标注的HTML文件
- 支持截图叠加显示

### 目录结构
- `ui-xml/`: 存放输入的XML文件和对应的截图
- `result/`: 存放生成的分析结果和标注文件
- `*.py`: Python脚本文件
- `*.txt`: 分析报告文件

## 技术特点

### XML处理
- 使用 `xml.etree.ElementTree` 解析Android UI布局文件
- 支持处理带有命名空间的XML文件
- 提取UI元素的属性和边界框信息

### 图像处理
- 支持截图与XML坐标的对应关系
- 生成HTML格式的可视化标注

## 开发注意事项

- 所有代码使用Python 3编写
- 使用标准库，无需额外依赖
- 支持中文界面和输出
- 文件编码统一使用UTF-8