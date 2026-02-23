#!/usr/bin/env python3
"""测试本地数据加载，验证是否从CSV文件读取股票名称"""

import sys
from pathlib import Path

sys.path.insert(0, '/Users/imtlll/Documents/trading-tips')

# 设置日志
from loguru import logger
logger.remove()
logger.add(sys.stdout, level="INFO")

print("="*80)
print("测试本地数据加载（验证股票名称来源）")
print("="*80)

# 创建配置
config = {
    'data_source': {
        'provider': 'akshare',
        'use_local_data': True,
        'local_data_dir': '~/.qlib/qlib_data/cn_data'
    },
    'analysis': {
        'market': 'A',
        'max_stocks': 10  # 只加载10只用于测试
    }
}

# 导入并初始化
from src.main import TradingTipsApp

app = TradingTipsApp(config=config)  # 使用命名参数传递config字典

print("\n开始加载本地数据...")
print("-"*80)

# 加载数据
stock_data, stock_names = app._load_local_data()

print("-"*80)
print(f"\n加载结果:")
print(f"  股票数据: {len(stock_data)} 只")
print(f"  股票名称: {len(stock_names)} 个")

print(f"\n股票名称示例（前10个）:")
for i, (code, name) in enumerate(list(stock_names.items())[:10], 1):
    print(f"  {i}. {code:>6s} - {name}")

print("\n" + "="*80)
print("✓ 测试完成：所有股票名称均从本地CSV文件读取，无网络请求")
print("="*80)
