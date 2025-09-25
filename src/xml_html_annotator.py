#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
XML HTML标注程序
生成HTML文件，在浏览器中显示标注效果
"""

import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional
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
    parent_node_id: Optional[str] = None
    parent: Optional['UIElement'] = None

class XMLHTMLAnnotator:
    """XML HTML标注器"""

    def __init__(self, xml_file: str):
        self.xml_file = xml_file
        self.elements = []
        self.screen_width = 0
        self.screen_height = 0
        self.ocr_enabled = True  # 启用OCR功能
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

        # 建立父子关系
        self._build_parent_child_relationships()

        print(f"XML解析完成，屏幕尺寸: {self.screen_width}x{self.screen_height}")

    def _build_parent_child_relationships(self):
        """建立父子关系"""
        # 创建node_id到元素的映射
        node_id_map = {element.node_id: element for element in self.elements}

        # 为每个元素设置parent引用
        for element in self.elements:
            if element.parent_node_id and element.parent_node_id in node_id_map:
                element.parent = node_id_map[element.parent_node_id]

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

    def _parse_all_elements(self, element: ET.Element, parent_node_id: Optional[str] = None) -> List[UIElement]:
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
            parent_node_id=parent_node_id
        )
        elements.append(ui_element)

        # 递归解析子元素
        current_node_id = ui_element.node_id
        for child in element:
            elements.extend(self._parse_all_elements(child, current_node_id))

        return elements

    def get_visible_elements(self) -> List[UIElement]:
        """获取可见元素"""
        visible_elements = []

        for element in self.elements:
            # 严格的可见性检查
            if not self._is_element_visible(element):
                continue

            # 计算可见百分比
            visibility = self._calculate_visibility(element.bounds)

            if visibility >= 50:  # 50%以上可见才标注
                element.visibility_percentage = visibility
                visible_elements.append(element)

        return visible_elements

    def _is_element_visible(self, element: UIElement) -> bool:
        """严格检查元素是否可见"""
        # 1. 检查visible-to-user属性
        if not element.visible_to_user:
            return False

        # 2. 检查元素尺寸
        element_width = element.bounds.right - element.bounds.left
        element_height = element.bounds.bottom - element.bounds.top

        # 过滤过小的元素（可能不可见）
        if element_width < 3 or element_height < 2:
            return False

        # 3. 检查元素位置是否在合理范围内
        # 状态栏高度36px，底部可能有导航栏
        min_y = 36  # 状态栏以下
        max_y = self.screen_height - 100  # 底部导航栏以上

        element_top = element.bounds.top
        element_bottom = element.bounds.bottom

        # 如果元素完全在状态栏上方或屏幕底部之外，不可见
        if element_bottom < min_y or element_top > self.screen_height:
            return False

        # 4. 检查是否有实际内容
        has_content = (
            (element.text and element.text.strip()) or
            (element.content_desc and element.content_desc.strip()) or
            (element.resource_id and element.resource_id.strip()) or
            element.clickable or
            element.important
        )

        # 如果没有内容且不是交互元素，可能不可见
        if not has_content:
            return False

        # 5. 特殊类的元素需要额外检查
        invisible_classes = [
            'android.widget.FrameLayout',
            'android.widget.LinearLayout',
            'android.widget.RelativeLayout',
            'android.view.ViewGroup'
        ]

        if element.class_name in invisible_classes:
            # 布局类元素需要更严格的内容检查
            if not (element.text or element.content_desc or element.clickable):
                return False

        return True

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

    def _perform_ocr_analysis(self, image_file: str) -> List:
        """执行OCR文字识别分析"""
        try:
            from ocr_processor import OCRProcessor

            print("正在执行OCR文字识别...")
            ocr_processor = OCRProcessor()
            text_blocks = ocr_processor.process_image(image_file, engine='auto')

            # 合并相邻的文字块
            text_blocks = ocr_processor.merge_nearby_blocks(text_blocks)

            # 转换为图像内容格式
            ocr_contents = []
            for block in text_blocks:
                # 根据文字内容判断类型
                content_type = self._classify_text_content(block.text)

                ocr_contents.append({
                    'content_type': content_type,
                    'text': block.text,
                    'confidence': block.confidence,
                    'bounds': {
                        'left': block.bounds.left,
                        'top': block.bounds.top,
                        'right': block.bounds.right,
                        'bottom': block.bounds.bottom
                    },
                    'source': 'ocr',
                    'is_ocr': True  # 标记为OCR识别的内容
                })

            print(f"OCR识别出 {len(ocr_contents)} 个文字块")
            return ocr_contents

        except ImportError:
            print("警告: 未安装OCR处理模块，跳过文字识别")
            return []
        except Exception as e:
            print(f"OCR分析失败: {e}")
            return []

    def _classify_text_content(self, text: str) -> str:
        """根据文本内容分类类型"""
        text_lower = text.lower().strip()

        # 搜索相关
        if any(keyword in text_lower for keyword in ['搜索', 'search', '查找', '查询']):
            return 'search_input'

        # 输入相关
        if any(keyword in text_lower for keyword in ['输入', 'input', '请输入', '请填写']):
            return 'input'

        # 按钮相关
        if any(keyword in text_lower for keyword in ['确定', '取消', '确认', '提交', '登录', '注册', '返回', '关闭', '下一步', '完成', '删除', '编辑', '保存']):
            return 'button_text'

        # 链接相关
        if any(keyword in text_lower for keyword in ['了解更多', '查看详情', '点击查看', '点击进入']):
            return 'link_text'

        # 默认为普通文本
        return 'text'

    def _combine_ocr_with_image_analysis(self, ocr_results: List, image_contents: List, xml_elements: List[UIElement]) -> List:
        """合并OCR结果和图像分析结果"""
        combined = []

        # 添加OCR结果
        combined.extend(ocr_results)

        # 添加传统图像分析结果，但去除与OCR结果重复的内容
        for image_content in image_contents:
            is_duplicate = False

            # 检查是否与OCR结果重复
            for ocr_result in ocr_results:
                if self._is_duplicate_content(image_content, ocr_result):
                    is_duplicate = True
                    break

            if not is_duplicate:
                # 标记为非OCR内容
                image_content['is_ocr'] = False
                image_content['source'] = 'image_analysis'
                combined.append(image_content)

        # 尝试将OCR结果与XML元素匹配
        combined = self._match_ocr_with_xml_elements(combined, xml_elements)

        return combined

    def _is_duplicate_content(self, content1: Dict, content2: Dict) -> bool:
        """判断两个内容是否重复"""
        # 检查文本内容相似性
        text1 = content1.get('text', '').strip().lower()
        text2 = content2.get('text', '').strip().lower()

        if text1 == text2:
            return True

        # 检查是否一个包含另一个
        if text1 in text2 or text2 in text1:
            # 计算重叠度
            overlap_ratio = max(len(text1) / len(text2), len(text2) / len(text1)) if len(text1) > 0 and len(text2) > 0 else 0
            if overlap_ratio > 0.8:
                return True

        # 检查位置重叠
        bounds1 = content1.get('bounds', {})
        bounds2 = content2.get('bounds', {})

        overlap = self._calculate_overlap(
            bounds1.get('left', 0), bounds1.get('top', 0),
            bounds1.get('right', 0), bounds1.get('bottom', 0),
            bounds2.get('left', 0), bounds2.get('top', 0),
            bounds2.get('right', 0), bounds2.get('bottom', 0)
        )

        # 如果文本相似且位置重叠超过70%，认为是重复的
        text_similarity = len(set(text1.split()) & set(text2.split())) / max(len(set(text1.split())), len(set(text2.split()))) if text1 and text2 else 0

        return overlap > 0.7 and text_similarity > 0.6

    def _match_ocr_with_xml_elements(self, combined_results: List, xml_elements: List[UIElement]) -> List:
        """将OCR结果与XML元素匹配"""
        for result in combined_results:
            if result.get('is_ocr', False):
                # 为OCR结果寻找匹配的XML元素
                best_match = self._find_best_xml_match(result, xml_elements)
                if best_match:
                    result['xml_element_id'] = best_match.node_id
                    result['xml_class_name'] = best_match.class_name
                    result['matched'] = True
                else:
                    result['matched'] = False

        return combined_results

    def _find_best_xml_match(self, ocr_result: Dict, xml_elements: List[UIElement]) -> Optional[UIElement]:
        """为OCR结果寻找最佳匹配的XML元素"""
        if not xml_elements:
            return None

        ocr_bounds = ocr_result.get('bounds', {})
        ocr_text = ocr_result.get('text', '').lower().strip()

        best_match = None
        best_score = 0

        for element in xml_elements:
            # 计算位置重叠度
            overlap = self._calculate_overlap(
                ocr_bounds.get('left', 0), ocr_bounds.get('top', 0),
                ocr_bounds.get('right', 0), ocr_bounds.get('bottom', 0),
                element.bounds.left, element.bounds.top,
                element.bounds.right, element.bounds.bottom
            )

            # 计算文本匹配度
            text_score = 0
            if ocr_text:
                element_text = (element.text or '').lower()
                element_desc = (element.content_desc or '').lower()

                if ocr_text in element_text or element_text in ocr_text:
                    text_score = 1.0
                elif ocr_text in element_desc or element_desc in ocr_text:
                    text_score = 0.8
                else:
                    # 计算词汇重叠度
                    ocr_words = set(ocr_text.split())
                    element_words = set(element_text.split()) | set(element_desc.split())
                    if ocr_words and element_words:
                        text_score = len(ocr_words & element_words) / len(ocr_words)

            # 综合评分
            total_score = overlap * 0.6 + text_score * 0.4

            if total_score > best_score and total_score > 0.3:
                best_score = total_score
                best_match = element

        return best_match

    def _analyze_xml_statistics(self, xml_elements: List[UIElement]) -> Dict:
        """分析XML元素统计信息"""
        stats = {
            'total_elements': len(xml_elements),
            'coordinate_elements': 0,
            'visible_coordinate_elements': 0,
            'invisible_coordinate_elements': 0,
            'by_type': {},
            'by_visibility': {'visible': 0, 'invisible': 0, 'partially_visible': 0},
            'by_class': {},
            'interactive_elements': 0,
            'text_elements': 0,
            'layout_elements': 0
        }

        for element in xml_elements:
            # 统计坐标元素
            if (element.bounds.left >= 0 and element.bounds.top >= 0 and
                element.bounds.right > element.bounds.left and
                element.bounds.bottom > element.bounds.top):
                stats['coordinate_elements'] += 1

                # 计算可见性
                visibility = self._calculate_visibility(element.bounds)
                if visibility >= 80:  # 80%以上可见
                    stats['visible_coordinate_elements'] += 1
                    stats['by_visibility']['visible'] += 1
                elif visibility > 0:  # 部分可见
                    stats['by_visibility']['partially_visible'] += 1
                else:  # 不可见
                    stats['invisible_coordinate_elements'] += 1
                    stats['by_visibility']['invisible'] += 1

            # 按类型统计
            element_type = element.__class__.__name__
            stats['by_type'][element_type] = stats['by_type'].get(element_type, 0) + 1

            # 按类名统计
            if hasattr(element, 'class_name') and element.class_name:
                stats['by_class'][element.class_name] = stats['by_class'].get(element.class_name, 0) + 1

            # 交互元素统计
            if getattr(element, 'clickable', False):
                stats['interactive_elements'] += 1

            # 文本元素统计
            if hasattr(element, 'text') and element.text and element.text.strip():
                stats['text_elements'] += 1

            # 布局元素统计
            if any(layout_type in str(getattr(element, 'class_name', '')).lower()
                   for layout_type in ['layout', 'viewgroup', 'linearlayout', 'relativelayout', 'framelayout']):
                stats['layout_elements'] += 1

        return stats

    def generate_html_annotation(self, image_file: str, output_file: str):
        """生成HTML标注文件"""
        print(f"正在生成HTML标注文件: {output_file}")

        # 获取可见元素
        visible_elements = self.get_visible_elements()

        # 分析XML统计信息
        print("正在分析XML统计信息...")
        xml_stats = self._analyze_xml_statistics(visible_elements)
        print(f"XML统计结果: 总元素{xml_stats['total_elements']}个, 坐标元素{xml_stats['coordinate_elements']}个, "
              f"可见坐标元素{xml_stats['visible_coordinate_elements']}个, 不可见坐标元素{xml_stats['invisible_coordinate_elements']}个")

        # 分析图像内容
        print("正在分析图像内容...")
        image_contents = self._analyze_image_content(image_file, visible_elements)

        # 禁用页面区域标注
        page_regions = []

        # 禁用图像识别标注，只基于XML元素进行标注
        elements_to_annotate = self._filter_xml_elements_only(visible_elements)

        print(f"基于XML分析找到 {len(elements_to_annotate)} 个需要标注的元素")

        # 读取图片并转换为base64
        image_base64 = self.image_to_base64(image_file)

        # 计算实际可点击的元素数量
        actually_clickable_count = len([e for e in elements_to_annotate if self._is_effectively_clickable(e)])

        # 生成HTML
        html_content = self._generate_html_content(image_base64, page_regions, elements_to_annotate, image_contents, xml_stats, actually_clickable_count)

        # 保存HTML文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        print(f"HTML标注文件已保存到: {output_file}")
        print(f"请在浏览器中打开: file://{output_file}")

    def _analyze_image_content(self, image_file: str, xml_elements: List[UIElement]) -> List:
        """分析图像内容"""
        try:
            # 尝试OCR文字识别
            ocr_results = []
            if self.ocr_enabled:
                ocr_results = self._perform_ocr_analysis(image_file)

            # 尝试传统图像内容分析
            try:
                from image_content_analyzer import ImageContentAnalyzer
                analyzer = ImageContentAnalyzer()
                image_contents = analyzer.analyze_image_content(image_file)
                matched_contents = analyzer.match_with_xml_elements(image_contents, xml_elements)
            except ImportError:
                print("警告: 未安装图像分析依赖库，使用简化分析")
                matched_contents = self._simplified_image_analysis(image_file, xml_elements)
            except Exception as e:
                print(f"图像内容分析失败: {e}")
                matched_contents = []

            # 合并OCR结果和传统分析结果
            combined_results = self._combine_ocr_with_image_analysis(ocr_results, matched_contents, xml_elements)
            return combined_results

        except Exception as e:
            print(f"图像内容分析失败: {e}")
            return []

    def _simplified_image_analysis(self, image_file: str, xml_elements: List[UIElement]) -> List:
        """简化的图像内容分析（基于XML特征分析）"""
        image_contents = []

        # 从XML元素中智能推断可能的UI组件
        for element in xml_elements:
            content_type = None
            text = None
            confidence = 0.7

            # 搜索框检测
            if (element.class_name == 'android.widget.EditText' or
                'search' in element.resource_id.lower() or
                'edit' in element.resource_id.lower() or
                'input' in element.resource_id.lower()):

                content_type = 'search_input' if 'search' in element.resource_id.lower() else 'input'
                text = element.text or '搜索框' if content_type == 'search_input' else '输入框'
                confidence = 0.9

            # 按钮检测
            elif (element.class_name in ['android.widget.Button', 'android.widget.ImageButton'] or
                  element.clickable):

                content_type = 'button'
                text = element.text or element.content_desc or '按钮'
                confidence = 0.8

                # 进一步分类按钮类型
                if element.text:
                    text_lower = element.text.lower()
                    if any(keyword in text_lower for keyword in ['搜索', 'search', '查找']):
                        content_type = 'search_input'
                    elif any(keyword in text_lower for keyword in ['确定', '取消', '确认', '提交']):
                        content_type = 'button_text'

            # 重要文本检测
            elif element.important and element.text:
                content_type = 'text'
                text = element.text
                confidence = 0.8

                # 文本类型分类
                text_lower = element.text.lower()
                if any(keyword in text_lower for keyword in ['搜索', 'search', '查找', '输入']):
                    content_type = 'search_input'

            # 图像视图检测
            elif element.class_name == 'android.widget.ImageView':
                if element.content_desc:
                    content_type = 'icon'
                    text = element.content_desc
                    confidence = 0.7

            # 如果识别到内容类型，添加到结果
            if content_type:
                image_contents.append({
                    'content_type': content_type,
                    'text': text,
                    'confidence': confidence,
                    'bounds': {
                        'left': element.bounds.left,
                        'top': element.bounds.top - 36,  # 减去状态栏
                        'right': element.bounds.right,
                        'bottom': element.bounds.bottom - 36
                    },
                    'xml_element_id': element.node_id
                })

        # 智能合并和去重
        return self._merge_similar_contents(image_contents)

    def _merge_similar_contents(self, contents: List) -> List:
        """合并相似的内容"""
        merged = []
        used_indices = set()

        for i, content1 in enumerate(contents):
            if i in used_indices:
                continue

            # 寻找相似的内容进行合并
            similar_contents = [content1]
            for j, content2 in enumerate(contents[i+1:], i+1):
                if j in used_indices:
                    continue

                if self._are_contents_similar(content1, content2):
                    similar_contents.append(content2)
                    used_indices.add(j)

            # 合并相似内容
            if len(similar_contents) > 1:
                merged_content = self._merge_content_group(similar_contents)
                merged.append(merged_content)
            else:
                merged.append(content1)

            used_indices.add(i)

        return merged

    def _are_contents_similar(self, content1: Dict, content2: Dict) -> bool:
        """判断两个内容是否相似"""
        # 检查类型
        if content1.get('content_type') != content2.get('content_type'):
            return False

        # 检查位置重叠
        bounds1 = content1.get('bounds', {})
        bounds2 = content2.get('bounds', {})

        overlap = self._calculate_overlap(
            bounds1.get('left', 0), bounds1.get('top', 0),
            bounds1.get('right', 0), bounds1.get('bottom', 0),
            bounds2.get('left', 0), bounds2.get('top', 0),
            bounds2.get('right', 0), bounds2.get('bottom', 0)
        )

        return overlap > 0.7

    def _merge_content_group(self, contents: List[Dict]) -> Dict:
        """合并一组相似的内容"""
        # 选择置信度最高的作为基础
        base_content = max(contents, key=lambda c: c.get('confidence', 0))

        # 合并边界框
        all_bounds = [c.get('bounds', {}) for c in contents]
        min_left = min(b.get('left', 0) for b in all_bounds)
        min_top = min(b.get('top', 0) for b in all_bounds)
        max_right = max(b.get('right', 0) for b in all_bounds)
        max_bottom = max(b.get('bottom', 0) for b in all_bounds)

        base_content['bounds'] = {
            'left': min_left,
            'top': min_top,
            'right': max_right,
            'bottom': max_bottom
        }

        return base_content

    def _calculate_overlap(self, x1, y1, x2, y2, x3, y3, x4, y4) -> float:
        """计算两个矩形区域的重叠度"""
        # 计算重叠区域
        overlap_left = max(x1, x3)
        overlap_top = max(y1, y3)
        overlap_right = min(x2, x4)
        overlap_bottom = min(y2, y4)

        if overlap_right <= overlap_left or overlap_bottom <= overlap_top:
            return 0.0

        overlap_area = (overlap_right - overlap_left) * (overlap_bottom - overlap_top)

        # 计算两个区域的总面积
        area1 = (x2 - x1) * (y2 - y1)
        area2 = (x4 - x3) * (y4 - y3)

        # 计算重叠度（相对于较小区域）
        min_area = min(area1, area2)
        if min_area == 0:
            return 0.0

        return overlap_area / min_area

    def _get_top_level_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """获取最上层的元素，过滤被遮挡的元素"""
        if not elements:
            return []

        # 按照优先级排序：重要的小元素优先，然后是交互元素
        def get_element_priority(e):
            # 计算元素面积
            area = (e.bounds.right - e.bounds.left) * (e.bounds.bottom - e.bounds.top)

            # 基础优先级分数（分数越低优先级越高）
            priority = 0

            # 1. 重要且面积小的元素（如按钮）优先级最高
            if e.important and area < 50000:
                priority += 0
            elif e.important:
                priority += 2
            else:
                priority += 4

            # 2. 交互元素优先
            if e.clickable:
                priority += 0
            else:
                priority += 1

            # 3. 有内容的元素优先
            if e.text or e.content_desc:
                priority += 0
            else:
                priority += 2

            # 4. 非布局容器优先
            if e.class_name not in ['android.widget.FrameLayout', 'android.widget.LinearLayout', 'android.widget.RelativeLayout']:
                priority += 0
            else:
                priority += 3

            # 5. 面积适中的元素优先（避免过小的噪声）
            if 100 < area < 100000:
                priority += 0
            elif area < 100:
                priority += 2
            else:
                priority += 1

            return priority, area

        sorted_elements = sorted(elements, key=get_element_priority)

        top_level_elements = []

        for element in sorted_elements:
            # 检查是否与已选择的元素重叠过多
            is_covered = False
            for selected in top_level_elements:
                if self._is_element_covered(element, selected):
                    is_covered = True
                    break

            if not is_covered:
                top_level_elements.append(element)

        return top_level_elements

    def _is_element_covered(self, element1: UIElement, element2: UIElement) -> bool:
        """判断element1是否被element2遮挡"""
        # 计算两个元素的重叠区域
        overlap_left = max(element1.bounds.left, element2.bounds.left)
        overlap_top = max(element1.bounds.top, element2.bounds.top)
        overlap_right = min(element1.bounds.right, element2.bounds.right)
        overlap_bottom = min(element1.bounds.bottom, element2.bounds.bottom)

        if overlap_right <= overlap_left or overlap_bottom <= overlap_top:
            return False  # 没有重叠

        overlap_area = (overlap_right - overlap_left) * (overlap_bottom - overlap_top)
        element1_area = (element1.bounds.right - element1.bounds.left) * (element1.bounds.bottom - element1.bounds.top)

        if element1_area == 0:
            return False

        overlap_ratio = overlap_area / element1_area

        # 如果重叠比例超过50%，认为被遮挡（降低阈值）
        if overlap_ratio > 0.5:
            return True

        # 特殊情况1：任何元素被重要的容器元素遮挡且重叠>30%
        if (element2.important and
            element2.class_name in ['android.widget.FrameLayout', 'android.widget.LinearLayout', 'android.widget.RelativeLayout'] and
            overlap_ratio > 0.3):
            return True

        # 特殊情况2：小的交互元素被大的容器元素遮挡
        if (element1.class_name in ['android.widget.Button', 'android.widget.EditText', 'android.widget.ImageButton', 'android.widget.TextView'] and
            element2.class_name in ['android.widget.FrameLayout', 'android.widget.LinearLayout', 'android.widget.RelativeLayout'] and
            overlap_ratio > 0.4):
            return True

        # 特殊情况3：不重要的文本元素被任何重要元素遮挡
        if (not element1.important and element1.class_name == 'android.widget.TextView' and
            element2.important and overlap_ratio > 0.3):
            return True

        return False

    def _filter_xml_elements_only(self, xml_elements: List[UIElement]) -> List[UIElement]:
        """只基于XML元素进行过滤和标注，不使用图像识别"""
        elements_to_annotate = []

        # 直接遍历所有XML元素，根据可见性和重要性进行过滤
        for element in xml_elements:
            if self._should_annotate_element_general(element):
                elements_to_annotate.append(element)

        # 应用最上层元素过滤
        elements_to_annotate = self._get_top_level_elements(elements_to_annotate)

        return elements_to_annotate

    def _filter_elements_by_image_content(self, xml_elements: List[UIElement], image_contents: List) -> List[UIElement]:
        """基于图像内容智能过滤要标注的元素"""
        elements_to_annotate = []

        # 按优先级排序的图像内容类型
        priority_content_types = [
            'search_input',    # 搜索框（最高优先级）
            'input',           # 输入框
            'button_text',     # 按钮文本
            'button',          # 按钮
            'link_text',       # 链接文本
            'text',            # 普通文本
            'icon'             # 图标
        ]

        # 创建内容类型到元素的映射
        content_to_elements = {}
        for content in image_contents:
            content_type = content.get('content_type', 'unknown')
            if content_type not in content_to_elements:
                content_to_elements[content_type] = []
            content_to_elements[content_type].append(content)

        # 1. 首先添加高优先级的图像识别内容
        for content_type in priority_content_types:
            if content_type in content_to_elements:
                for content in content_to_elements[content_type]:
                    matched_element = self._find_best_matching_element(content, xml_elements)
                    if matched_element and matched_element not in elements_to_annotate:
                        elements_to_annotate.append(matched_element)

        # 2. 添加重要的XML元素（未被图像识别覆盖的）
        important_xml_elements = self._get_important_xml_elements(xml_elements)
        for element in important_xml_elements:
            if element not in elements_to_annotate:
                # 检查是否与已标注的元素重叠过多
                if not self._is_overlapping_with_annotated(element, elements_to_annotate):
                    elements_to_annotate.append(element)

        # 3. 添加其他符合条件的元素（限制数量避免过度标注）
        remaining_elements = [e for e in xml_elements if e not in elements_to_annotate]
        for element in remaining_elements:
            if self._should_annotate_element(element):
                # 进一步过滤：避免标注过多相似元素
                if self._should_include_element(element, elements_to_annotate):
                    elements_to_annotate.append(element)

        # 4. 去重和清理
        elements_to_annotate = self._deduplicate_elements(elements_to_annotate)

        # 5. 最后过滤：只保留最上层的元素
        elements_to_annotate = self._get_top_level_elements(elements_to_annotate)

        return elements_to_annotate

    def _find_best_matching_element(self, content: Dict, xml_elements: List[UIElement]) -> Optional[UIElement]:
        """为图像内容找到最佳匹配的XML元素"""
        if not xml_elements:
            return None

        content_bounds = content.get('bounds', {})
        if not content_bounds:
            return None

        best_match = None
        best_score = 0

        for element in xml_elements:
            # 调整XML元素坐标
            elem_top = element.bounds.top - 36  # 减去状态栏
            elem_bottom = element.bounds.bottom - 36

            # 计算重叠度
            overlap = self._calculate_overlap(
                content_bounds['left'], content_bounds['top'],
                content_bounds['right'], content_bounds['bottom'],
                element.bounds.left, elem_top,
                element.bounds.right, elem_bottom
            )

            # 文本匹配度
            text_score = 0
            content_text = content.get('text', '').lower()
            if content_text:
                # 与元素文本匹配
                if element.text and content_text in element.text.lower():
                    text_score = 1.0
                elif element.content_desc and content_text in element.content_desc.lower():
                    text_score = 0.8
                elif element.resource_id and any(keyword in element.resource_id.lower() for keyword in content_text.split()):
                    text_score = 0.6

            # 类型匹配度
            type_score = 0
            content_type = content.get('content_type', '')
            if content_type == 'search_input' and element.class_name == 'android.widget.EditText':
                type_score = 1.0
            elif content_type == 'button' and element.clickable:
                type_score = 0.8
            elif content_type == 'text' and element.text:
                type_score = 0.6

            # 综合评分
            total_score = overlap * 0.5 + text_score * 0.3 + type_score * 0.2

            if total_score > best_score and total_score > 0.4:
                best_score = total_score
                best_match = element

        return best_match

    def _get_important_xml_elements(self, xml_elements: List[UIElement]) -> List[UIElement]:
        """获取重要的XML元素"""
        important_elements = []

        for element in xml_elements:
            # 重要的可点击元素
            if element.clickable and (element.text or element.content_desc):
                important_elements.append(element)

            # 重要的文本元素
            elif element.important and element.text:
                important_elements.append(element)

            # 搜索框和输入框
            elif element.class_name in ['android.widget.EditText', 'android.widget.AutoCompleteTextView']:
                important_elements.append(element)

            # 按钮
            elif element.class_name in ['android.widget.Button', 'android.widget.ImageButton']:
                important_elements.append(element)

        return important_elements

    def _is_overlapping_with_annotated(self, element: UIElement, annotated_elements: List[UIElement]) -> bool:
        """检查元素是否与已标注元素重叠过多"""
        for annotated in annotated_elements:
            overlap = self._calculate_element_overlap(element, annotated)
            if overlap > 0.8:  # 重叠度超过80%
                return True
        return False

    def _calculate_element_overlap(self, elem1: UIElement, elem2: UIElement) -> float:
        """计算两个元素的重叠度"""
        # 调整坐标
        top1 = elem1.bounds.top - 36
        bottom1 = elem1.bounds.bottom - 36
        top2 = elem2.bounds.top - 36
        bottom2 = elem2.bounds.bottom - 36

        return self._calculate_overlap(
            elem1.bounds.left, top1, elem1.bounds.right, bottom1,
            elem2.bounds.left, top2, elem2.bounds.right, bottom2
        )

    def _should_include_element(self, element: UIElement, annotated_elements: List[UIElement]) -> bool:
        """判断是否应该包含该元素（避免过度标注）"""
        # 过滤掉一些不重要的元素
        if element.class_name in ['android.widget.FrameLayout', 'android.widget.LinearLayout']:
            return False

        # 如果已经有太多相似类型的元素，跳过
        similar_count = sum(1 for e in annotated_elements if e.class_name == element.class_name)
        if similar_count >= 10:  # 同类型元素不超过10个
            return False

        # 过滤过小的元素
        width = element.bounds.right - element.bounds.left
        height = element.bounds.bottom - element.bounds.top
        if width < 15 or height < 8:
            return False

        return True

    def _deduplicate_elements(self, elements: List[UIElement]) -> List[UIElement]:
        """去重相似的元素"""
        unique_elements = []
        seen_positions = set()

        for element in elements:
            # 创建位置键
            pos_key = (
                round(element.bounds.left / 10),  # 10px精度
                round(element.bounds.top / 10),
                round(element.bounds.right / 10),
                round(element.bounds.bottom / 10)
            )

            if pos_key not in seen_positions:
                seen_positions.add(pos_key)
                unique_elements.append(element)

        return unique_elements

    def _divide_page_regions(self, elements: List[UIElement]) -> List[Dict]:
        """划分页面大区域"""
        regions = []

        # 计算状态栏高度
        status_bar_height = 36

        # 分析页面结构
        top_elements = []
        middle_elements = []
        bottom_elements = []

        for element in elements:
            adjusted_top = element.bounds.top - status_bar_height

            # 顶部区域（标题栏）：0-200px
            if adjusted_top <= 200:
                top_elements.append(element)

            # 底部区域（功能切换栏）：1000px以下
            elif adjusted_top >= 1000:
                bottom_elements.append(element)

            # 中间区域（内容展示）
            else:
                middle_elements.append(element)

        # 创建顶部区域
        if top_elements:
            top_bounds = self._calculate_region_bounds(top_elements, status_bar_height)
            regions.append({
                'name': '标题区域',
                'type': 'title',
                'bounds': top_bounds,
                'color': '#3498db',  # 蓝色
                'elements': top_elements
            })

        # 创建中间区域
        if middle_elements:
            middle_bounds = self._calculate_region_bounds(middle_elements, status_bar_height)
            regions.append({
                'name': '内容展示区域',
                'type': 'content',
                'bounds': middle_bounds,
                'color': '#2ecc71',  # 绿色
                'elements': middle_elements
            })

        # 创建底部区域
        if bottom_elements:
            bottom_bounds = self._calculate_region_bounds(bottom_elements, status_bar_height)
            regions.append({
                'name': '功能切换区域',
                'type': 'navigation',
                'bounds': bottom_bounds,
                'color': '#f39c12',  # 橙色
                'elements': bottom_elements
            })

        return regions

    def _calculate_region_bounds(self, elements: List[UIElement], status_bar_height: int) -> Dict:
        """计算区域边界"""
        if not elements:
            return {'left': 0, 'top': 0, 'right': 0, 'bottom': 0}

        min_left = min(e.bounds.left for e in elements)
        min_top = min(e.bounds.top for e in elements) - status_bar_height
        max_right = max(e.bounds.right for e in elements)
        max_bottom = max(e.bounds.bottom for e in elements) - status_bar_height

        # 扩展边界以包含完整区域
        padding = 10
        return {
            'left': max(0, min_left - padding),
            'top': max(0, min_top - padding),
            'right': min(self.screen_width, max_right + padding),
            'bottom': min(self.screen_height - status_bar_height, max_bottom + padding)
        }

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

    def _is_effectively_clickable(self, element: UIElement) -> bool:
        """基于父元素二次判断元素是否实际可点击"""
        # 如果元素本身是可点击的，直接返回True
        if element.clickable:
            return True

        # 向上搜索相同类型的可点击父节点
        current = element.parent
        while current:
            # 只检查相同类型的父节点
            if current.class_name == element.class_name and current.clickable:
                return True

            # 检查父节点是否为可点击的容器（特殊情况处理）
            if current.clickable:
                container_types = [
                    'android.widget.FrameLayout',
                    'android.widget.LinearLayout',
                    'android.widget.RelativeLayout'
                ]

                if current.class_name in container_types:
                    # 只有特定类型的子元素才可能继承容器的可点击性
                    if element.class_name == 'android.widget.TextView':
                        # 检查是否为明确的按钮文本
                        if element.text:
                            text = element.text.strip()
                            button_keywords = [
                                '确定', '取消', '确认', '提交', '登录', '注册', '返回', '关闭',
                                '下一步', '完成', '删除', '编辑', '保存', '搜索', '查询',
                                '手动定位', '更新定位', '重新加载', '刷新', '重试'
                            ]

                            for keyword in button_keywords:
                                if keyword in text:
                                    return True

                    elif element.class_name == 'android.widget.ImageView':
                        # 有描述内容的ImageView可能是可点击的
                        if element.content_desc and element.content_desc.strip():
                            return True

            current = current.parent

        return False

    def _should_annotate_element_general(self, element: UIElement) -> bool:
        """精简版XML页面元素标注逻辑"""

        # 首先检查元素可见性
        if not self._is_element_visible(element):
            return False

        # 1. 彻底禁用所有FrameLayout（无论是否重要）
        if element.class_name == 'android.widget.FrameLayout':
            return False

        # 2. 禁用其他布局容器（除非非常重要）
        layout_classes = [
            'android.widget.LinearLayout',
            'android.widget.RelativeLayout',
            'android.view.ViewGroup'
        ]

        if element.class_name in layout_classes and not element.important:
            return False

        # 3. 禁用没有内容的TextView
        if element.class_name == 'android.widget.TextView':
            has_content = (element.text and element.text.strip()) or (element.content_desc and element.content_desc.strip())
            if not has_content:
                return False

        # 4. 禁用没有内容的ImageView
        if element.class_name == 'android.widget.ImageView':
            has_content = (element.content_desc and element.content_desc.strip())
            if not has_content:
                return False

        # 5. 优先级1：重要的非容器元素
        if element.important and element.class_name not in layout_classes:
            return True

        # 6. 优先级2：可点击的交互元素
        if element.clickable:
            return True

        # 7. 优先级3：有实质内容的元素
        has_real_content = False

        # 有意义的文本内容（长度≥2）
        if element.text and len(element.text.strip()) >= 2:
            # 过滤掉无意义的文本
            text = element.text.strip()
            if text not in ['', ' ', '\n', '\t', '\r\n']:
                has_real_content = True

        # 有意义的描述内容
        if element.content_desc and len(element.content_desc.strip()) >= 2:
            has_real_content = True

        if has_real_content:
            return True

        # 8. 重要的UI组件类型（即使没有内容也标注）
        important_components = [
            'android.widget.Button',
            'android.widget.EditText',
            'android.widget.ImageButton',
            'android.widget.CheckBox',
            'android.widget.RadioButton',
            'android.widget.Spinner',
            'android.widget.ToggleButton'
        ]

        if element.class_name in important_components:
            return True

        # 9. 跳过纯View元素
        if element.class_name == 'android.view.View':
            return False

        # 10. 跳过过小的元素（进一步提高阈值）
        element_width = element.bounds.right - element.bounds.left
        element_height = element.bounds.bottom - element.bounds.top
        if element_width < 15 or element_height < 8:
            return False

        # 11. 跳过负坐标区域
        if element.bounds.left < 0:
            return False

        # 12. 跳过系统UI和提示文本
        if element.text and (
            "可竖向滚动" in element.text or
            "可横向滚动" in element.text or
            element.text.strip() in ['', ' ', '\n', '\t']
        ):
            return False

        # 13. 跳过状态栏等系统UI
        if element.bounds.top < 36:  # 状态栏高度
            return False

        # 14. 检查是否在合理的高度范围内
        adjusted_top = element.bounds.top - 36
        if adjusted_top < 0 or adjusted_top > 1100:
            return False

        return False

    def _generate_html_content(self, image_base64: str, regions: List[Dict], elements: List[UIElement], image_contents: List, xml_stats: Dict = None, actually_clickable_count: int = 0) -> str:
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
            max-width: 1400px;
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
        .main-content {{
            display: flex;
            height: calc(100vh - 200px);
        }}
        .left-panel {{
            flex: 1;
            padding: 20px;
            border-right: 2px solid #ecf0f1;
            overflow-y: auto;
        }}
        .right-panel {{
            width: 400px;
            padding: 20px;
            background-color: #f8f9fa;
            overflow-y: auto;
        }}
        .control-panel {{
            background-color: #e9ecef;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            border: 1px solid #dee2e6;
        }}
        .control-panel h4 {{
            margin: 0 0 15px 0;
            color: #495057;
            font-size: 14px;
            font-weight: bold;
        }}
        .control-item {{
            display: flex;
            align-items: center;
            margin-bottom: 10px;
            padding: 8px;
            background-color: white;
            border-radius: 4px;
            transition: background-color 0.2s ease;
        }}
        .control-item:hover {{
            background-color: #f8f9fa;
        }}
        .control-item:last-child {{
            margin-bottom: 0;
        }}
        .control-checkbox {{
            margin-right: 10px;
            transform: scale(1.2);
        }}
        .control-label {{
            flex: 1;
            font-size: 13px;
            color: #495057;
            cursor: pointer;
            user-select: none;
        }}
        .control-icon {{
            margin-right: 8px;
            font-size: 14px;
        }}
        .section-hidden {{
            display: none !important;
        }}
        .toggle-btn {{
            background: none;
            border: none;
            color: #6c757d;
            cursor: pointer;
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 3px;
            transition: all 0.2s ease;
        }}
        .toggle-btn:hover {{
            background-color: #e9ecef;
            color: #495057;
        }}
        .image-container {{
            position: relative;
            display: inline-block;
            border: 1px solid #ddd;
            max-width: 100%;
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
        .annotation.element-annotation {{
            border-color: #e74c3c;
            background-color: rgba(231, 76, 60, 0.1);
        }}
        .annotation.region-annotation {{
            border-color: #3498db;
            background-color: rgba(52, 152, 219, 0.1);
        }}
        .annotation.image-content-annotation {{
            border-color: #9b59b6;
            background-color: rgba(155, 89, 182, 0.1);
        }}
        .annotation:hover {{
            border-color: #c0392b;
            background-color: rgba(231, 76, 60, 0.2);
            box-shadow: 0 0 10px rgba(231, 76, 60, 0.5);
        }}
        .annotation.highlighted {{
            animation: highlightPulse 2s ease-in-out;
            border-width: 4px !important;
            z-index: 200 !important;
            transform: scale(1.02);
            transition: all 0.3s ease;
        }}
        .annotation.element-annotation.highlighted {{
            border-color: #e74c3c !important;
            background-color: rgba(231, 76, 60, 0.3) !important;
            box-shadow: 0 0 30px rgba(231, 76, 60, 0.8), 0 0 60px rgba(231, 76, 60, 0.4) !important;
        }}
        .annotation.region-annotation.highlighted {{
            border-color: #3498db !important;
            background-color: rgba(52, 152, 219, 0.3) !important;
            box-shadow: 0 0 30px rgba(52, 152, 219, 0.8), 0 0 60px rgba(52, 152, 219, 0.4) !important;
        }}
        .annotation.image-content-annotation.highlighted {{
            border-color: #9b59b6 !important;
            background-color: rgba(155, 89, 182, 0.3) !important;
            box-shadow: 0 0 30px rgba(155, 89, 182, 0.8), 0 0 60px rgba(155, 89, 182, 0.4) !important;
        }}
        @keyframes highlightPulse {{
            0% {{
                transform: scale(1);
                box-shadow: 0 0 20px rgba(255, 215, 0, 0.8);
            }}
            50% {{
                transform: scale(1.05);
                box-shadow: 0 0 40px rgba(255, 215, 0, 1), 0 0 80px rgba(255, 215, 0, 0.6);
            }}
            100% {{
                transform: scale(1.02);
                box-shadow: 0 0 30px rgba(255, 215, 0, 0.9), 0 0 60px rgba(255, 215, 0, 0.4);
            }}
        }}
        .region {{
            position: absolute;
            border: 3px solid;
            background-color: rgba(52, 152, 219, 0.05);
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 1;
        }}
        .region:hover {{
            background-color: rgba(52, 152, 219, 0.15);
            box-shadow: 0 0 15px rgba(52, 152, 219, 0.4);
        }}
        .region-title {{
            position: absolute;
            top: -25px;
            left: 0;
            background-color: #2c3e50;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .region-info {{
            position: absolute;
            bottom: -20px;
            left: 0;
            background-color: rgba(44, 62, 80, 0.8);
            color: white;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 10px;
            white-space: nowrap;
        }}
        .image-content {{
            position: absolute;
            border: 3px solid #9b59b6;
            background-color: rgba(155, 89, 182, 0.1);
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 5;
        }}
        .image-content:hover {{
            background-color: rgba(155, 89, 182, 0.2);
            box-shadow: 0 0 15px rgba(155, 89, 182, 0.6);
        }}
        .image-content-label {{
            position: absolute;
            top: -25px;
            left: 0;
            background-color: #9b59b6;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        .ocr-annotation {{
            position: absolute;
            border: 2px solid #e67e22;
            background-color: rgba(230, 126, 34, 0.1);
            cursor: pointer;
            transition: all 0.3s ease;
            z-index: 6;
        }}
        .ocr-annotation:hover {{
            background-color: rgba(230, 126, 34, 0.2);
            box-shadow: 0 0 15px rgba(230, 126, 34, 0.6);
        }}
        .ocr-annotation.highlighted {{
            border-color: #d35400 !important;
            background-color: rgba(230, 126, 34, 0.3) !important;
            box-shadow: 0 0 30px rgba(230, 126, 34, 0.8), 0 0 60px rgba(230, 126, 34, 0.4) !important;
        }}
        .ocr-label {{
            position: absolute;
            top: -25px;
            left: 0;
            background-color: #e67e22;
            color: white;
            padding: 3px 6px;
            border-radius: 3px;
            font-size: 10px;
            font-weight: bold;
            white-space: nowrap;
            box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }}
        .ocr-confidence {{
            position: absolute;
            bottom: -18px;
            right: 0;
            background-color: rgba(52, 73, 94, 0.8);
            color: white;
            padding: 1px 4px;
            border-radius: 2px;
            font-size: 8px;
            font-weight: normal;
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
            <h1>📱 XML UI元素标注分析 + 🔤 OCR文字识别</h1>
            <p>屏幕尺寸: {self.screen_width} × {self.screen_height} 像素 | 支持智能文字识别与XML元素匹配</p>
        </div>

        <div class="main-content">
            <!-- 左侧：标注页面 -->
            <div class="left-panel">
                <div class="stats">
                    <h3>📊 统计信息</h3>
                    <div class="stats-grid">
                        <div class="stat-item">
                            <div class="stat-number">{xml_stats['coordinate_elements'] if xml_stats else 0}</div>
                            <div class="stat-label">坐标组件</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{xml_stats['visible_coordinate_elements'] if xml_stats else 0}</div>
                            <div class="stat-label">可见区域</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{xml_stats['invisible_coordinate_elements'] if xml_stats else 0}</div>
                            <div class="stat-label">不可见区域</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{actually_clickable_count}</div>
                            <div class="stat-label">可点击元素</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{len([c for c in image_contents if c.get('is_ocr', False)])}</div>
                            <div class="stat-label">OCR文字块</div>
                        </div>
                        <div class="stat-item">
                            <div class="stat-number">{len([c for c in image_contents if c.get('matched', False) and c.get('is_ocr', False)])}</div>
                            <div class="stat-label">匹配成功</div>
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

        # 添加页面区域
        for i, region in enumerate(regions):
            region_width = region['bounds']['right'] - region['bounds']['left']
            region_height = region['bounds']['bottom'] - region['bounds']['top']
            region_elements_count = len(region['elements'])

            html += f"""                <div class="annotation region-annotation"
                     style="left: {region['bounds']['left']}px; top: {region['bounds']['top']}px;
                            width: {region_width}px; height: {region_height}px;
                            border-color: {region['color']};"
                     data-region="{i}"
                     data-annotation-type="region">
                    <div class="region-title">{region['name']}</div>
                    <div class="region-info">{region_elements_count} 个元素</div>
                </div>
