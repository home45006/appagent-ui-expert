#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML文件对比分析工具
对比两个不同时间点的XML文件，分析页面状态变化
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple
from dataclasses import dataclass
import re
import argparse

@dataclass
class Bounds:
    """表示UI元素的边界框"""
    left: int
    top: int
    right: int
    bottom: int

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

class XMLComparator:
    """XML文件对比器"""

    def __init__(self, xml_file1: str, xml_file2: str):
        self.xml_file1 = xml_file1
        self.xml_file2 = xml_file2
        self.elements1 = []
        self.elements2 = []
        self.parse_xml_files()

    def parse_xml_files(self):
        """解析两个XML文件"""
        print(f"正在解析XML文件1: {self.xml_file1}")
        self.elements1 = self._parse_xml_file(self.xml_file1)

        print(f"正在解析XML文件2: {self.xml_file2}")
        self.elements2 = self._parse_xml_file(self.xml_file2)

    def _parse_xml_file(self, xml_file: str) -> List[UIElement]:
        """解析单个XML文件"""
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read()

        if '<?xml' in xml_content:
            xml_content = xml_content.split('?>', 1)[1]

        root = ET.fromstring(xml_content.strip())
        return self._parse_all_elements(root)

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

    def compare_pages(self):
        """对比两个页面的差异"""
        print("=" * 60)
        print("XML文件对比分析报告")
        print("=" * 60)

        # 基本统计
        self._compare_basic_stats()

        # 页面类型分析
        self._analyze_page_types()

        # 关键元素对比
        self._compare_key_elements()

        # WebView状态对比
        self._compare_webview_states()

        # 文本内容对比
        self._compare_text_content()

        # 交互元素对比
        self._compare_interactive_elements()

    def _compare_basic_stats(self):
        """对比基本统计信息"""
        print("\n📊 基本统计对比:")
        print("-" * 40)

        visible_elements1 = [e for e in self.elements1 if e.visible_to_user]
        visible_elements2 = [e for e in self.elements2 if e.visible_to_user]

        important_elements1 = [e for e in self.elements1 if e.important]
        important_elements2 = [e for e in self.elements2 if e.important]

        text_elements1 = [e for e in self.elements1 if e.text and e.text.strip()]
        text_elements2 = [e for e in self.elements2 if e.text and e.text.strip()]

        clickable_elements1 = [e for e in self.elements1 if e.clickable]
        clickable_elements2 = [e for e in self.elements2 if e.clickable]

        print(f"{'指标':<20} {'文件1':<10} {'文件2':<10} {'变化':<10}")
        print("-" * 50)
        print(f"{'总元素数':<20} {len(self.elements1):<10} {len(self.elements2):<10} {len(self.elements2)-len(self.elements1):+d}")
        print(f"{'可见元素':<20} {len(visible_elements1):<10} {len(visible_elements2):<10} {len(visible_elements2)-len(visible_elements1):+d}")
        print(f"{'重要元素':<20} {len(important_elements1):<10} {len(important_elements2):<10} {len(important_elements2)-len(important_elements1):+d}")
        print(f"{'文本元素':<20} {len(text_elements1):<10} {len(text_elements2):<10} {len(text_elements2)-len(text_elements1):+d}")
        print(f"{'可点击元素':<20} {len(clickable_elements1):<10} {len(clickable_elements2):<10} {len(clickable_elements2)-len(clickable_elements1):+d}")

    def _analyze_page_types(self):
        """分析页面类型"""
        print("\n🔍 页面类型分析:")
        print("-" * 40)

        # 分析文件1 (1754975278926)
        key_texts1 = [e.text for e in self.elements1 if e.text and e.text.strip()]
        page1_type = self._identify_page_type(key_texts1)

        # 分析文件2 (1757493209695)
        key_texts2 = [e.text for e in self.elements2 if e.text and e.text.strip()]
        page2_type = self._identify_page_type(key_texts2)

        print(f"文件1 (1754975278926): {page1_type}")
        print(f"文件2 (1757493209695): {page2_type}")

        if page1_type != page2_type:
            print("⚠️  页面类型发生了变化！")
        else:
            print("✅ 页面类型一致")

    def _identify_page_type(self, key_texts: List[str]) -> str:
        """根据关键文本识别页面类型"""
        text_str = " ".join(key_texts).lower()

        if "选择收货地址" in text_str:
            return "地址选择页面"
        elif "请使用微信扫码支付" in text_str:
            return "微信支付页面"
        elif "订单" in text_str:
            return "订单页面"
        elif "购物车" in text_str:
            return "购物车页面"
        elif "首页" in text_str:
            return "首页"
        else:
            return "未知页面类型"

    def _compare_key_elements(self):
        """对比关键元素"""
        print("\n🎯 关键元素对比:")
        print("-" * 40)

        # 文件1的关键元素
        file1_elements = {
            "选择收货地址": self._find_element_by_text(self.elements1, "选择收货地址"),
            "郑州市": self._find_element_by_text(self.elements1, "郑州市"),
            "请输入你的收货地址": self._find_element_by_text(self.elements1, "请输入你的收货地址"),
            "当前定位": self._find_element_by_text(self.elements1, "当前定位"),
            "新增地址": self._find_element_by_text(self.elements1, "新增地址")
        }

        # 文件2的关键元素
        file2_elements = {
            "请使用微信扫码支付": self._find_element_by_text(self.elements2, "请使用微信扫码支付"),
            "关闭": self._find_element_by_text(self.elements2, "关闭"),
            "阿克苏苹果": self._find_element_by_text(self.elements2, "阿克苏苹果"),
            "拼单": self._find_element_by_text(self.elements2, "拼单"),
            "我的常点": self._find_element_by_text(self.elements2, "我的常点")
        }

        print("文件1 (地址选择页面) 关键元素:")
        for name, element in file1_elements.items():
            if element:
                print(f"  ✅ {name}: {element.bounds.left},{element.bounds.top}-{element.bounds.right},{element.bounds.bottom}")
            else:
                print(f"  ❌ {name}: 未找到")

        print("\n文件2 (支付页面) 关键元素:")
        for name, element in file2_elements.items():
            if element:
                print(f"  ✅ {name}: {element.bounds.left},{element.bounds.top}-{element.bounds.right},{element.bounds.bottom}")
            else:
                print(f"  ❌ {name}: 未找到")

    def _compare_webview_states(self):
        """对比WebView状态"""
        print("\n🌐 WebView状态对比:")
        print("-" * 40)

        webviews1 = [e for e in self.elements1 if e.class_name == "android.webkit.WebView"]
        webviews2 = [e for e in self.elements2 if e.class_name == "android.webkit.WebView"]

        print(f"文件1 WebView数量: {len(webviews1)}")
        for i, wv in enumerate(webviews1):
            visibility = "可见" if wv.visible_to_user else "隐藏"
            print(f"  WebView{i+1}: {wv.bounds.left},{wv.bounds.top}-{wv.bounds.right},{wv.bounds.bottom} ({visibility})")

        print(f"\n文件2 WebView数量: {len(webviews2)}")
        for i, wv in enumerate(webviews2):
            visibility = "可见" if wv.visible_to_user else "隐藏"
            print(f"  WebView{i+1}: {wv.bounds.left},{wv.bounds.top}-{wv.bounds.right},{wv.bounds.bottom} ({visibility})")

    def _compare_text_content(self):
        """对比文本内容"""
        print("\n📝 文本内容对比:")
        print("-" * 40)

        text_elements1 = [e for e in self.elements1 if e.text and e.text.strip()]
        text_elements2 = [e for e in self.elements2 if e.text and e.text.strip()]

        texts1 = set(e.text.strip() for e in text_elements1)
        texts2 = set(e.text.strip() for e in text_elements2)

        common_texts = texts1 & texts2
        only_in_file1 = texts1 - texts2
        only_in_file2 = texts2 - texts1

        print(f"共同文本: {len(common_texts)} 个")
        for text in sorted(list(common_texts))[:5]:  # 只显示前5个
            print(f"  • {text}")

        print(f"\n仅在文件1中的文本: {len(only_in_file1)} 个")
        for text in sorted(list(only_in_file1))[:5]:
            print(f"  • {text}")

        print(f"\n仅在文件2中的文本: {len(only_in_file2)} 个")
        for text in sorted(list(only_in_file2))[:5]:
            print(f"  • {text}")

    def _compare_interactive_elements(self):
        """对比交互元素"""
        print("\n🖱️  交互元素对比:")
        print("-" * 40)

        clickable1 = [e for e in self.elements1 if e.clickable]
        clickable2 = [e for e in self.elements2 if e.clickable]

        print(f"文件1可点击元素: {len(clickable1)} 个")
        for elem in clickable1[:5]:  # 只显示前5个
            label = elem.text or elem.content_desc or elem.class_name
            print(f"  • {label}")

        print(f"\n文件2可点击元素: {len(clickable2)} 个")
        for elem in clickable2[:5]:  # 只显示前5个
            label = elem.text or elem.content_desc or elem.class_name
            print(f"  • {label}")

    def _find_element_by_text(self, elements: List[UIElement], text: str) -> UIElement:
        """根据文本查找元素"""
        for element in elements:
            if element.text and text in element.text:
                return element
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='XML文件对比分析工具')
    parser.add_argument('xml_file1', help='第一个XML文件路径')
    parser.add_argument('xml_file2', help='第二个XML文件路径')
    parser.add_argument('--output', help='输出报告文件路径')

    args = parser.parse_args()

    try:
        # 创建对比器
        comparator = XMLComparator(args.xml_file1, args.xml_file2)

        # 执行对比
        comparator.compare_pages()

        print(f"\n✅ 对比分析完成！")

        # 保存报告到文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                # 这里可以保存更详细的报告
                pass

    except Exception as e:
        print(f"❌ 对比过程中发生错误: {e}")
        return 1

    return 0

if __name__ == "__main__":
    exit(main())