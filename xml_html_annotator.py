#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML HTML标注程序
生成HTML文件，在浏览器中显示标注效果
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple
from dataclasses import dataclass
import argparse
import json
import base64

@dataclass
class Bounds:
    """表示UI元素的边界框"""
    left: int
    top: int
    right: int
    bottom: int

    def __post_init__(self):
        if self.left > self.right:
            self.left, self.right = self.right, self.left
        if self.top > self.bottom:
            self.top, self.bottom = self.bottom, self.top

@dataclass
class UIElement:
    """表示一个UI元素"""
    node_id: str
    class_name: str
    text: str
    content_desc: str
    resource_id: str
    bounds: Bounds
    visible_to_user: bool
    important: bool
    clickable: bool

class XMLHTMLAnnotator:
    """XML HTML标注器"""

    def __init__(self, xml_file: str):
        self.xml_file = xml_file
        self.elements = []
        self.screen_width = 0
        self.screen_height = 0
        self.parse_xml()

    def parse_xml(self):
        """解析XML文件"""
        print(f"正在解析XML文件: {self.xml_file}")

        with open(self.xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        if '<?xml' in xml_content:
            xml_content = xml_content.split('?>', 1)[1]

        root = ET.fromstring(xml_content.strip())

        # 获取屏幕尺寸
        all_elements = self._find_all_elements_xml(root)
        max_right = 0
        max_bottom = 0
        for elem in all_elements:
            bounds = self._parse_bounds(elem.get('bounds', '0 0 0 0'))
            max_right = max(max_right, bounds.right)
            max_bottom = max(max_bottom, bounds.bottom)

        self.screen_width = max_right
        self.screen_height = max_bottom

        # 解析所有UI元素
        self.elements = self._parse_all_elements(root)
        print(f"XML解析完成，屏幕尺寸: {self.screen_width}x{self.screen_height}")

    def _find_all_elements_xml(self, element: ET.Element) -> List[ET.Element]:
        """查找所有XML元素（递归）"""
        elements = [element]
        for child in element:
            elements.extend(self._find_all_elements_xml(child))
        return elements

    def _parse_bounds(self, bounds_str: str) -> Bounds:
        """解析bounds字符串"""
        if not bounds_str:
            return Bounds(0, 0, 0, 0)

        bounds_str = bounds_str.strip('"\'')
        coords = bounds_str.split()
        if len(coords) != 4:
            return Bounds(0, 0, 0, 0)

        try:
            return Bounds(
                left=int(coords[0]),
                top=int(coords[1]),
                right=int(coords[2]),
                bottom=int(coords[3])
            )
        except ValueError:
            return Bounds(0, 0, 0, 0)

    def _parse_all_elements(self, element: ET.Element) -> List[UIElement]:
        """解析所有UI元素"""
        elements = []

        # 解析当前元素
        bounds = self._parse_bounds(element.get('bounds', ''))
        ui_element = UIElement(
            node_id=element.get('source-node-id', ''),
            class_name=element.get('class', ''),
            text=element.get('text', ''),
            content_desc=element.get('content-desc', ''),
            resource_id=element.get('resource-id', ''),
            bounds=bounds,
            visible_to_user=element.get('visible-to-user', 'false').lower() == 'true',
            important=element.get('important', 'false').lower() == 'true',
            clickable=element.get('clickable', 'false').lower() == 'true'
        )
        elements.append(ui_element)

        # 递归解析子元素
        for child in element:
            elements.extend(self._parse_all_elements(child))

        return elements

    def get_visible_elements(self) -> List[UIElement]:
        """获取可见元素"""
        visible_elements = []

        for element in self.elements:
            if not element.visible_to_user:
                continue

            # 计算可见百分比
            visibility = self._calculate_visibility(element.bounds)

            if visibility >= 50:  # 50%以上可见才标注
                element.visibility_percentage = visibility
                visible_elements.append(element)

        return visible_elements

    def _calculate_visibility(self, bounds: Bounds) -> float:
        """计算元素可见百分比"""
        total_area = (bounds.right - bounds.left) * (bounds.bottom - bounds.top)
        if total_area == 0:
            return 0.0

        # 计算在屏幕内的面积
        visible_left = max(0, bounds.left)
        visible_right = min(self.screen_width, bounds.right)
        visible_top = max(0, bounds.top)
        visible_bottom = min(self.screen_height, bounds.bottom)

        if visible_right <= visible_left or visible_bottom <= visible_top:
            return 0.0

        visible_area = (visible_right - visible_left) * (visible_bottom - visible_top)
        return (visible_area / total_area) * 100

    def image_to_base64(self, image_file: str) -> str:
        """将图片转换为base64编码"""
        try:
            with open(image_file, 'rb') as f:
                return base64.b64encode(f.read()).decode()
        except:
            return ""

    def generate_html_annotation(self, image_file: str, output_file: str):
        """生成HTML标注文件"""
        print(f"正在生成HTML标注文件: {output_file}")

        # 获取可见元素
        visible_elements = self.get_visible_elements()

        # 过滤需要标注的元素
        elements_to_annotate = []
        for element in visible_elements:
            if self._should_annotate_element(element):
                elements_to_annotate.append(element)

        print(f"找到 {len(elements_to_annotate)} 个需要标注的元素")

        # 读取图片并转换为base64
        image_base64 = self.image_to_base64(image_file)

        # 生成HTML
        html_content = self._generate_html_content(image_base64, elements_to_annotate)

        # 保存HTML文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML标注文件已保存到: {output_file}")
        print(f"请在浏览器中打开: file://{output_file}")

    def _should_annotate_element(self, element: UIElement) -> bool:
        """判断是否应该标注该元素 - 基于二维码页面识别"""

        # 识别是否为二维码页面
        def is_qr_code_page():
            # 检查XML中是否包含二维码页面的关键元素
            qr_page_indicators = [
                '请使用微信扫码支付',
                '关闭'
            ]

            for indicator in qr_page_indicators:
                if any(indicator in e.text for e in self.elements if e.text):
                    return True
            return False

        # 如果不是二维码页面，则使用之前的逻辑
        if not is_qr_code_page():
            # 使用之前的通用页面逻辑
            return self._should_annotate_element_general(element)

        # 二维码页面：只标注二维码弹窗内的元素
        # 二维码弹窗区域 (基于实际分析，包含扫码提示和关闭按钮)
        qr_window_bounds = (183, 357, 499, 835)  # left, top, right, bottom

        # 检查元素是否在二维码弹窗内
        element_left = element.bounds.left
        element_top = element.bounds.top
        element_right = element.bounds.right
        element_bottom = element.bounds.bottom

        # 允许一些边距
        margin = 20
        in_qr_window = (
            element_left >= qr_window_bounds[0] - margin and
            element_top >= qr_window_bounds[1] - margin and
            element_right <= qr_window_bounds[2] + margin and
            element_bottom <= qr_window_bounds[3] + margin
        )

        if not in_qr_window:
            return False

        # 二维码弹窗内的关键元素
        qr_window_elements = [
            '请使用微信扫码支付',
            '关闭'
        ]

        # 检查是否为二维码弹窗内的元素
        element_text = element.text or ''
        element_desc = element.content_desc or ''

        for key_text in qr_window_elements:
            if key_text in element_text or key_text in element_desc:
                return True

        # 基本过滤
        skip_classes = [
            'android.widget.FrameLayout',
            'android.widget.LinearLayout',
            'android.widget.RelativeLayout',
            'android.view.ViewGroup',
            'android.view.View'
        ]

        if element.class_name in skip_classes:
            return False

        if not element.text and not element.content_desc:
            return False

        # 跳过过小的元素
        element_width = element.bounds.right - element.bounds.left
        element_height = element.bounds.bottom - element.bounds.top
        if element_width < 20 or element_height < 10:
            return False

        return False  # 二维码页面只标注关键元素

    def _should_annotate_element_general(self, element: UIElement) -> bool:
        """通用页面的元素标注逻辑"""

        # 如果是重要的元素，即使是布局类也标注
        if element.important:
            return True

        # 如果是可点击的元素，即使没有文本也标注
        if element.clickable:
            return True

        # 如果有文本内容，标注
        if element.text and element.text.strip():
            return True

        # 如果有描述内容，标注
        if element.content_desc and element.content_desc.strip():
            return True

        # 如果是特定的UI组件类型，标注
        interactive_classes = [
            'android.widget.Button',
            'android.widget.EditText',
            'android.widget.TextView',
            'android.widget.ImageButton',
            'android.widget.CheckBox',
            'android.widget.RadioButton',
            'android.widget.Spinner',
            'android.widget.ImageView'
        ]

        if element.class_name in interactive_classes:
            return True

        # 跳过明显的布局容器（但有文本或可点击的已经被上面的逻辑捕获）
        layout_classes = [
            'android.widget.FrameLayout',
            'android.widget.LinearLayout',
            'android.widget.RelativeLayout',
            'android.view.ViewGroup'
        ]

        if element.class_name in layout_classes:
            return False

        # 跳过纯View元素
        if element.class_name == 'android.view.View':
            return False

        # 跳过过小的元素
        element_width = element.bounds.right - element.bounds.left
        element_height = element.bounds.bottom - element.bounds.top
        if element_width < 5 or element_height < 3:
            return False

        # 跳过负坐标区域
        if element.bounds.left < 0:
            return False

        # 跳过滚动提示文本
        if element.text and ("可竖向滚动" in element.text or "可横向滚动" in element.text):
            return False

        # 检查是否在合理的高度范围内
        adjusted_top = element.bounds.top - 36
        if adjusted_top < 0 or adjusted_top > 1100:
            return False

        return True

    def _generate_html_content(self, image_base64: str, elements: List[UIElement]) -> str:
        """生成HTML内容"""
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XML UI元素标注</title>
    <style>
        body {{
            margin: 0;
            padding: 20px;
            font-family: Arial, sans-serif;
            background-color: #f0f0f0;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background-color: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .content {{
            padding: 20px;
        }}
        .image-container {{
            position: relative;
            display: inline-block;
            border: 1px solid #ddd;
            margin-bottom: 20px;
        }}
        .screenshot {{
            display: block;
            max-width: 100%;
            height: auto;
        }}
        .annotation {{
            position: absolute;
            border: 2px solid #e74c3c;
            background-color: rgba(231, 76, 60, 0.1);
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        .annotation:hover {{
            border-color: #c0392b;
            background-color: rgba(231, 76, 60, 0.2);
            box-shadow: 0 0 10px rgba(231, 76, 60, 0.5);
        }}
        .annotation-label {{
            position: absolute;
            background-color: #e74c3c;
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
            font-weight: bold;
            white-space: nowrap;
            z-index: 10;
            box-shadow: 0 1px 3px rgba(0,0,0,0.3);
        }}
        .stats {{
            background-color: #ecf0f1;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .stats h3 {{
            margin-top: 0;
            color: #2c3e50;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }}
        .stat-item {{
            background-color: white;
            padding: 10px;
            border-radius: 3px;
            text-align: center;
        }}
        .stat-number {{
            font-size: 24px;
            font-weight: bold;
            color: #e74c3c;
        }}
        .stat-label {{
            font-size: 12px;
            color: #7f8c8d;
        }}
        .elements-list {{
            max-height: 400px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 5px;
        }}
        .element-item {{
            padding: 10px;
            border-bottom: 1px solid #eee;
            cursor: pointer;
            transition: background-color 0.3s ease;
        }}
        .element-item:hover {{
            background-color: #f8f9fa;
        }}
        .element-item:last-child {{
            border-bottom: none;
        }}
        .element-title {{
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .element-info {{
            font-size: 12px;
            color: #7f8c8d;
        }}
        .coordinates {{
            font-family: monospace;
            background-color: #f8f9fa;
            padding: 2px 4px;
            border-radius: 3px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📱 XML UI元素标注分析</h1>
            <p>屏幕尺寸: {self.screen_width} × {self.screen_height} 像素</p>
        </div>

        <div class="content">
            <div class="stats">
                <h3>📊 统计信息</h3>
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-number">{len(elements)}</div>
                        <div class="stat-label">标注元素</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{len([e for e in elements if e.important])}</div>
                        <div class="stat-label">重要元素</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{len([e for e in elements if e.text])}</div>
                        <div class="stat-label">文本元素</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-number">{len([e for e in elements if e.clickable])}</div>
                        <div class="stat-label">可点击元素</div>
                    </div>
                </div>
            </div>

            <div class="image-container">
"""

        # 添加图片
        if image_base64:
            html += f'                <img src="data:image/jpeg;base64,{image_base64}" alt="截图" class="screenshot">'
        else:
            html += '                <div style="width: 683px; height: 1169px; background-color: #f8f9fa; display: flex; align-items: center; justify-content: center; color: #7f8c8d;">无法加载图片</div>'

        html += """

"""

        # 添加标注框
        for i, element in enumerate(elements):
            label = self._get_element_label(element)
            # 调整坐标：页面内容从Y=36开始（状态栏区域），需要减去偏移量
            status_bar_offset = 36  # 状态栏高度
            adjusted_top = element.bounds.top - status_bar_offset
            adjusted_left = element.bounds.left

            html += f"""                <div class="annotation"
                     style="left: {adjusted_left}px; top: {adjusted_top}px;
                            width: {element.bounds.right - element.bounds.left}px;
                            height: {element.bounds.bottom - element.bounds.top}px;"
                     data-element="{i}">
                    <div class="annotation-label"
                         style="left: 0px; top: -20px;">{label}</div>
                </div>
"""

        html += """
            </div>

            <h3>📋 标注元素列表</h3>
            <div class="elements-list">
"""

        # 添加元素列表
        for i, element in enumerate(elements):
            html += f"""                <div class="element-item" data-element="{i}">
                    <div class="element-title">{self._get_element_label(element)}</div>
                    <div class="element-info">
                        类型: {element.class_name}<br>
                        坐标: <span class="coordinates">{element.bounds.left},{element.bounds.top} - {element.bounds.right},{element.bounds.bottom}</span><br>
                        尺寸: {element.bounds.right - element.bounds.left} × {element.bounds.bottom - element.bounds.top}<br>
                        可见度: {getattr(element, 'visibility_percentage', 100):.1f}% |
                        重要: {'是' if element.important else '否'} |
                        可点击: {'是' if element.clickable else '否'}
                    </div>
                </div>
"""

        html += """
            </div>
        </div>
    </div>

    <script>
        // 添加交互功能
        document.addEventListener('DOMContentLoaded', function() {
            const annotations = document.querySelectorAll('.annotation');
            const elementItems = document.querySelectorAll('.element-item');

            // 点击标注框高亮对应的列表项
            annotations.forEach(annotation => {
                annotation.addEventListener('click', function() {
                    const elementId = this.getAttribute('data-element');

                    // 移除所有高亮
                    elementItems.forEach(item => item.style.backgroundColor = '');

                    // 高亮对应的列表项
                    const targetItem = document.querySelector(`.element-item[data-element="${elementId}"]`);
                    if (targetItem) {
                        targetItem.style.backgroundColor = '#fff3cd';
                        targetItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                });
            });

            // 点击列表项高亮对应的标注框
            elementItems.forEach(item => {
                item.addEventListener('click', function() {
                    const elementId = this.getAttribute('data-element');

                    // 移除所有高亮
                    elementItems.forEach(i => i.style.backgroundColor = '');
                    annotations.forEach(a => a.style.zIndex = '');

                    // 高亮对应的标注框
                    const targetAnnotation = document.querySelector(`.annotation[data-element="${elementId}"]`);
                    if (targetAnnotation) {
                        targetAnnotation.style.zIndex = '100';
                        this.style.backgroundColor = '#fff3cd';
                    }
                });
            });
        });
    </script>
</body>
</html>
"""

        return html

    def _get_element_label(self, element: UIElement) -> str:
        """获取元素的标签文本"""
        # 优先使用文本内容
        if element.text and element.text.strip():
            return element.text.strip()[:20]

        # 其次使用描述
        if element.content_desc and element.content_desc.strip():
            return element.content_desc.strip()[:20]

        # 最后使用resource_id的最后一部分
        if element.resource_id and element.resource_id.strip():
            parts = element.resource_id.split('/')
            if len(parts) > 1:
                return parts[-1][:20]
            return element.resource_id[:20]

        # 使用类名
        class_parts = element.class_name.split('.')
        if len(class_parts) > 1:
            return class_parts[-1][:15]

        return ''

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='XML HTML标注程序')
    parser.add_argument('xml_file', help='XML文件路径')
    parser.add_argument('image_file', help='截图文件路径')
    parser.add_argument('output_file', help='输出HTML文件路径')

    args = parser.parse_args()

    try:
        # 分析XML
        annotator = XMLHTMLAnnotator(args.xml_file)

        # 生成HTML标注文件
        annotator.generate_html_annotation(args.image_file, args.output_file)

        print("✅ HTML标注文件生成成功！")

    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())