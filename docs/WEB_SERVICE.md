# Web版XML标注器使用指南

本文档说明如何使用Web版的XML UI元素标注分析工具。

## 🚀 快速开始

### 1. 启动Web服务

```bash
# 方法1: 使用启动脚本（推荐）
python3 start_web_service.py

# 方法2: 直接运行Flask应用
python3 web_annotator.py
```

### 2. 访问Web界面

打开浏览器访问：`http://localhost:5000`

### 3. 使用工具

- **文件上传**：将XML和图片文件上传到`ui-xml`文件夹
- **文件选择**：在Web界面选择要处理的文件对
- **生成标注**：点击"生成标注"按钮
- **查看结果**：在浏览器中查看或下载标注结果

## 📋 功能特性

### 🌐 Web界面功能
- **文件管理**：上传、浏览、选择文件
- **拖拽上传**：支持拖拽文件到上传区域
- **自动匹配**：自动为XML文件查找对应图片
- **进度显示**：实时显示处理进度
- **结果管理**：查看、下载、删除结果文件

### 🔧 API接口
- `GET /api/files` - 获取可用文件列表
- `POST /api/upload` - 上传文件
- `POST /api/generate` - 生成标注文件
- `GET /api/task/<task_id>` - 获取任务状态
- `GET /api/results` - 获取结果文件列表
- `GET /api/result/<filename>` - 下载结果文件
- `DELETE /api/result/<filename>` - 删除结果文件
- `GET /api/match` - 查找匹配文件
- `GET /view/<filename>` - 在线查看结果

### 🎯 智能功能
- **文件匹配**：自动查找同名的XML和图片文件
- **后台处理**：异步处理任务，不阻塞界面
- **状态监控**：实时监控处理进度和状态
- **错误处理**：完善的错误提示和处理机制

## 📁 目录结构

```
appagent-ui-expert/
├── web_annotator.py           # Web应用主文件
├── start_web_service.py      # 启动脚本
├── templates/
│   └── index.html           # Web界面模板
├── ui-xml/                   # 文件上传目录
├── result/                   # 结果文件目录
├── xml_html_annotator.py     # 标注生成器
├── ocr_processor.py          # OCR处理器
└── requirements.txt          # Python依赖
```

## 🔧 安装依赖

### 方法1: 自动安装（推荐）
```bash
python3 start_web_service.py
# 脚本会自动检查并安装缺少的依赖
```

### 方法2: 手动安装
```bash
# 安装基础依赖
pip install flask pillow

# 安装OCR引擎（可选）
pip install pytesseract          # Tesseract OCR
pip install easyocr             # EasyOCR
pip install paddlepaddle paddleocr  # PaddleOCR
```

## 📖 详细使用说明

### 文件准备

1. **文件命名**：建议XML文件和图片文件使用相同的基础名
   ```
   example.xml
   example.jpg
   ```

2. **支持的格式**：
   - XML文件：`.xml`
   - 图片文件：`.jpg`, `.jpeg`, `.png`

3. **文件大小限制**：单个文件最大50MB

### Web界面操作

#### 1. 文件上传
- 点击上传区域选择文件
- 或直接拖拽文件到上传区域
- 支持批量上传多个文件

#### 2. 文件选择
- 在XML文件列表中点击选择XML文件
- 系统会自动查找并高亮对应的图片文件
- 也可以手动选择图片文件

#### 3. 生成标注
- 确保已选择XML文件和图片文件
- 点击"生成标注"按钮
- 等待处理完成（进度条会显示处理进度）

#### 4. 查看结果
- 处理完成后，结果会显示在右侧面板
- 点击"查看"按钮在浏览器中打开标注
- 点击"下载"按钮保存到本地
- 点击"删除"按钮删除结果文件

### 标注文件特性

生成的HTML标注文件包含：
- 📱 **XML元素标注**：红色边框标注XML解析的UI元素
- 🔤 **OCR文字标注**：橙色边框标注OCR识别的文字内容
- 📊 **统计信息**：显示各类元素的统计数据
- 🎛️ **交互控制**：可控制不同类型标注的显示/隐藏
- 🖱️ **点击交互**：支持标注与列表项的双向交互

## 🛠️ 高级功能

### API使用示例

```python
import requests

# 获取文件列表
response = requests.get('http://localhost:5000/api/files')
files = response.json()

# 上传文件
with open('example.xml', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:5000/api/upload', files=files)

# 生成标注
data = {
    'xml_file': 'example.xml',
    'image_file': 'example.jpg'
}
response = requests.post('http://localhost:5000/api/generate', json=data)
task_id = response.json()['task_id']

# 监控进度
response = requests.get(f'http://localhost:5000/api/task/{task_id}')
status = response.json()
```

### 配置选项

在`web_annotator.py`中可以修改以下配置：

```python
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 文件大小限制
UPLOAD_FOLDER = 'ui-xml'                              # 上传目录
RESULT_FOLDER = 'result'                              # 结果目录
```

## 🔍 故障排除

### 常见问题

#### 1. 端口被占用
```bash
Error: [Errno 98] Address already in use
```
**解决方案**：
- 修改`web_annotator.py`中的端口号
- 或停止占用端口的程序：`lsof -ti:5000 | xargs kill -9`

#### 2. 文件上传失败
```bash
413 Request Entity Too Large
```
**解决方案**：
- 减小文件大小
- 或修改`MAX_CONTENT_LENGTH`配置

#### 3. OCR功能不可用
```bash
没有可用的OCR引擎
```
**解决方案**：
- 安装OCR引擎（参考`OCR_INSTALLATION.md`）
- 或在没有OCR引擎的情况下，系统会跳过OCR功能

#### 4. 模板文件不存在
```bash
jinja2.exceptions.TemplateNotFound
```
**解决方案**：
- 确保`templates/index.html`文件存在
- 检查文件路径是否正确

### 性能优化

#### 1. 大文件处理
- 使用较小的图片文件（建议小于5MB）
- 图片分辨率建议不超过1920x1080

#### 2. 并发处理
- 当前版本支持同时处理多个任务
- 建议避免同时生成大量标注文件

#### 3. 内存管理
- 处理完成后及时清理结果文件
- 定期清理`result`目录

## 📝 更新日志

### v1.0.0 (2024-01-XX)
- ✨ 初始版本发布
- 🌐 Web界面功能
- 📁 文件上传和管理
- 🔤 集成OCR文字识别
- 🎯 智能文件匹配
- 📊 结果管理和预览

## 🤝 技术支持

如有问题或建议，请：
1. 检查本文档的故障排除部分
2. 查看控制台输出的错误信息
3. 确保Python版本≥3.6
4. 确保所有依赖已正确安装

---

**享受使用Web版XML标注器！** 🎉