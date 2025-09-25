# XML UI元素标注分析工具 (含OCR文字识别功能)

一个用于分析Android UI XML文件的工具，主要用于移动应用自动化测试和UI元素分析。集成了智能OCR文字识别功能，支持命令行和Web版两种使用方式。

## 🚀 快速开始

### 方法1：便捷启动（推荐）
```bash
python start.py
```

### 方法2：使用脚本
```bash
python scripts/run.py web
```

### 方法3：命令行使用
```bash
python scripts/run.py cli --xml example.xml --image example.jpg
```

## 📋 功能特性

### 🎯 核心功能
- 📱 **XML元素分析** - 解析Android UI布局文件
- 🔤 **OCR文字识别** - 智能识别图片中的文字
- 🎨 **可视化标注** - 生成HTML格式的标注文件
- 🖱️ **交互功能** - 支持点击交互和高亮显示

### 🌐 Web版特性
- 🖥️ **图形界面** - 现代化的Web操作界面
- 📁 **文件管理** - 拖拽上传和文件浏览
- 🔄 **实时反馈** - 进度显示和状态监控
- 📊 **结果管理** - 查看、下载、删除结果

### 💻 命令行特性
- ⚡ **快速处理** - 适合批量操作和自动化
- 🎛️ **灵活配置** - 支持多种参数配置
- 🔧 **易于集成** - 可集成到其他工作流

## 📁 项目结构

```
appagent-ui-expert/
├── src/                          # 源代码
│   ├── xml_html_annotator.py      # 主标注生成器
│   ├── ocr_processor.py           # OCR处理器
│   ├── web_annotator.py           # Web应用
│   ├── templates/                 # Web模板
│   │   └── index.html            # Web界面
│   └── requirements.txt          # Python依赖
├── scripts/                       # 脚本文件
│   └── run.py                     # 统一启动脚本
├── docs/                          # 文档
│   ├── README.md                  # 详细文档
│   ├── OCR_INSTALLATION.md        # OCR安装指南
│   └── WEB_SERVICE.md            # Web服务指南
├── ui-xml/                       # 输入文件
├── result/                        # 输出结果
├── start.py                       # 便捷启动脚本
├── CLAUDE.md                     # Claude配置
└── README.md                      # 项目说明
```

## 🛠️ 安装依赖

### 自动安装（推荐）
```bash
python start.py
# 脚本会自动检查并安装依赖
```

### 手动安装
```bash
pip install flask pillow

# 可选：安装OCR引擎
pip install pytesseract          # Tesseract OCR
pip install easyocr             # EasyOCR
pip install paddlepaddle paddleocr  # PaddleOCR
```

## 📖 使用说明

### 🌐 Web版本

1. **启动服务**
   ```bash
   python start.py
   ```

2. **访问界面**
   - 浏览器打开：`http://localhost:5000`
   - 或网络访问：`http://your-ip:5000`

3. **使用功能**
   - 上传XML和图片文件到`ui-xml`目录
   - 在Web界面选择文件对
   - 点击"生成标注"
   - 查看和下载结果

### 💻 命令行版本

1. **基本使用**
   ```bash
   python scripts/run.py cli --xml example.xml --image example.jpg
   ```

2. **指定输出文件**
   ```bash
   python scripts/run.py cli --xml example.xml --image example.jpg --output result.html
   ```

### 🔤 OCR测试

```bash
# 测试OCR功能
python scripts/run.py ocr --image example.jpg

# 使用指定引擎
python scripts/run.py ocr --image example.jpg --engine tesseract

# 保存结果到JSON
python scripts/run.py ocr --image example.jpg --output ocr_result.json
```

## 🎯 高级功能

### API接口

Web版提供RESTful API：

```python
import requests

# 获取文件列表
response = requests.get('http://localhost:5000/api/files')

# 上传文件
with open('example.xml', 'rb') as f:
    files = {'file': f}
    response = requests.post('http://localhost:5000/api/upload', files=files)

# 生成标注
data = {'xml_file': 'example.xml', 'image_file': 'example.jpg'}
response = requests.post('http://localhost:5000/api/generate', json=data)
```

### 配置选项

#### Web服务配置
```bash
# 指定端口
python start.py --port 8080

# 调试模式
python start.py --debug
```

#### OCR引擎配置
- **Tesseract**: 准确率高，轻量级
- **EasyOCR**: 易于使用，开箱即用
- **PaddleOCR**: 百度飞桨，精度最佳

## 📊 输出文件特性

生成的HTML标注文件包含：

- 📱 **XML元素标注** - 红色边框标注XML解析的UI元素
- 🔤 **OCR文字标注** - 橙色边框标注OCR识别的文字内容
- 📊 **统计信息** - 显示坐标元素、可见区域、OCR文字块等统计
- 🎛️ **交互控制** - 可控制不同类型标注的显示/隐藏
- 🖱️ **点击交互** - 支持标注与列表项的双向交互

## 🔧 故障排除

### 常见问题

1. **端口被占用**
   ```bash
   # 使用其他端口
   python start.py --port 5001
   ```

2. **OCR功能不可用**
   ```bash
   # 安装OCR引擎
   pip install pytesseract
   ```

3. **WSL网络问题**
   ```bash
   # 在WSL中启动
   python start.py

   # 在Windows浏览器访问
   # http://localhost:5000 或 http://WSL_IP:5000
   ```

### 性能优化

- 图片建议小于5MB，分辨率不超过1920x1080
- 定期清理`result`目录
- 使用SSD提高I/O性能

## 📚 相关文档

- [详细使用指南](docs/README.md)
- [OCR安装指南](docs/OCR_INSTALLATION.md)
- [Web服务指南](docs/WEB_SERVICE.md)
- [Claude配置](CLAUDE.md)

## 🤝 技术支持

如有问题，请检查：
1. 确保Python版本≥3.6
2. 检查依赖是否正确安装
3. 查看控制台错误信息
4. 参考相关文档

---

**享受使用XML标注器！** 🎉