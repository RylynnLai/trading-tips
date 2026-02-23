#!/usr/bin/env python3
"""测试股票数据下载和名称保存"""

import sys
sys.path.insert(0, '/Users/imtlll/Documents/trading-tips')

from download_stock_data import download_stock_data
import pandas as pd
from pathlib import Path

print("开始测试...")
print("="*80)

# 下载5只股票用于测试
success = download_stock_data(
    target_dir="/tmp/test_stock_data",
    num_stocks=5,
    start_date="20240101",
    exclude_st=True
)

if success:
    print("\n" + "="*80)
    print("测试下载成功，验证数据...")
    print("="*80)
    
    csv_files = list(Path("/tmp/test_stock_data").glob("*.csv"))
    
    for csv_file in csv_files[:5]:
        df = pd.read_csv(csv_file, dtype={'代码': str})
        print(f"\n文件: {csv_file.name}")
        print(f"  列名: {df.columns.tolist()[:5]}...")
        
        if '代码' in df.columns and '名称' in df.columns:
            print(f"  代码: {df['代码'].iloc[0]}")
            print(f"  名称: {df['名称'].iloc[0]}")
            print(f"  ✓ 股票名称保存成功")
        else:
            print(f"  ✗ 缺少代码或名称列")
    
    print("\n" + "="*80)
    print("测试完成")
    print("="*80)
else:
    print("测试下载失败")