"""

        # 添加图像内容标注
        ocr_index = 0
        for i, content in enumerate(image_contents):
            if 'bounds' in content:
                bounds = content['bounds']
                content_width = bounds['right'] - bounds['left']
                content_height = bounds['bottom'] - bounds['top']
                content_type = content.get('content_type', 'unknown')
                content_text = content.get('text', '未知内容')

                # 检查是否是OCR内容
                is_ocr = content.get('is_ocr', False)
                source = content.get('source', 'unknown')

                if is_ocr:
                    # OCR标注
                    confidence = content.get('confidence', 0)
                    matched = content.get('matched', False)
                    xml_class = content.get('xml_class_name', '')

                    # 设置标签
                    label = f'🔤 OCR'
                    if matched:
                        label += f' [{xml_class.split(".")[-1] if "." in xml_class else xml_class}]'

                    html += f"""                <div class="annotation ocr-annotation"
                             style="left: {bounds['left']}px; top: {bounds['top']}px;
                                    width: {content_width}px; height: {content_height}px;"
                             data-ocr="{ocr_index}"
                             data-annotation-type="ocr">
                            <div class="ocr-label">{label}: {content_text[:20]}</div>
                            <div class="ocr-confidence">{confidence:.1%}</div>
                        </div>
"""
                    ocr_index += 1
                else:
                    # 传统图像内容标注
                    type_labels = {
                        'search_input': '🔍 搜索框',
                        'input': '📝 输入框',
                        'button_text': '🔘 按钮',
                        'button': '🔘 按钮',
                        'link_text': '🔗 链接',
                        'text': '📝 文本',
                        'icon': '🎯 图标'
                    }
                    label = type_labels.get(content_type, f'📍 {content_type}')

                    html += f"""                <div class="annotation image-content-annotation"
                             style="left: {bounds['left']}px; top: {bounds['top']}px;
                                    width: {content_width}px; height: {content_height}px;"
                             data-image-content="{i}"
                             data-annotation-type="image-content">
                            <div class="image-content-label">{label}: {content_text[:15]}</div>
                        </div>
