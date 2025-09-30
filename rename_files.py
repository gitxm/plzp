#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件重命名工具启动脚本
用于将旧格式的文件名更新为包含URL信息的新格式
"""

import sys
import os

# 添加项目路径到系统路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.tools.file_renamer import main
    main()
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保所有依赖库已安装：pip install pandas openpyxl")
except Exception as e:
    print(f"❌ 运行错误: {e}")
