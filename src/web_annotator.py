#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Web版XML标注器
提供Web界面进行文件选择和标注生成
"""

import os
import json
import shutil
from flask import Flask, render_template, request, jsonify, send_file, flash, redirect, url_for
from werkzeug.utils import secure_filename
from datetime import datetime
import threading
import glob
from typing import List, Dict, Tuple
from xml_html_annotator import XMLHTMLAnnotator
from ocr_processor import OCRProcessor

app = Flask(__name__)
app.secret_key = 'xml_annotator_secret_key'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# 配置 - 使用绝对路径
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'ui-xml')
RESULT_FOLDER = os.path.join(BASE_DIR, 'result')
ALLOWED_EXTENSIONS = {'xml', 'jpg', 'jpeg', 'png'}

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

class WebAnnotatorService:
    """Web标注服务类"""

    def __init__(self):
        self.upload_folder = UPLOAD_FOLDER
        self.result_folder = RESULT_FOLDER
        self.processing_tasks = {}  # 存储处理任务状态

    def get_available_files(self) -> Dict[str, List[str]]:
        """获取可用的XML和图片文件"""
        xml_files = []
        image_files = []

        # 获取XML文件
        for file in os.listdir(self.upload_folder):
            if file.lower().endswith('.xml'):
                xml_files.append(file)

        # 获取图片文件
        for file in os.listdir(self.upload_folder):
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                image_files.append(file)

        return {
            'xml_files': sorted(xml_files),
            'image_files': sorted(image_files)
        }

    def find_matching_image(self, xml_filename: str) -> str:
        """为XML文件查找对应的图片文件"""
        base_name = os.path.splitext(xml_filename)[0]

        # 常见的图片扩展名
        extensions = ['.jpg', '.jpeg', '.png']

        for ext in extensions:
            possible_image = f"{base_name}{ext}"
            if os.path.exists(os.path.join(self.upload_folder, possible_image)):
                return possible_image

        return ""

    def find_matching_xml(self, image_filename: str) -> str:
        """为图片文件查找对应的XML文件"""
        base_name = os.path.splitext(image_filename)[0]
        possible_xml = f"{base_name}.xml"

        if os.path.exists(os.path.join(self.upload_folder, possible_xml)):
            return possible_xml

        return ""

    def generate_annotation(self, xml_file: str, image_file: str, task_id: str) -> str:
        """生成标注文件"""
        try:
            xml_path = os.path.join(self.upload_folder, xml_file)
            image_path = os.path.join(self.upload_folder, image_file)

            # 生成输出文件名
            base_name = os.path.splitext(xml_file)[0]
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"{base_name}_annotated_{timestamp}.html"
            output_path = os.path.join(self.result_folder, output_filename)

            # 更新任务状态
            self.processing_tasks[task_id]['status'] = 'processing'
            self.processing_tasks[task_id]['message'] = '正在生成标注文件...'

            # 执行标注
            annotator = XMLHTMLAnnotator(xml_path)
            annotator.generate_html_annotation(image_path, output_path)

            # 更新任务状态
            self.processing_tasks[task_id]['status'] = 'completed'
            self.processing_tasks[task_id]['result_file'] = output_filename
            self.processing_tasks[task_id]['message'] = '标注文件生成成功'

            return output_filename

        except Exception as e:
            self.processing_tasks[task_id]['status'] = 'error'
            self.processing_tasks[task_id]['message'] = f'生成失败: {str(e)}'
            return None

    def create_task(self, xml_file: str, image_file: str) -> str:
        """创建处理任务"""
        task_id = f"task_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"

        self.processing_tasks[task_id] = {
            'xml_file': xml_file,
            'image_file': image_file,
            'status': 'pending',
            'message': '等待处理...',
            'created_at': datetime.now().isoformat(),
            'result_file': None
        }

        return task_id

    def get_task_status(self, task_id: str) -> Dict:
        """获取任务状态"""
        return self.processing_tasks.get(task_id, {})

    def get_result_files(self) -> List[Dict]:
        """获取生成的结果文件列表"""
        result_files = []

        for file in os.listdir(self.result_folder):
            if file.endswith('.html'):
                file_path = os.path.join(self.result_folder, file)
                stat = os.stat(file_path)

                result_files.append({
                    'filename': file,
                    'size': stat.st_size,
                    'created_at': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S'),
                    'modified_at': datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })

        # 按修改时间倒序排列
        return sorted(result_files, key=lambda x: x['modified_at'], reverse=True)

    def delete_result_file(self, filename: str) -> bool:
        """删除结果文件"""
        try:
            file_path = os.path.join(self.result_folder, filename)
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
        except Exception as e:
            print(f"删除文件失败: {e}")
        return False

# 创建服务实例
service = WebAnnotatorService()

def allowed_file(filename: str) -> bool:
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/files')
def get_files():
    """获取可用文件列表"""
    try:
        files = service.get_available_files()
        return jsonify({
            'success': True,
            'data': files
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """上传文件"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '没有选择文件'})

        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '没有选择文件'})

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            return jsonify({
                'success': True,
                'message': f'文件 {filename} 上传成功',
                'filename': filename
            })
        else:
            return jsonify({'success': False, 'error': '不支持的文件类型'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def generate_annotation():
    """生成标注文件"""
    try:
        data = request.get_json()
        xml_file = data.get('xml_file')
        image_file = data.get('image_file')

        if not xml_file or not image_file:
            return jsonify({'success': False, 'error': '请选择XML文件和图片文件'})

        # 检查文件是否存在
        xml_path = os.path.join(service.upload_folder, xml_file)
        image_path = os.path.join(service.upload_folder, image_file)

        if not os.path.exists(xml_path):
            return jsonify({'success': False, 'error': f'XML文件 {xml_file} 不存在'})

        if not os.path.exists(image_path):
            return jsonify({'success': False, 'error': f'图片文件 {image_file} 不存在'})

        # 创建任务
        task_id = service.create_task(xml_file, image_file)

        # 在后台线程中执行任务
        def run_task():
            service.generate_annotation(xml_file, image_file, task_id)

        thread = threading.Thread(target=run_task)
        thread.daemon = True
        thread.start()

        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': '任务已创建，正在处理中...'
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/task/<task_id>')
def get_task_status(task_id):
    """获取任务状态"""
    try:
        task = service.get_task_status(task_id)
        if not task:
            return jsonify({'success': False, 'error': '任务不存在'}), 404

        return jsonify({
            'success': True,
            'data': task
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/results')
def get_results():
    """获取结果文件列表"""
    try:
        results = service.get_result_files()
        return jsonify({
            'success': True,
            'data': results
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/result/<filename>')
def download_result(filename):
    """下载结果文件"""
    try:
        return send_file(
            os.path.join(service.result_folder, filename),
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 404

@app.route('/api/result/<filename>', methods=['DELETE'])
def delete_result(filename):
    """删除结果文件"""
    try:
        if service.delete_result_file(filename):
            return jsonify({'success': True, 'message': '文件删除成功'})
        else:
            return jsonify({'success': False, 'error': '文件删除失败'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/match')
def find_matches():
    """查找匹配的文件"""
    try:
        filename = request.args.get('filename')
        file_type = request.args.get('type')  # 'xml' or 'image'

        if not filename or not file_type:
            return jsonify({'success': False, 'error': '参数不完整'})

        if file_type == 'xml':
            matched_image = service.find_matching_image(filename)
            return jsonify({
                'success': True,
                'matched_file': matched_image
            })
        elif file_type == 'image':
            matched_xml = service.find_matching_xml(filename)
            return jsonify({
                'success': True,
                'matched_file': matched_xml
            })
        else:
            return jsonify({'success': False, 'error': '无效的文件类型'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/view/<filename>')
def view_result(filename):
    """查看结果文件"""
    try:
        return send_file(os.path.join(service.result_folder, filename))
    except Exception as e:
        return f"文件不存在: {str(e)}", 404

if __name__ == '__main__':
    print("🚀 启动Web XML标注服务...")
    print(f"📁 上传文件夹: {os.path.abspath(UPLOAD_FOLDER)}")
    print(f"📁 结果文件夹: {os.path.abspath(RESULT_FOLDER)}")
    print("🌐 访问地址: http://localhost:5000")
    print("📖 使用说明:")
    print("   1. 将XML和图片文件放到 ui-xml/ 文件夹中")
    print("   2. 或者使用页面上的上传功能")
    print("   3. 选择文件对并生成标注")
    print("   4. 在浏览器中查看标注结果")

    app.run(debug=True, host='0.0.0.0', port=5000)