"""

        # 添加标注框
        for i, element in enumerate(elements):
            label = self._get_element_label(element)
            # 调整坐标：页面内容从Y=36开始（状态栏区域），需要减去偏移量
            status_bar_offset = 36  # 状态栏高度
            adjusted_top = element.bounds.top - status_bar_offset
            adjusted_left = element.bounds.left

            html += f"""                <div class="annotation element-annotation"
                     style="left: {adjusted_left}px; top: {adjusted_top}px;
                            width: {element.bounds.right - element.bounds.left}px;
                            height: {element.bounds.bottom - element.bounds.top}px;"
                     data-element="{i}"
                     data-annotation-type="element">
                    <div class="annotation-label"
                         style="left: 0px; top: -20px;">{label}</div>
                </div>
"""

        html += """
            </div>

            <!-- 禁用图像识别内容显示 -->
            <div class="elements-list">
"""

        # 禁用图像内容列表显示
        # for i, content in enumerate(image_contents):
        #     if 'bounds' in content:
        #         bounds = content['bounds']
        #         content_width = bounds['right'] - bounds['left']
        #         content_height = bounds['bottom'] - bounds['top']
        #         content_type = content.get('content_type', 'unknown')
        #         content_text = content.get('text', '未知内容')
        #         confidence = content.get('confidence', 0)
        #
        #         # 类型图标
        #         type_icons = {
        #             'search_input': '🔍',
        #             'input': '📝',
        #             'button_text': '🔘',
        #             'button': '🔘',
        #             'link_text': '🔗',
        #             'text': '📝',
        #             'icon': '🎯'
        #         }
        #         icon = type_icons.get(content_type, '📍')
        #
        #         html += f"""                <div class="element-item" data-image-content="{i}">
        #             <div class="element-title" style="color: #9b59b6;">{icon} {content_type.upper()}</div>
        #             <div class="element-info">
        #                 内容: {content_text}<br>
        #                 坐标: <span class="coordinates">{bounds['left']},{bounds['top']} - {bounds['right']},{bounds['bottom']}</span><br>
        #                 尺寸: {content_width} × {content_height}<br>
        #                 置信度: {confidence:.1%}
        #             </div>
        #         </div>
        # """

        html += """
            </div>
            </div>

            <!-- 右侧：数据面板 -->
            <div class="right-panel">
                <!-- 控制面板 -->
                <div class="control-panel">
                    <h4>🎛️ 显示控制</h4>
                    <div class="control-item">
                        <input type="checkbox" id="toggle-elements" class="control-checkbox" checked>
                        <label for="toggle-elements" class="control-label">
                            <span class="control-icon">📋</span>
                            标注元素列表
                        </label>
                        <button class="toggle-btn" onclick="toggleSection('elements-section')">切换</button>
                    </div>
                    <div class="control-item">
                        <input type="checkbox" id="toggle-regions" class="control-checkbox" checked>
                        <label for="toggle-regions" class="control-label">
                            <span class="control-icon">🗺️</span>
                            页面区域划分
                        </label>
                        <button class="toggle-btn" onclick="toggleSection('regions-section')">切换</button>
                    </div>
                    <div class="control-item">
                        <input type="checkbox" id="toggle-image-content" class="control-checkbox" checked>
                        <label for="toggle-image-content" class="control-label">
                            <span class="control-icon">🔍</span>
                            图像识别结果
                        </label>
                        <button class="toggle-btn" onclick="toggleSection('image-content-section')">切换</button>
                    </div>
                    <div class="control-item">
                        <input type="checkbox" id="toggle-xml-stats" class="control-checkbox" checked>
                        <label for="toggle-xml-stats" class="control-label">
                            <span class="control-icon">📋</span>
                            XML分析统计
                        </label>
                    </div>
                    <div class="control-item">
                        <input type="checkbox" id="toggle-ocr" class="control-checkbox" checked onchange="toggleOCRAnnotations()">
                        <label for="toggle-ocr" class="control-label">
                            <span class="control-icon">🔤</span>
                            OCR文字标注
                        </label>
                    </div>
                </div>

                <!-- 标注元素列表 -->
                <div id="elements-section">
                    <h3>📋 标注元素列表</h3>
                <div class="elements-list">
"""
        # 添加元素列表
        for i, element in enumerate(elements):
            html += f"""                    <div class="element-item" data-element="{i}">
                        <div class="element-title">{self._get_element_label(element)}</div>
                        <div class="element-info">
                            类型: {element.class_name}<br>
                            坐标: <span class="coordinates">{element.bounds.left},{element.bounds.top} - {element.bounds.right},{element.bounds.bottom}</span><br>
                            尺寸: {element.bounds.right - element.bounds.left} × {element.bounds.bottom - element.bounds.top}<br>
                            可见度: {getattr(element, 'visibility_percentage', 100):.1f}% |
                            重要: {'是' if element.important else '否'} |
                            可点击: {'是' if self._is_effectively_clickable(element) else '否'}
                        </div>
                    </div>
"""
        html += """
                </div>

                </div>

                <!-- 页面区域划分 -->
                <div id="regions-section">
                    <h3>🗺️ 页面区域划分</h3>
                    <div class="elements-list">
"""
        # 添加区域列表
        for i, region in enumerate(regions):
            region_width = region['bounds']['right'] - region['bounds']['left']
            region_height = region['bounds']['bottom'] - region['bounds']['top']
            html += f"""                    <div class="element-item" data-region="{i}">
                        <div class="element-title" style="color: {region['color']};">📍 {region['name']}</div>
                        <div class="element-info">
                            类型: {region['type']}<br>
                            坐标: <span class="coordinates">{region['bounds']['left']},{region['bounds']['top']} - {region['bounds']['right']},{region['bounds']['bottom']}</span><br>
                            尺寸: {region_width} × {region_height}<br>
                            包含元素: {len(region['elements'])} 个
                        </div>
                    </div>
"""
        html += """
                </div>

                </div>

                <!-- 图像识别结果 -->
                <div id="image-content-section">
                    <h3>🔍 图像识别结果</h3>
                    <div class="elements-list">
"""
        # 分别显示OCR结果和传统分析结果
        ocr_count = 0
        image_analysis_count = 0

        for i, content in enumerate(image_contents):
            if 'bounds' in content:
                bounds = content['bounds']
                content_width = bounds['right'] - bounds['left']
                content_height = bounds['bottom'] - bounds['top']
                content_type = content.get('content_type', 'unknown')
                content_text = content.get('text', '未知内容')
                confidence = content.get('confidence', 0)
                is_ocr = content.get('is_ocr', False)
                source = content.get('source', 'unknown')
                matched = content.get('matched', False)
                xml_class = content.get('xml_class_name', '')

                if is_ocr:
                    # OCR结果
                    ocr_count += 1
                    matched_status = "✅ 已匹配" if matched else "❌ 未匹配"
                    xml_info = f" [{xml_class.split('.')[-1] if '.' in xml_class else xml_class}]" if matched else ""

                    html += f"""                    <div class="element-item" data-ocr="{ocr_count - 1}">
                        <div class="element-title" style="color: #e67e22;">🔤 OCR文字识别{xml_info}</div>
                        <div class="element-info">
                            文字: {content_text}<br>
                            坐标: <span class="coordinates">{bounds['left']},{bounds['top']} - {bounds['right']},{bounds['bottom']}</span><br>
                            尺寸: {content_width} × {content_height}<br>
                            置信度: {confidence:.1f}% | {matched_status}
                        </div>
                    </div>
"""
                else:
                    # 传统图像分析结果
                    image_analysis_count += 1
                    # 类型图标
                    type_icons = {
                        'search_input': '🔍',
                        'input': '📝',
                        'button_text': '🔘',
                        'button': '🔘',
                        'link_text': '🔗',
                        'text': '📝',
                        'icon': '🎯'
                    }
                    icon = type_icons.get(content_type, '📍')

                    html += f"""                    <div class="element-item" data-image-content="{image_analysis_count - 1}">
                        <div class="element-title" style="color: #9b59b6;">{icon} {content_type.upper()}</div>
                        <div class="element-info">
                            内容: {content_text}<br>
                            坐标: <span class="coordinates">{bounds['left']},{bounds['top']} - {bounds['right']},{bounds['bottom']}</span><br>
                            尺寸: {content_width} × {content_height}<br>
                            置信度: {confidence:.1f}%
                        </div>
                    </div>
"""
        html += """
                </div>

                </div>

                <!-- XML分析统计 -->
                <div id="xml-stats-section">
                    <h3>📋 XML分析统计</h3>
                    <div class="elements-list">"""

        # 添加总体统计
        total_elements = xml_stats['total_elements'] if xml_stats else 0
        coordinate_elements = xml_stats['coordinate_elements'] if xml_stats else 0
        visible_coordinate_elements = xml_stats['visible_coordinate_elements'] if xml_stats else 0
        invisible_coordinate_elements = xml_stats['invisible_coordinate_elements'] if xml_stats else 0
        partially_visible = xml_stats['by_visibility']['partially_visible'] if xml_stats else 0

        html += f"""                        <div class="element-item">
                            <div class="element-title">📊 总体统计</div>
                            <div class="element-info">
                                总元素数量: {total_elements}<br>
                                坐标元素总数: {coordinate_elements}<br>
                                可见坐标元素: {visible_coordinate_elements}<br>
                                不可见坐标元素: {invisible_coordinate_elements}<br>
                                部分可见元素: {partially_visible}
                            </div>
                        </div>"""

        # 添加元素分类统计
        interactive_elements = xml_stats['interactive_elements'] if xml_stats else 0
        text_elements = xml_stats['text_elements'] if xml_stats else 0
        layout_elements = xml_stats['layout_elements'] if xml_stats else 0

        html += f"""                        <div class="element-item">
                            <div class="element-title">🎯 元素分类统计</div>
                            <div class="element-info">
                                交互元素: {interactive_elements}<br>
                                文本元素: {text_elements}<br>
                                布局元素: {layout_elements}
                            </div>
                        </div>"""

        if xml_stats and xml_stats['by_class']:
            # 添加按类名统计的前5个
            top_classes = sorted(xml_stats['by_class'].items(), key=lambda x: x[1], reverse=True)[:5]
            class_info = "<br>".join([f"{class_name}: {count}" for class_name, count in top_classes])
            html += f"""                        <div class="element-item">
                            <div class="element-title">📱 主要类名分布</div>
                            <div class="element-info">{class_info}
                            </div>
                        </div>"""

        if xml_stats and xml_stats['by_type']:
            # 添加按类型统计
            type_info = "<br>".join([f"{type_name}: {count}" for type_name, count in xml_stats['by_type'].items()])
            html += f"""                        <div class="element-item">
                            <div class="element-title">🔧 按类型统计</div>
                            <div class="element-info">{type_info}
                            </div>
                        </div>"""

        html += """
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        // 专门处理OCR标注的显示/隐藏
        function toggleOCRAnnotations() {
            const checkbox = document.getElementById('toggle-ocr');
            const isVisible = checkbox.checked;
            const ocrAnnotations = document.querySelectorAll('.annotation[data-annotation-type="ocr"]');

            ocrAnnotations.forEach(annotation => {
                if (isVisible) {
                    annotation.style.display = 'block';
                } else {
                    annotation.style.display = 'none';
                }
            });
        }

        // 切换面板显示/隐藏
        function toggleSection(sectionId) {
            const section = document.getElementById(sectionId);
            const checkbox = document.getElementById('toggle-' + sectionId.replace('-section', ''));
            const annotationType = sectionId.replace('-section', '');

            if (section) {
                const isHidden = section.classList.contains('section-hidden');

                if (isHidden) {
                    section.classList.remove('section-hidden');
                    if (checkbox) checkbox.checked = true;
                    toggleAnnotationsByType(annotationType, true);
                } else {
                    section.classList.add('section-hidden');
                    if (checkbox) checkbox.checked = false;
                    toggleAnnotationsByType(annotationType, false);
                }
            }
        }

        // 复选框变化事件
        function setupToggleListeners() {
            const checkboxes = ['toggle-elements', 'toggle-regions', 'toggle-image-content', 'toggle-xml-stats', 'toggle-ocr'];

            checkboxes.forEach(id => {
                const checkbox = document.getElementById(id);
                if (checkbox) {
                    checkbox.addEventListener('change', function() {
                        const sectionId = id.replace('toggle-', '') + '-section';
                        const section = document.getElementById(sectionId);
                        const annotationType = id.replace('toggle-', '');

                        // 控制右侧面板section的显示/隐藏
                        if (section) {
                            if (this.checked) {
                                section.classList.remove('section-hidden');
                            } else {
                                section.classList.add('section-hidden');
                            }
                        }

                        // 控制左侧标注的显示/隐藏
                        toggleAnnotationsByType(annotationType, this.checked);
                    });
                }
            });
        }

        // 根据类型控制标注的显示/隐藏
        function toggleAnnotationsByType(type, isVisible) {
            let selector = '';
            switch(type) {
                case 'elements':
                    selector = '.annotation[data-annotation-type="element"]';
                    break;
                case 'regions':
                    selector = '.annotation[data-annotation-type="region"]';
                    break;
                case 'image-content':
                    selector = '.annotation[data-annotation-type="image-content"]';
                    break;
                case 'ocr':
                    selector = '.annotation[data-annotation-type="ocr"]';
                    break;
                case 'xml-stats':
                    // XML统计信息不需要标注，仅控制右侧面板
                    break;
            }

            if (selector) {
                const annotations = document.querySelectorAll(selector);
                annotations.forEach(annotation => {
                    if (isVisible) {
                        annotation.style.display = 'block';
                    } else {
                        annotation.style.display = 'none';
                    }
                });
            }
        }

        // 添加交互功能
        document.addEventListener('DOMContentLoaded', function() {
            // 初始化切换监听器
            setupToggleListeners();

            setupAnnotationInteractions();
        });

        // 设置标注交互功能
        function setupAnnotationInteractions() {
            const annotations = document.querySelectorAll('.annotation');
            const elementItems = document.querySelectorAll('.element-item');

            // 点击标注框高亮对应的列表项
            annotations.forEach(annotation => {
                annotation.addEventListener('click', function() {
                    const annotationType = this.getAttribute('data-annotation-type');
                    let targetItem = null;
                    let targetSection = null;

                    // 根据标注类型找到对应的数据项
                    switch(annotationType) {
                        case 'element':
                            const elementId = this.getAttribute('data-element');
                            targetItem = document.querySelector(`.element-item[data-element="${elementId}"]`);
                            targetSection = document.getElementById('elements-section');
                            break;
                        case 'region':
                            const regionId = this.getAttribute('data-region');
                            targetItem = document.querySelector(`.element-item[data-region="${regionId}"]`);
                            targetSection = document.getElementById('regions-section');
                            break;
                        case 'image-content':
                            const imageContentId = this.getAttribute('data-image-content');
                            targetItem = document.querySelector(`.element-item[data-image-content="${imageContentId}"]`);
                            targetSection = document.getElementById('image-content-section');
                            break;
                        case 'ocr':
                            const ocrId = this.getAttribute('data-ocr');
                            targetItem = document.querySelector(`.element-item[data-ocr="${ocrId}"]`);
                            targetSection = document.getElementById('image-content-section');
                            break;
                    }

                    if (targetItem) {
                        // 移除所有高亮
                        elementItems.forEach(item => item.style.backgroundColor = '');

                        // 高亮目标项
                        targetItem.style.backgroundColor = '#fff3cd';

                        // 确保对应的section是可见的
                        if (targetSection && targetSection.classList.contains('section-hidden')) {
                            targetSection.classList.remove('section-hidden');
                            // 更新对应的复选框状态
                            const checkboxId = 'toggle-' + annotationType;
                            const checkbox = document.getElementById(checkboxId);
                            if (checkbox) checkbox.checked = true;
                        }

                        // 滚动到目标项
                        targetItem.scrollIntoView({ behavior: 'smooth', block: 'center' });

                        // 临时高亮标注框
                        highlightAnnotation(this);
                    }
                });
            });

            // 点击列表项高亮对应的标注框
            elementItems.forEach(item => {
                item.addEventListener('click', function() {
                    // 移除所有高亮
                    elementItems.forEach(i => i.style.backgroundColor = '');
                    document.querySelectorAll('.annotation').forEach(a => {
                        a.style.zIndex = '';
                        a.style.boxShadow = '';
                    });

                    this.style.backgroundColor = '#fff3cd';

                    // 根据不同的data属性找到对应的标注
                    let targetAnnotation = null;

                    if (this.hasAttribute('data-element')) {
                        const elementId = this.getAttribute('data-element');
                        targetAnnotation = document.querySelector(`.annotation[data-annotation-type="element"][data-element="${elementId}"]`);
                    } else if (this.hasAttribute('data-region')) {
                        const regionId = this.getAttribute('data-region');
                        targetAnnotation = document.querySelector(`.annotation[data-annotation-type="region"][data-region="${regionId}"]`);
                    } else if (this.hasAttribute('data-image-content')) {
                        const imageContentId = this.getAttribute('data-image-content');
                        targetAnnotation = document.querySelector(`.annotation[data-annotation-type="image-content"][data-image-content="${imageContentId}"]`);
                    } else if (this.hasAttribute('data-ocr')) {
                        const ocrId = this.getAttribute('data-ocr');
                        targetAnnotation = document.querySelector(`.annotation[data-annotation-type="ocr"][data-ocr="${ocrId}"]`);
                    }

                    if (targetAnnotation) {
                        highlightAnnotation(targetAnnotation);
                    }
                });
            });
        }

        // 高亮标注框
        function highlightAnnotation(annotation) {
            // 移除所有高亮
            document.querySelectorAll('.annotation').forEach(a => {
                a.classList.remove('highlighted');
            });

            // 添加高亮类到目标标注框
            annotation.classList.add('highlighted');

            // 添加高亮完成后的回调
            annotation.addEventListener('animationend', function onAnimationEnd(event) {
                if (event.animationName === 'highlightPulse') {
                    // 动画结束后保持最后的状态，移除动画类但保持高亮样式
                    annotation.style.animation = 'none';
                    annotation.style.zIndex = '150';
                    annotation.style.borderWidth = '3px';
                }
            }, { once: true });

            // 5秒后完全移除高亮
            setTimeout(() => {
                annotation.classList.remove('highlighted');
                annotation.style.animation = '';
                annotation.style.zIndex = '';
                annotation.style.borderWidth = '';
                annotation.style.transform = '';
                annotation.style.boxShadow = '';
            }, 5000);
        }
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