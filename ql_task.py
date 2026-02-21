#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青龙面板定时任务入口脚本

在青龙面板中运行本脚本，支持从环境变量读取配置
"""

import os
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.env_config import load_config_from_env
from src.main import TradingTipsApp
from loguru import logger


def main():
    """
    青龙面板任务入口
    """
    try:
        logger.info("=" * 60)
        logger.info("青龙面板 - 证券交易推荐系统")
        logger.info("=" * 60)
        
        # 从环境变量加载配置
        config = load_config_from_env()
        
        # 创建应用实例（使用环境变量配置）
        app = TradingTipsApp(config=config)
        
        # 运行应用
        app.run()
        
        logger.info("=" * 60)
        logger.info("任务执行完成")
        logger.info("=" * 60)
        
        return 0
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
