#!/usr/bin/env python3
"""
快速启动脚本

便捷启动证券推荐系统
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.main import main

if __name__ == '__main__':
    main()
