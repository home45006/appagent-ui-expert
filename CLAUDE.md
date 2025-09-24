# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述
这是一个用于分析Android UI XML文件的工具集，主要用于移动应用自动化测试和UI元素分析。项目包含多个Python脚本，用于处理、验证和标注Android界面布局XML文件。

## 常用命令

### 运行坐标验证工具
```bash
python coordinate_validator.py <xml_file>
```
验证XML中关键元素的坐标是否正确。

### 运行XML对比分析
```bash
python xml_comparator.py <xml_file1> <xml_file2>
```
对比两个不同时间点的XML文件，分析页面状态变化。

### 生成HTML标注文件
```bash
python xml_html_annotator.py <xml_file> --screenshot <image_file>
```
生成HTML文件，在浏览器中显示标注效果。

### XML与截图对比分析
```bash
python xml_screenshot_analyzer.py <xml_file> <screenshot_file>
```
分析XML中哪些元素在截图可见区域内。

### 在截图上标注UI元素
```bash
python xml_visual_annotator.py <xml_file> <screenshot_file> --output <output_file>
```
在截图上用红框标示出可见区域的UI元素。

### 坐标修正验证
```bash
python correction_validator.py
```
验证Y坐标修正是否正确。

## 项目架构

### 核心数据结构
- **Bounds**: 表示UI元素的边界框 (left, top, right, bottom)
- **UIElement**: 表示一个UI元素，包含节点ID、类名、文本、描述、资源ID、边界框等属性

### 主要模块

1. **coordinate_validator.py**: 坐标验证工具
   - 提取关键元素的坐标信息
   - 验证坐标的合理性
   - 生成验证报告

2. **xml_comparator.py**: XML文件对比分析工具
   - 解析两个XML文件
   - 比较UI元素的变化
   - 识别新增、删除、修改的元素

3. **xml_html_annotator.py**: HTML标注生成器
   - 解析XML文件
   - 生成带标注的HTML文件
   - 支持截图叠加显示

4. **xml_screenshot_analyzer.py**: XML与截图对比分析
   - 分析XML元素在截图中的可见性
   - 计算可见区域比例
   - 生成可见性报告

5. **xml_visual_annotator.py**: 可视化标注工具
   - 在截图上绘制UI元素边界框
   - 生成标注后的图像文件

6. **correction_validator.py**: 坐标修正验证工具
   - 验证坐标修正的正确性
   - 生成修正报告

### 目录结构
- `ui-xml/`: 存放输入的XML文件和对应的截图
- `result/`: 存放生成的分析结果和标注文件
- `*.py`: 主要的Python脚本文件
- `*.txt`: 分析报告文件

## 技术特点

### XML处理
- 使用 `xml.etree.ElementTree` 解析Android UI布局文件
- 支持处理带有命名空间的XML文件
- 提取UI元素的属性和边界框信息

### 图像处理
- 支持截图与XML坐标的对应关系
- 可在截图上绘制UI元素边界框
- 生成HTML格式的可视化标注

### 坐标系统
- 处理Android屏幕坐标系统
- 支持坐标修正和验证
- 计算UI元素的尺寸和位置关系

## 开发注意事项

- 所有代码使用Python 3编写
- 使用标准库，无需额外依赖
- 支持中文界面和输出
- 文件编码统一使用UTF-8