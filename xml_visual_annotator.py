#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML可视化标注程序
在截图上用红框标示出可见区域的UI元素
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple
from dataclasses import dataclass
import argparse
import sys

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
    children: List['UIElement']

class XMLVisualAnnotator:
    """XML可视化标注器"""

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
            clickable=element.get('clickable', 'false').lower() == 'true',
            children=[]
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

    def generate_annotated_image(self, image_file: str, output_file: str):
        """生成标注图片"""
        print(f"正在生成标注图片: {output_file}")

        try:
            # 尝试使用PIL
            self._generate_with_pil(image_file, output_file)
        except ImportError:
            print("警告: 未安装Pillow库，无法生成图片标注")
            print("请运行: pip install Pillow")
            return False
        except Exception as e:
            print(f"生成图片时发生错误: {e}")
            return False

        return True

    def _generate_with_pil(self, image_file: str, output_file: str):
        """使用PIL生成标注图片"""
        from PIL import Image, ImageDraw, ImageFont

        # 打开图片
        with Image.open(image_file) as img:
            # 创建绘图对象
            draw = ImageDraw.Draw(img)

            # 获取可见元素
            visible_elements = self.get_visible_elements()

            print(f"找到 {len(visible_elements)} 个可见元素")

            # 绘制红框
            for i, element in enumerate(visible_elements):
                # 跳过过小的元素
                element_width = element.bounds.right - element.bounds.left
                element_height = element.bounds.bottom - element.bounds.top

                if element_width < 10 or element_height < 10:
                    continue

                # 跳过容器类元素，只标注具体内容
                if self._should_skip_element(element):
                    continue

                # 绘制红框
                draw.rectangle(
                    [element.bounds.left, element.bounds.top,
                     element.bounds.right, element.bounds.bottom],
                    outline='red',
                    width=2
                )

                # 添加标签
                label = self._get_element_label(element)
                if label:
                    try:
                        # 尝试使用默认字体
                        font = ImageFont.load_default()
                        # 获取文本边界
                        bbox = draw.textbbox((0, 0), label, font=font)
                        text_width = bbox[2] - bbox[0]
                        text_height = bbox[3] - bbox[1]

                        # 确保标签位置在图片内
                        label_x = element.bounds.left
                        label_y = max(0, element.bounds.top - text_height - 5)

                        # 绘制标签背景
                        draw.rectangle(
                            [label_x, label_y, label_x + text_width + 4, label_y + text_height + 2],
                            fill='red',
                            outline='red'
                        )

                        # 绘制白色文字
                        draw.text(
                            (label_x + 2, label_y + 1),
                            label,
                            fill='white',
                            font=font
                        )
                    except:
                        # 如果字体处理失败，只绘制框
                        pass

            # 保存图片
            img.save(output_file)
            print(f"标注图片已保存到: {output_file}")

    def _should_skip_element(self, element: UIElement) -> bool:
        """判断是否应该跳过该元素（不标注）"""
        # 跳过容器类元素
        skip_classes = [
            'android.widget.FrameLayout',
            'android.widget.LinearLayout',
            'android.widget.RelativeLayout',
            'android.view.ViewGroup',
            'android.view.View'
        ]

        if element.class_name in skip_classes:
            return True

        # 跳过没有文本和描述的元素
        if not element.text and not element.content_desc and not element.resource_id:
            return True

        # 跳过过大的容器（可能是根容器）
        element_area = (element.bounds.right - element.bounds.left) * (element.bounds.bottom - element.bounds.top)
        screen_area = self.screen_width * self.screen_height
        if element_area > screen_area * 0.8:  # 超过屏幕80%的元素
            return True

        return False

    def _get_element_label(self, element: UIElement) -> str:
        """获取元素的标签文本"""
        # 优先使用文本内容
        if element.text and element.text.strip():
            return element.text.strip()[:15]  # 限制长度

        # 其次使用描述
        if element.content_desc and element.content_desc.strip():
            return element.content_desc.strip()[:15]

        # 最后使用resource_id的最后一部分
        if element.resource_id and element.resource_id.strip():
            parts = element.resource_id.split('/')
            if len(parts) > 1:
                return parts[-1][:15]
            return element.resource_id[:15]

        # 使用类名
        class_parts = element.class_name.split('.')
        if len(class_parts) > 1:
            return class_parts[-1][:10]

        return ''

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='XML可视化标注程序')
    parser.add_argument('xml_file', help='XML文件路径')
    parser.add_argument('image_file', help='截图文件路径')
    parser.add_argument('output_file', help='输出标注图片路径')
    parser.add_argument('--min-visibility', type=int, default=50,
                       help='最小可见百分比 (默认: 50)')

    args = parser.parse_args()

    try:
        # 分析XML
        annotator = XMLVisualAnnotator(args.xml_file)

        # 生成标注图片
        success = annotator.generate_annotated_image(args.image_file, args.output_file)

        if success:
            print("✅ 标注图片生成成功！")
            print(f"📱 屏幕尺寸: {annotator.screen_width}x{annotator.screen_height}")

            # 显示统计信息
            visible_elements = annotator.get_visible_elements()
            important_elements = [e for e in visible_elements if e.important]
            text_elements = [e for e in visible_elements if e.text and e.text.strip()]
            clickable_elements = [e for e in visible_elements if e.clickable]

            print(f"📊 统计信息:")
            print(f"   可见元素总数: {len(visible_elements)}")
            print(f"   重要元素: {len(important_elements)}")
            print(f"   文本元素: {len(text_elements)}")
            print(f"   可点击元素: {len(clickable_elements)}")

        else:
            print("❌ 标注图片生成失败")
            return 1

    except Exception as e:
        print(f"❌ 分析过程中发生错误: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())