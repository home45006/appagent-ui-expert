#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐标验证工具
验证XML中关键元素的坐标是否正确
"""

import xml.etree.ElementTree as ET
import re

def extract_key_elements(xml_file):
    """提取关键元素的坐标信息"""
    print("正在分析XML中的关键元素坐标...")

    with open(xml_file, 'r', encoding='utf-8') as f:
        xml_content = f.read()

    if '<?xml' in xml_content:
        xml_content = xml_content.split('?>', 1)[1]

    # 关键元素及其预期位置
    key_elements = {
        '选择收货地址': '标题栏中央',
        '郑州市': '城市选择区域',
        '请输入你的收货地址': '地址输入框',
        '当前定位': '定位功能区域',
        '无定位信息': '定位状态显示',
        '重新定位': '定位操作按钮',
        '收货地址': '地址列表标题',
        '管理': '管理按钮',
        '新增地址': '底部操作按钮'
    }

    found_elements = {}

    for element_name, expected_location in key_elements.items():
        # 查找元素
        pattern = f'text="{re.escape(element_name)}"[^>]*bounds="([^"]*)"'
        match = re.search(pattern, xml_content)

        if match:
            bounds = match.group(1)
            coords = bounds.split()
            if len(coords) == 4:
                left, top, right, bottom = map(int, coords)
                width = right - left
                height = bottom - top

                found_elements[element_name] = {
                    'bounds': bounds,
                    'left': left,
                    'top': top,
                    'right': right,
                    'bottom': bottom,
                    'width': width,
                    'height': height,
                    'expected': expected_location
                }

    return found_elements

def analyze_coordinate_system(xml_file):
    """分析坐标系统"""
    print("正在分析坐标系统...")

    with open(xml_file, 'r', encoding='utf-8') as f:
        xml_content = f.read()

    # 查找根元素bounds
    root_match = re.search(r'<hierarchy[^>]*bounds="([^"]*)"', xml_content)
    if root_match:
        root_bounds = root_match.group(1)
        print(f"根元素bounds: {root_bounds}")

    # 查找所有bounds的最大最小值
    all_bounds = re.findall(r'bounds="([^"]*)"', xml_content)

    min_left = float('inf')
    max_right = 0
    min_top = float('inf')
    max_bottom = 0

    for bounds in all_bounds:
        coords = bounds.split()
        if len(coords) == 4:
            left, top, right, bottom = map(int, coords)
            min_left = min(min_left, left)
            max_right = max(max_right, right)
            min_top = min(min_top, top)
            max_bottom = max(max_bottom, bottom)

    print(f"坐标范围: left={min_left}, top={min_top}, right={max_right}, bottom={max_bottom}")
    print(f"屏幕尺寸: {max_right} x {max_bottom}")

    # 检查是否有负坐标
    negative_coords = []
    for bounds in all_bounds:
        coords = bounds.split()
        if len(coords) == 4:
            left, top, right, bottom = map(int, coords)
            if left < 0 or top < 0:
                negative_coords.append((left, top, bounds))

    if negative_coords:
        print(f"发现 {len(negative_coords)} 个负坐标元素:")
        for left, top, bounds in negative_coords[:5]:  # 只显示前5个
            print(f"  负坐标: {bounds}")

    return {
        'min_left': min_left,
        'max_right': max_right,
        'min_top': min_top,
        'max_bottom': max_bottom,
        'negative_count': len(negative_coords)
    }

def main():
    """主函数"""
    import sys

    if len(sys.argv) > 1:
        xml_file = sys.argv[1]
    else:
        xml_file = '1754975278926.xml'

    print("=" * 60)
    print("坐标验证分析报告")
    print("=" * 60)

    # 分析坐标系统
    coord_info = analyze_coordinate_system(xml_file)
    print()

    # 提取关键元素
    key_elements = extract_key_elements(xml_file)

    print("\n关键元素坐标分析:")
    print("-" * 60)

    for element_name, info in key_elements.items():
        print(f"元素: {element_name}")
        print(f"  预期位置: {info['expected']}")
        print(f"  实际坐标: {info['bounds']}")
        print(f"  位置: ({info['left']}, {info['top']}) - ({info['right']}, {info['bottom']})")
        print(f"  尺寸: {info['width']} × {info['height']}")
        print()

    # 分析可见性
    print("可见性分析:")
    print("-" * 60)

    visible_count = 0
    hidden_count = 0

    for element_name, info in key_elements.items():
        # 检查是否在可见区域内
        if (info['left'] >= 0 and info['top'] >= 0 and
            info['right'] <= coord_info['max_right'] and
            info['bottom'] <= coord_info['max_bottom']):
            status = "✅ 可见"
            visible_count += 1
        else:
            status = "❌ 不可见"
            hidden_count += 1

        print(f"{status} {element_name}: {info['bounds']}")

    print(f"\n可见性统计: {visible_count} 个可见, {hidden_count} 个不可见")

    # 生成坐标映射建议
    print("\n坐标映射建议:")
    print("-" * 60)
    print(f"1. XML坐标系统: bounds格式为 [left top right bottom]")
    print(f"2. 屏幕原点: (0, 0) 在左上角")
    print(f"3. 页面内容从 Y={coord_info['min_top']} 开始（可能包含状态栏）")
    print(f"4. 实际可见区域: (0, {coord_info['min_top']}) 到 ({coord_info['max_right']}, {coord_info['max_bottom']})")

    if coord_info['negative_count'] > 0:
        print(f"5. 警告: 发现 {coord_info['negative_count']} 个负坐标元素，可能表示隐藏或偏移的UI")

if __name__ == "__main__":
    main()