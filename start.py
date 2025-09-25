#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
便捷启动脚本
直接运行即可启动Web服务
"""

import os
import sys
import subprocess

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(__file__))

if __name__ == "__main__":
    # 切换到scripts目录
    os.chdir('scripts')
    # 启动Web服务
    subprocess.run([sys.executable, 'run.py', 'web'] + sys.argv[1:])