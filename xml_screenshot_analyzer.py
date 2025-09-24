#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML与截图对比分析程序
分析XML中哪些元素在截图可见区域内，哪些不在可见区域
"""

import xml.etree.ElementTree as ET
import re
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
import argparse

@dataclass
class Bounds:
    """表示UI元素的边界框"""
    left: int
    top: int
    right: int
    bottom: int

    def __post_init__(self):
        # 确保坐标是合理的
        if self.left > self.right:
            self.left, self.right = self.right, self.left
        if self.top > self.bottom:
            self.top, self.bottom = self.bottom, self.top

    @property
    def width(self) -> int:
        return self.right - self.left

    @property
    def height(self) -> int:
        return self.bottom - self.top

    @property
    def area(self) -> int:
        return self.width * self.height

    def is_within_screen(self, screen_width: int, screen_height: int) -> bool:
        """检查是否在屏幕范围内"""
        return (self.right > 0 and self.bottom > 0 and
                self.left < screen_width and self.top < screen_height)

    def get_visible_area(self, screen_width: int, screen_height: int) -> int:
        """计算在屏幕内的可见面积"""
        visible_left = max(0, self.left)
        visible_right = min(screen_width, self.right)
        visible_top = max(0, self.top)
        visible_bottom = min(screen_height, self.bottom)

        if visible_right <= visible_left or visible_bottom <= visible_top:
            return 0

        return (visible_right - visible_left) * (visible_bottom - visible_top)

    def get_visibility_percentage(self, screen_width: int, screen_height: int) -> float:
        """获取可见百分比"""
        if self.area == 0:
            return 0.0
        return self.get_visible_area(screen_width, screen_height) / self.area * 100

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

    def __post_init__(self):
        # 初始化children列表
        if self.children is None:
            self.children = []

class XMLAnalyzer:
    """XML分析器"""

    def __init__(self, xml_file: str):
        self.xml_file = xml_file
        self.root_element = None
        self.screen_width = 0
        self.screen_height = 0
        self.parse_xml()

    def parse_xml(self):
        """解析XML文件"""
        print(f"正在解析XML文件: {self.xml_file}")

        # 读取XML文件内容
        with open(self.xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        # 移除XML声明，只保留hierarchy部分
        if '<?xml' in xml_content:
            xml_content = xml_content.split('?>', 1)[1]

        # 解析XML
        root = ET.fromstring(xml_content.strip())

        # 获取屏幕尺寸 - 从根元素的bounds属性获取
        screen_bounds = self._parse_bounds(root.get('bounds', '0 0 0 0'))
        if screen_bounds.width == 0 or screen_bounds.height == 0:
            # 如果根元素没有有效的bounds，查找所有元素中的最大尺寸
            all_elements = self._find_all_elements_xml(root)
            max_right = 0
            max_bottom = 0
            for elem in all_elements:
                bounds = self._parse_bounds(elem.get('bounds', '0 0 0 0'))
                max_right = max(max_right, bounds.right)
                max_bottom = max(max_bottom, bounds.bottom)

            self.screen_width = max_right
            self.screen_height = max_bottom
        else:
            self.screen_width = screen_bounds.right
            self.screen_height = screen_bounds.bottom

        # 递归解析UI元素
        self.root_element = self._parse_element(root)

        print(f"XML解析完成，屏幕尺寸: {self.screen_width}x{self.screen_height}")

    def _parse_bounds(self, bounds_str: str) -> Bounds:
        """解析bounds字符串"""
        if not bounds_str:
            return Bounds(0, 0, 0, 0)

        # 移除引号
        bounds_str = bounds_str.strip('"\'')
        # 分割坐标
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

    def _find_all_elements_xml(self, element: ET.Element) -> List[ET.Element]:
        """查找所有XML元素（递归）"""
        elements = [element]
        for child in element:
            elements.extend(self._find_all_elements_xml(child))
        return elements

    def _parse_element(self, element: ET.Element) -> UIElement:
        """解析单个UI元素"""
        # 解析属性
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

        # 递归解析子元素
        for child in element:
            ui_element.children.append(self._parse_element(child))

        return ui_element

    def analyze_visibility(self) -> Dict[str, List[UIElement]]:
        """分析所有元素的可见性"""
        print("正在分析元素可见性...")

        visible_elements = []
        hidden_elements = []
        partially_visible_elements = []

        all_elements = self._get_all_elements(self.root_element)

        for element in all_elements:
            if not element.visible_to_user:
                hidden_elements.append(element)
                continue

            visibility = element.bounds.get_visibility_percentage(
                self.screen_width, self.screen_height
            )

            if visibility >= 90:  # 90%以上可见认为完全可见
                visible_elements.append(element)
            elif visibility > 0:  # 部分可见
                element.visibility_percentage = visibility
                partially_visible_elements.append(element)
            else:  # 完全不可见
                hidden_elements.append(element)

        return {
            'visible': visible_elements,
            'partially_visible': partially_visible_elements,
            'hidden': hidden_elements
        }

    def _get_all_elements(self, element: UIElement) -> List[UIElement]:
        """获取所有UI元素（递归）"""
        elements = [element]
        for child in element.children:
            elements.extend(self._get_all_elements(child))
        return elements

    def find_text_elements(self) -> List[UIElement]:
        """查找所有包含文本的元素"""
        text_elements = []
        all_elements = self._get_all_elements(self.root_element)

        for element in all_elements:
            if element.text and element.text.strip():
                text_elements.append(element)

        return text_elements

    def find_clickable_elements(self) -> List[UIElement]:
        """查找所有可点击的元素"""
        clickable_elements = []
        all_elements = self._get_all_elements(self.root_element)

        for element in all_elements:
            if element.clickable:
                clickable_elements.append(element)

        return clickable_elements

class VisibilityReporter:
    """可见性报告生成器"""

    def __init__(self, analyzer: XMLAnalyzer):
        self.analyzer = analyzer

    def generate_report(self) -> str:
        """生成分析报告"""
        visibility_analysis = self.analyzer.analyze_visibility()

        report = []
        report.append("=" * 60)
        report.append("XML与截图对比分析报告")
        report.append("=" * 60)
        report.append("")

        # 基本信息
        report.append(f"屏幕尺寸: {self.analyzer.screen_width} x {self.analyzer.screen_height}")
        report.append("")

        # 可见性统计
        visible_count = len(visibility_analysis['visible'])
        partial_count = len(visibility_analysis['partially_visible'])
        hidden_count = len(visibility_analysis['hidden'])
        total_count = visible_count + partial_count + hidden_count

        report.append("可见性统计:")
        report.append(f"  完全可见元素: {visible_count} ({visible_count/total_count*100:.1f}%)")
        report.append(f"  部分可见元素: {partial_count} ({partial_count/total_count*100:.1f}%)")
        report.append(f"  隐藏元素: {hidden_count} ({hidden_count/total_count*100:.1f}%)")
        report.append("")

        # 完全可见的重要元素
        report.append("完全可见的重要元素:")
        visible_important = [e for e in visibility_analysis['visible'] if e.important]
        if visible_important:
            for element in visible_important[:10]:  # 只显示前10个
                report.append(f"  - {element.class_name}: '{element.text}' | '{element.content_desc}' | {element.resource_id}")
                report.append(f"    位置: {element.bounds.left},{element.bounds.top} - {element.bounds.right},{element.bounds.bottom}")
        else:
            report.append("  无完全可见的重要元素")
        report.append("")

        # 部分可见元素
        report.append("部分可见元素:")
        if visibility_analysis['partially_visible']:
            for element in visibility_analysis['partially_visible'][:5]:  # 只显示前5个
                report.append(f"  - {element.class_name}: '{element.text}' (可见度: {element.visibility_percentage:.1f}%)")
                report.append(f"    位置: {element.bounds.left},{element.bounds.top} - {element.bounds.right},{element.bounds.bottom}")
        else:
            report.append("  无部分可见元素")
        report.append("")

        # 隐藏的重要元素
        report.append("隐藏的重要元素:")
        hidden_important = [e for e in visibility_analysis['hidden'] if e.important]
        if hidden_important:
            for element in hidden_important[:10]:  # 只显示前10个
                report.append(f"  - {element.class_name}: '{element.text}' | '{element.content_desc}' | {element.resource_id}")
                report.append(f"    位置: {element.bounds.left},{element.bounds.top} - {element.bounds.right},{element.bounds.bottom}")
                # 分析隐藏原因
                reason = self._analyze_hidden_reason(element)
                if reason:
                    report.append(f"    可能原因: {reason}")
        else:
            report.append("  无隐藏的重要元素")
        report.append("")

        # 文本元素分析
        text_elements = self.analyzer.find_text_elements()
        visible_text = [e for e in text_elements if e in visibility_analysis['visible']]
        hidden_text = [e for e in text_elements if e in visibility_analysis['hidden']]

        report.append("文本元素分析:")
        report.append(f"  可见文本元素: {len(visible_text)}")
        for element in visible_text[:5]:
            report.append(f"    - '{element.text}'")
        report.append(f"  隐藏文本元素: {len(hidden_text)}")
        for element in hidden_text[:5]:
            report.append(f"    - '{element.text}'")
        report.append("")

        # 可点击元素分析
        clickable_elements = self.analyzer.find_clickable_elements()
        visible_clickable = [e for e in clickable_elements if e in visibility_analysis['visible']]
        hidden_clickable = [e for e in clickable_elements if e in visibility_analysis['hidden']]

        report.append("可点击元素分析:")
        report.append(f"  可见可点击元素: {len(visible_clickable)}")
        for element in visible_clickable[:5]:
            report.append(f"    - {element.class_name}: '{element.content_desc}'")
        report.append(f"  隐藏可点击元素: {len(hidden_clickable)}")
        for element in hidden_clickable[:5]:
            report.append(f"    - {element.class_name}: '{element.content_desc}'")
        report.append("")

        return "\n".join(report)

    def _analyze_hidden_reason(self, element: UIElement) -> str:
        """分析元素隐藏的可能原因"""
        reasons = []

        # 检查是否在屏幕外
        if element.bounds.left < 0:
            reasons.append("向左偏移超出屏幕")
        if element.bounds.top < 0:
            reasons.append("向上偏移超出屏幕")
        if element.bounds.right > self.analyzer.screen_width:
            reasons.append("向右偏移超出屏幕")
        if element.bounds.bottom > self.analyzer.screen_height:
            reasons.append("向下偏移超出屏幕")

        # 检查是否是错误状态相关
        if "定位获取失败" in element.text:
            reasons.append("错误状态显示")

        if "错误" in element.resource_id or "error" in element.resource_id.lower():
            reasons.append("错误页面组件")

        # 检查是否是后台组件
        if "taskbar" in element.resource_id.lower():
            reasons.append("后台任务栏")

        if "toast" in element.resource_id.lower():
            reasons.append("提示框组件")

        return "; ".join(reasons) if reasons else ""

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='XML与截图对比分析程序')
    parser.add_argument('xml_file', help='XML文件路径')
    parser.add_argument('--image', help='截图文件路径（可选，用于显示分析结果）')
    parser.add_argument('--output', help='输出报告文件路径（可选）')

    args = parser.parse_args()

    try:
        # 分析XML
        analyzer = XMLAnalyzer(args.xml_file)

        # 生成报告
        reporter = VisibilityReporter(analyzer)
        report = reporter.generate_report()

        # 输出报告
        print(report)

        # 保存报告到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"报告已保存到: {args.output}")

        # 如果有图片，显示图片信息
        if args.image:
            print(f"\n截图信息:")
            print(f"  图片文件: {args.image}")
            print("  注意: 需要安装Pillow库来读取图片尺寸信息")
            print(f"  XML屏幕尺寸: {analyzer.screen_width} x {analyzer.screen_height}")

    except Exception as e:
        print(f"分析过程中发生错误: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())