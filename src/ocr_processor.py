#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OCR文字识别模块
用于从图片中提取文字并进行标注
"""

import argparse
import sys
import os
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import base64
import json

@dataclass
class OCRTextBlock:
    """OCR识别的文字块"""
    text: str
    confidence: float
    bounds: 'Bounds'  # 文字块在图片中的边界框
    language: str = 'zh'  # 识别出的语言

@dataclass
class Bounds:
    """边界框"""
    left: int
    top: int
    right: int
    bottom: int

class OCRProcessor:
    """OCR文字识别处理器"""

    def __init__(self):
        self.available_engines = self._check_available_engines()

    def _check_available_engines(self) -> List[str]:
        """检查可用的OCR引擎"""
        engines = []

        # 检查 Tesseract OCR
        try:
            import pytesseract
            from PIL import Image
            engines.append('tesseract')
        except ImportError:
            pass

        # 检查 EasyOCR
        try:
            import easyocr
            engines.append('easyocr')
        except ImportError:
            pass

        # 检查 PaddleOCR
        try:
            import paddleocr
            engines.append('paddleocr')
        except ImportError:
            pass

        return engines

    def process_image(self, image_path: str, engine: str = 'auto') -> List[OCRTextBlock]:
        """处理图片并提取文字"""
        if engine == 'auto':
            # 自动选择最佳引擎
            if 'paddleocr' in self.available_engines:
                return self._process_with_paddleocr(image_path)
            elif 'easyocr' in self.available_engines:
                return self._process_with_easyocr(image_path)
            elif 'tesseract' in self.available_engines:
                return self._process_with_tesseract(image_path)
            else:
                raise RuntimeError("没有可用的OCR引擎，请安装至少一个OCR库")
        else:
            # 使用指定的引擎
            if engine == 'tesseract' and 'tesseract' in self.available_engines:
                return self._process_with_tesseract(image_path)
            elif engine == 'easyocr' and 'easyocr' in self.available_engines:
                return self._process_with_easyocr(image_path)
            elif engine == 'paddleocr' and 'paddleocr' in self.available_engines:
                return self._process_with_paddleocr(image_path)
            else:
                raise RuntimeError(f"OCR引擎 '{engine}' 不可用")

    def _process_with_tesseract(self, image_path: str) -> List[OCRTextBlock]:
        """使用 Tesseract OCR 处理图片"""
        import pytesseract
        from PIL import Image

        print(f"使用 Tesseract OCR 处理图片: {image_path}")

        try:
            # 打开图片
            image = Image.open(image_path)

            # 获取OCR数据（包含位置信息）
            ocr_data = pytesseract.image_to_data(image, lang='chi_sim+eng', output_type=pytesseract.Output.DICT)

            text_blocks = []

            # 解析OCR结果
            for i in range(len(ocr_data['text'])):
                text = ocr_data['text'][i].strip()
                confidence = int(ocr_data['conf'][i])

                # 只保留有文字且置信度大于50的结果
                if text and confidence > 50:
                    x, y, w, h = ocr_data['left'][i], ocr_data['top'][i], ocr_data['width'][i], ocr_data['height'][i]

                    bounds = Bounds(
                        left=x,
                        top=y,
                        right=x + w,
                        bottom=y + h
                    )

                    text_blocks.append(OCRTextBlock(
                        text=text,
                        confidence=confidence / 100.0,
                        bounds=bounds
                    ))

            print(f"Tesseract OCR 识别出 {len(text_blocks)} 个文字块")
            return text_blocks

        except Exception as e:
            print(f"Tesseract OCR 处理失败: {e}")
            return []

    def _process_with_easyocr(self, image_path: str) -> List[OCRTextBlock]:
        """使用 EasyOCR 处理图片"""
        import easyocr

        print(f"使用 EasyOCR 处理图片: {image_path}")

        try:
            # 初始化读取器（第一次使用时会下载模型）
            reader = easyocr.Reader(['ch_sim', 'en'])

            # 识别图片中的文字
            results = reader.readtext(image_path)

            text_blocks = []

            for (bbox, text, confidence) in results:
                if text.strip() and confidence > 0.5:
                    # EasyOCR 返回的边界框是四个角的坐标
                    x_coords = [point[0] for point in bbox]
                    y_coords = [point[1] for point in bbox]

                    bounds = Bounds(
                        left=int(min(x_coords)),
                        top=int(min(y_coords)),
                        right=int(max(x_coords)),
                        bottom=int(max(y_coords))
                    )

                    text_blocks.append(OCRTextBlock(
                        text=text.strip(),
                        confidence=confidence,
                        bounds=bounds
                    ))

            print(f"EasyOCR 识别出 {len(text_blocks)} 个文字块")
            return text_blocks

        except Exception as e:
            print(f"EasyOCR 处理失败: {e}")
            return []

    def _process_with_paddleocr(self, image_path: str) -> List[OCRTextBlock]:
        """使用 PaddleOCR 处理图片"""
        from paddleocr import PaddleOCR

        print(f"使用 PaddleOCR 处理图片: {image_path}")

        try:
            # 初始化OCR（第一次使用时会下载模型）
            ocr = PaddleOCR(use_angle_cls=True, lang='ch')

            # 识别图片中的文字
            result = ocr.ocr(image_path, cls=True)

            text_blocks = []

            for idx in range(len(result)):
                res = result[idx]
                for line in res:
                    # 提取文字和置信度
                    text = line[1][0]
                    confidence = line[1][1]

                    if text.strip() and confidence > 0.5:
                        # 提取边界框坐标
                        bbox = line[0]
                        x_coords = [point[0] for point in bbox]
                        y_coords = [point[1] for point in bbox]

                        bounds = Bounds(
                            left=int(min(x_coords)),
                            top=int(min(y_coords)),
                            right=int(max(x_coords)),
                            bottom=int(max(y_coords))
                        )

                        text_blocks.append(OCRTextBlock(
                            text=text.strip(),
                            confidence=confidence,
                            bounds=bounds
                        ))

            print(f"PaddleOCR 识别出 {len(text_blocks)} 个文字块")
            return text_blocks

        except Exception as e:
            print(f"PaddleOCR 处理失败: {e}")
            return []

    def merge_nearby_blocks(self, text_blocks: List[OCRTextBlock], max_distance: int = 20) -> List[OCRTextBlock]:
        """合并相邻的文字块"""
        if not text_blocks:
            return []

        merged_blocks = []
        used_indices = set()

        for i, block1 in enumerate(text_blocks):
            if i in used_indices:
                continue

            # 查找相邻的块
            nearby_blocks = [block1]
            for j, block2 in enumerate(text_blocks[i+1:], i+1):
                if j in used_indices:
                    continue

                # 计算距离
                if self._are_blocks_nearby(block1, block2, max_distance):
                    nearby_blocks.append(block2)
                    used_indices.add(j)

            # 合并块
            if len(nearby_blocks) > 1:
                merged_block = self._merge_text_blocks(nearby_blocks)
                merged_blocks.append(merged_block)
            else:
                merged_blocks.append(block1)

            used_indices.add(i)

        return merged_blocks

    def _are_blocks_nearby(self, block1: OCRTextBlock, block2: OCRTextBlock, max_distance: int) -> bool:
        """判断两个文字块是否相邻"""
        # 计算边界框之间的最小距离
        x_distance = max(0, max(block1.bounds.left, block2.bounds.left) - min(block1.bounds.right, block2.bounds.right))
        y_distance = max(0, max(block1.bounds.top, block2.bounds.top) - min(block1.bounds.bottom, block2.bounds.bottom))

        # 如果水平距离或垂直距离小于阈值，认为是相邻的
        return x_distance <= max_distance or y_distance <= max_distance

    def _merge_text_blocks(self, blocks: List[OCRTextBlock]) -> OCRTextBlock:
        """合并多个文字块"""
        # 合并文字
        merged_text = ' '.join(block.text for block in blocks)

        # 计算平均置信度
        avg_confidence = sum(block.confidence for block in blocks) / len(blocks)

        # 合并边界框
        min_left = min(block.bounds.left for block in blocks)
        min_top = min(block.bounds.top for block in blocks)
        max_right = max(block.bounds.right for block in blocks)
        max_bottom = max(block.bounds.bottom for block in blocks)

        merged_bounds = Bounds(
            left=min_left,
            top=min_top,
            right=max_right,
            bottom=max_bottom
        )

        return OCRTextBlock(
            text=merged_text,
            confidence=avg_confidence,
            bounds=merged_bounds
        )

def main():
    """命令行接口"""
    parser = argparse.ArgumentParser(description='OCR文字识别工具')
    parser.add_argument('image_path', help='图片文件路径')
    parser.add_argument('--engine', choices=['auto', 'tesseract', 'easyocr', 'paddleocr'],
                       default='auto', help='OCR引擎 (默认: auto)')
    parser.add_argument('--output', '-o', help='输出JSON文件路径')
    parser.add_argument('--merge', action='store_true', help='合并相邻的文字块')

    args = parser.parse_args()

    # 检查图片文件
    if not os.path.exists(args.image_path):
        print(f"错误: 图片文件不存在: {args.image_path}")
        return 1

    try:
        # 初始化OCR处理器
        ocr = OCRProcessor()

        # 显示可用引擎
        print(f"可用OCR引擎: {ocr.available_engines}")

        # 处理图片
        text_blocks = ocr.process_image(args.image_path, args.engine)

        # 合并相邻块
        if args.merge:
            text_blocks = ocr.merge_nearby_blocks(text_blocks)

        # 输出结果
        print(f"\n识别结果 ({len(text_blocks)} 个文字块):")
        for i, block in enumerate(text_blocks):
            print(f"{i+1}. {block.text} (置信度: {block.confidence:.2f})")
            print(f"   位置: ({block.bounds.left}, {block.bounds.top}) - ({block.bounds.right}, {block.bounds.bottom})")
            print()

        # 保存到文件
        if args.output:
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

            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(result_data, f, ensure_ascii=False, indent=2)

            print(f"结果已保存到: {args.output}")

        return 0

    except Exception as e:
        print(f"错误: {e}")
        return 1

if __name__ == "__main__":
    exit(main())