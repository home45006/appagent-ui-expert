#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
坐标修正验证工具
验证Y坐标修正是否正确
"""

def validate_coordinate_correction():
    """验证坐标修正"""
    print("坐标修正验证报告")
    print("=" * 50)

    # 关键元素的原始坐标和修正后的坐标
    key_elements = [
        {
            'name': '选择收货地址',
            'original_bounds': '66 84 222 120',
            'expected_position': '标题栏中央'
        },
        {
            'name': '郑州市',
            'original_bounds': '27 169 102 198',
            'expected_position': '城市选择区域'
        },
        {
            'name': '请输入你的收货地址',
            'original_bounds': '216 153 655 210',
            'expected_position': '地址输入框'
        },
        {
            'name': '当前定位',
            'original_bounds': '27 243 126 280',
            'expected_position': '定位功能区域'
        },
        {
            'name': '新增地址',
            'original_bounds': '294 1119 411 1141',
            'expected_position': '底部操作按钮'
        }
    ]

    status_bar_offset = 36

    print("原始坐标 -> 修正后坐标（减去状态栏36px）")
    print("-" * 60)

    for element in key_elements:
        # 解析原始坐标
        coords = element['original_bounds'].split()
        if len(coords) == 4:
            left, top, right, bottom = map(int, coords)

            # 计算修正后的坐标
            corrected_top = top - status_bar_offset
            corrected_bottom = bottom - status_bar_offset

            print(f"元素: {element['name']}")
            print(f"  预期位置: {element['expected_position']}")
            print(f"  原始坐标: {element['original_bounds']}")
            print(f"  修正后坐标: {left} {corrected_top} {right} {corrected_bottom}")
            print(f"  Y轴偏移: -{status_bar_offset}px")
            print()

    print("修正说明:")
    print("-" * 30)
    print("1. XML中的坐标包含36像素的状态栏区域")
    print("2. 图片显示的是实际页面内容，不包含状态栏")
    print("3. 因此需要将所有Y坐标减去36px来对齐图片")
    print("4. X坐标保持不变（左右位置正确）")
    print()

    print("修正前后对比示例:")
    print("-" * 30)
    print("• 选择收货地址:")
    print("  - 原始: Y=84 (从屏幕顶部算起，包含状态栏)")
    print("  - 修正: Y=48 (从页面内容顶部算起)")
    print()
    print("• 新增地址:")
    print("  - 原始: Y=1119 (从屏幕顶部算起)")
    print("  - 修正: Y=1083 (从页面内容顶部算起)")

if __name__ == "__main__":
    validate_coordinate_correction()