# OCR文字识别功能安装指南

本文档说明如何安装OCR功能所需的依赖库。

## 支持的OCR引擎

本项目支持以下三种OCR引擎，可以根据需要选择安装：

### 1. Tesseract OCR (推荐)

```bash
# Ubuntu/Debian系统
sudo apt update
sudo apt install tesseract-ocr tesseract-ocr-chi-sim tesseract-ocr-chi-tra

# CentOS/RHEL系统
sudo yum install tesseract tesseract-langpack-chi_sim tesseract-langpack-chi_tra

# 安装Python库
pip install pytesseract pillow
```

### 2. EasyOCR (简单易用)

```bash
# 安装Python库
pip install easyocr
```

EasyOCR会自动下载所需模型，第一次使用时会下载中文和英文模型。

### 3. PaddleOCR (百度飞桨OCR，精度高)

```bash
# 安装Python库
pip install paddlepaddle paddleocr
```

PaddleOCR也会自动下载模型文件。

## 推荐安装方案

### 方案一：只安装Tesseract (轻量级)
```bash
sudo apt install tesseract-ocr tesseract-ocr-chi-sim
pip install pytesseract pillow
```

### 方案二：安装EasyOCR (开箱即用)
```bash
pip install easyocr
```

### 方案三：安装全部引擎 (功能最全)
```bash
sudo apt install tesseract-ocr tesseract-ocr-chi-sim
pip install pytesseract pillow easyocr paddlepaddle paddleocr
```

## 使用方法

### 测试OCR功能

```bash
# 测试单个图片
python3 ocr_processor.py ui-xml/1754975278926.jpg --output result/ocr_test.json

# 查看OCR结果
cat result/ocr_test.json
```

### 在XML标注中使用OCR

```bash
# 生成带OCR标注的HTML文件
python3 xml_html_annotator.py ui-xml/1754975278926.xml ui-xml/1754975278926.jpg result/test_with_ocr.html
```

## 功能特点

1. **多引擎支持**：自动选择最佳可用的OCR引擎
2. **智能合并**：自动合并相邻的文字块
3. **XML匹配**：将OCR识别的文字与XML元素进行智能匹配
4. **可视化标注**：在HTML中用不同颜色标注OCR识别结果
5. **交互功能**：支持点击交互和高亮显示

## 注意事项

1. 首次使用OCR引擎时，可能需要下载模型文件，请确保网络连接正常
2. 中文识别需要安装中文语言包
3. OCR识别需要一定的时间，请耐心等待
4. 图片质量和清晰度会影响OCR识别准确率

## 故障排除

### 问题：没有找到可用的OCR引擎
**解决方案**：按照上述安装方法安装至少一个OCR引擎

### 问题：OCR识别准确率低
**解决方案**：
1. 确保图片清晰度高
2. 检查是否安装了中文语言包
3. 尝试使用不同的OCR引擎

### 问题：模型下载失败
**解决方案**：
1. 检查网络连接
2. 设置代理（如果需要）
3. 手动下载模型文件并放到指定目录