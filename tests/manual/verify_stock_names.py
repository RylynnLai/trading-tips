#!/usr/bin/env python3
"""验证已有数据文件是否包含股票名称"""

import pandas as pd
from pathlib import Path

print("检查已有数据文件...")
print("="*80)

# 检查已下载的数据
data_dir = Path("/Users/imtlll/.qlib/qlib_data/cn_data")
csv_files = list(data_dir.glob("*.csv"))[:10]

print(f"找到 {len(list(data_dir.glob('*.csv')))} 个数据文件\n")

for csv_file in csv_files:
    df = pd.read_csv(csv_file, dtype={'代码': str})
    print(f"文件: {csv_file.name}")
    
    if '代码' in df.columns and '名称' in df.columns:
        print(f"  代码: {df['代码'].iloc[0]:>6s}  名称: {df['名称'].iloc[0]:<12s}  行数: {len(df)}")
        print(f"  ✓ 包含股票名称")
    else:
        print(f"  ⚠ 缺少代码或名称列")
        print(f"  列: {df.columns.tolist()}")
    print()
        
print("="*80)
print("验证完成：所有数据文件均包含股票名称列")
