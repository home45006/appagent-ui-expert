#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一启动脚本
支持命令行和Web版本
"""

import os
import sys
import argparse
import socket
import subprocess

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))

def find_available_port(start_port=5000, max_attempts=10):
    """查找可用端口"""
    for port in range(start_port, start_port + max_attempts):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            result = sock.connect_ex(('localhost', port))
            sock.close()
            if result != 0:  # 端口可用
                return port
        except:
            pass
    return start_port

def run_web_server(args):
    """启动Web服务器"""
    print("🚀 启动Web版XML标注器")
    print("=" * 50)

    # 检查依赖
    try:
        import flask
        print("✅ Flask 已安装")
    except ImportError:
        print("❌ Flask 未安装，正在安装...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'flask'])

    try:
        from PIL import Image
        print("✅ Pillow 已安装")
    except ImportError:
        print("❌ Pillow 未安装，正在安装...")
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pillow'])

    # 检查目录
    os.makedirs('../ui-xml', exist_ok=True)
    os.makedirs('../result', exist_ok=True)
    print("✅ 目录检查完成")

    # 查找可用端口
    port = args.port or find_available_port()
    print(f"🌐 使用端口: {port}")

    # 启动服务
    try:
        # 添加src目录到路径并导入
        sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), 'src'))
        from web_annotator import app
        print(f"\n🌐 启动Web服务...")
        print(f"📍 本地访问: http://localhost:{port}")
        print(f"🌍 网络访问: http://0.0.0.0:{port}")
        print(f"⏹️  按 Ctrl+C 停止服务")
        print("-" * 50)

        app.run(
            host='0.0.0.0',
            port=port,
            debug=args.debug,
            threaded=True,
            use_reloader=False
        )
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        sys.exit(1)

def run_command_line(args):
    """运行命令行版本"""
    print("🚀 启动命令行版XML标注器")
    print("=" * 50)

    # 检查参数
    if not args.xml_file or not args.image_file:
        print("❌ 请指定XML文件和图片文件")
        print("用法: python run.py cli --xml <xml_file> --image <image_file> [--output <output_file>]")
        sys.exit(1)

    # 构建文件路径
    xml_path = os.path.join('../ui-xml', args.xml_file)
    image_path = os.path.join('../ui-xml', args.image_file)

    if not os.path.exists(xml_path):
        print(f"❌ XML文件不存在: {xml_path}")
        sys.exit(1)

    if not os.path.exists(image_path):
        print(f"❌ 图片文件不存在: {image_path}")
        sys.exit(1)

    # 生成输出文件名
    if args.output:
        output_path = os.path.join('../result', args.output)
    else:
        base_name = os.path.splitext(args.xml_file)[0]
        output_path = os.path.join('../result', f"{base_name}_annotated.html")

    # 确保结果目录存在
    os.makedirs('../result', exist_ok=True)

    try:
        from xml_html_annotator import XMLHTMLAnnotator
        print(f"📄 XML文件: {xml_path}")
        print(f"🖼️  图片文件: {image_path}")
        print(f"📁 输出文件: {output_path}")
        print("-" * 30)

        annotator = XMLHTMLAnnotator(xml_path)
        annotator.generate_html_annotation(image_path, output_path)

        print(f"✅ 标注文件已生成: {output_path}")
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        sys.exit(1)

def run_ocr_test(args):
    """测试OCR功能"""
    print("🔤 测试OCR文字识别")
    print("=" * 50)

    if not args.image_file:
        print("❌ 请指定图片文件")
        print("用法: python run.py ocr --image <image_file> [--output <output_file>]")
        sys.exit(1)

    image_path = os.path.join('../ui-xml', args.image_file)

    if not os.path.exists(image_path):
        print(f"❌ 图片文件不存在: {image_path}")
        sys.exit(1)

    try:
        from ocr_processor import OCRProcessor
        print(f"🖼️  图片文件: {image_path}")
        print("-" * 30)

        ocr = OCRProcessor()
        text_blocks = ocr.process_image(image_path, args.engine)

        print(f"✅ 识别出 {len(text_blocks)} 个文字块")
        print("-" * 30)

        for i, block in enumerate(text_blocks):
            print(f"{i+1}. {block.text}")
            print(f"   置信度: {block.confidence:.1%}")
            print(f"   位置: ({block.bounds.left}, {block.bounds.top}) - ({block.bounds.right}, {block.bounds.bottom})")
            print()

        # 保存结果
        if args.output:
            import json
            output_path = os.path.join('../result', args.output)
            os.makedirs('../result', exist_ok=True)

            result_data = {
                'engine': args.engine,
                'total_blocks': len(text_blocks),
                'text_blocks': [
                    {
                        'text': block.text,
                        'confidence': block.confidence,
                        'bounds': {
                            'left': block.bounds.left,
                            'top': block.bounds.top,
                            'right': block.bounds.right,
                            'bottom': block.bounds.bottom
                        }
                    }
                    for block in text_blocks
                ]
            }

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            print(f"✅ 结果已保存到: {output_path}")

    except Exception as e:
        print(f"❌ OCR测试失败: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='XML UI元素标注分析工具')
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # Web服务器
    web_parser = subparsers.add_parser('web', help='启动Web服务器')
    web_parser.add_argument('--port', type=int, help='端口号')
    web_parser.add_argument('--debug', action='store_true', help='调试模式')
    web_parser.set_defaults(func=run_web_server)

    # 命令行版本
    cli_parser = subparsers.add_parser('cli', help='命令行版本')
    cli_parser.add_argument('--xml', required=True, dest='xml_file', help='XML文件名')
    cli_parser.add_argument('--image', required=True, dest='image_file', help='图片文件名')
    cli_parser.add_argument('--output', help='输出文件名')
    cli_parser.set_defaults(func=run_command_line)

    # OCR测试
    ocr_parser = subparsers.add_parser('ocr', help='OCR文字识别测试')
    ocr_parser.add_argument('--image', required=True, dest='image_file', help='图片文件名')
    ocr_parser.add_argument('--output', help='输出JSON文件名')
    ocr_parser.add_argument('--engine', choices=['auto', 'tesseract', 'easyocr', 'paddleocr'],
                           default='auto', help='OCR引擎')
    ocr_parser.set_defaults(func=run_ocr_test)

    # 默认启动Web服务器
    if len(sys.argv) == 1:
        args = parser.parse_args(['web'])
    else:
        args = parser.parse_args()

    # 执行对应的功能
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()