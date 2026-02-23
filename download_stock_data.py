"""
A股数据下载脚本

使用AKShare下载最新的A股数据到本地，用于趋势分析
数据存储路径: ~/.qlib/qlib_data/cn_data/
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger


def setup_logger():
    """配置日志"""
    logger.add(
        "logs/download_data_{time}.log",
        rotation="1 day",
        retention="7 days",
        level="INFO"
    )


def download_stock_data(target_dir="~/.qlib/qlib_data/cn_data", num_stocks=300, 
                       start_date="20200101", exclude_st=True):
    """
    使用AKShare下载A股历史数据
    
    Args:
        target_dir: 数据存储目录
        num_stocks: 下载股票数量，默认300只
        start_date: 开始日期，默认2020-01-01
        exclude_st: 是否排除ST股票，默认True
        
    Returns:
        bool: 下载是否成功
    """
    try:
        import akshare as ak
        import pandas as pd
        from tqdm import tqdm
        
    except ImportError as e:
        logger.error(f"缺少必要的库: {e}")
        print("\n错误: 缺少必要的库")
        print("请运行: pip install akshare tqdm")
        return False
    
    # 创建目标目录
    target_dir = os.path.expanduser(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    
    logger.info("="*80)
    logger.info("开始下载A股数据")
    logger.info("="*80)
    print("\n" + "="*80)
    print("A股数据下载工具")
    print("="*80)
    
    try:
        # 获取A股实时行情
        logger.info("获取A股市场数据...")
        print("\n正在获取A股市场数据...")
        
        stock_info = ak.stock_zh_a_spot_em()
        logger.info(f"获取到 {len(stock_info)} 只股票")
        
        # 筛选股票
        if exclude_st:
            original_count = len(stock_info)
            stock_info = stock_info[~stock_info['名称'].str.contains('ST|退|\\*', na=False, regex=True)]
            removed_count = original_count - len(stock_info)
            logger.info(f"排除ST股票: {removed_count} 只")
            print(f"已排除ST股票: {removed_count} 只")
        
        # 按总市值排序，取前N只
        if '总市值' in stock_info.columns:
            stock_info = stock_info.sort_values('总市值', ascending=False).head(num_stocks)
        else:
            # 如果没有总市值列，按市值或流通市值排序
            sort_col = '市值' if '市值' in stock_info.columns else stock_info.columns[0]
            logger.warning(f"未找到总市值列，使用 {sort_col} 排序")
            stock_info = stock_info.head(num_stocks)
        
        logger.info(f"筛选出 {len(stock_info)} 只股票进行下载")
        
        # 显示下载信息
        print("\n下载配置:")
        print(f"  股票数量: {len(stock_info)} 只")
        print(f"  起始日期: {start_date}")
        print(f"  结束日期: {datetime.now().strftime('%Y%m%d')}")
        print(f"  存储路径: {target_dir}")
        print(f"  排除ST股: {'是' if exclude_st else '否'}")
        print("="*80 + "\n")
        
        # 确认是否继续
        if '--yes' not in sys.argv and '-y' not in sys.argv:
            confirm = input("确认开始下载? [y/N]: ").strip().lower()
            if confirm != 'y':
                print("已取消下载")
                return False
        
        # 开始下载
        success_count = 0
        fail_count = 0
        failed_stocks = []
        
        today = datetime.now().strftime("%Y%m%d")
        
        # 创建进度条
        with tqdm(total=len(stock_info), desc="下载进度", ncols=100) as pbar:
            for idx, row in stock_info.iterrows():
                code = row['代码']
                name = row['名称']
                
                try:
                    # 下载历史数据（前复权）
                    df = ak.stock_zh_a_hist(
                        symbol=code, 
                        period="daily", 
                        start_date=start_date, 
                        end_date=today,
                        adjust="qfq"
                    )
                    
                    if df is not None and len(df) > 0:
                        # 重命名列以保持一致性
                        df = df.rename(columns={
                            '日期': '日期',
                            '股票代码': '代码',
                            '开盘': '开盘',
                            '收盘': '收盘',
                            '最高': '最高',
                            '最低': '最低',
                            '成交量': '成交量',
                            '成交额': '成交额',
                            '振幅': '振幅',
                            '涨跌幅': '涨跌幅',
                            '涨跌额': '涨跌额',
                            '换手率': '换手率'
                        })
                        
                        # 添加股票代码列（如果没有）
                        if '代码' not in df.columns:
                            df['代码'] = code
                        if '名称' not in df.columns:
                            df['名称'] = name
                        
                        # 保存数据
                        file_path = os.path.join(target_dir, f"{code}.csv")
                        df.to_csv(file_path, index=False, encoding='utf-8-sig')
                        
                        success_count += 1
                        pbar.set_postfix({'成功': success_count, '失败': fail_count})
                        
                        # 每10个打印一次进度
                        if success_count % 10 == 0:
                            logger.info(f"已完成 {success_count}/{len(stock_info)} 只股票")
                    else:
                        fail_count += 1
                        failed_stocks.append((code, name, "无数据"))
                        logger.warning(f"{code} {name}: 无数据")
                        
                except Exception as e:
                    fail_count += 1
                    error_msg = str(e)
                    failed_stocks.append((code, name, error_msg[:50]))
                    logger.error(f"{code} {name} 下载失败: {error_msg}")
                    
                    # 如果是频率限制，休息一下
                    if "频繁" in error_msg or "limit" in error_msg.lower():
                        logger.warning("访问过于频繁，休息3秒...")
                        import time
                        time.sleep(3)
                
                pbar.update(1)
        
        # 显示下载结果
        print("\n" + "="*80)
        print("下载完成！")
        print("="*80)
        print(f"成功: {success_count} 只")
        print(f"失败: {fail_count} 只")
        print(f"数据保存至: {target_dir}")
        
        logger.info(f"下载完成 - 成功: {success_count}, 失败: {fail_count}")
        
        # 显示失败的股票（如果有）
        if failed_stocks:
            print(f"\n失败的股票 (前10只):")
            for code, name, error in failed_stocks[:10]:
                print(f"  {code} {name}: {error}")
            
            if len(failed_stocks) > 10:
                print(f"  ... 还有 {len(failed_stocks) - 10} 只失败")
        
        print("="*80 + "\n")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"下载过程出错: {e}")
        print(f"\n错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def verify_data(target_dir="~/.qlib/qlib_data/cn_data"):
    """
    验证下载的数据
    
    Args:
        target_dir: 数据目录
        
    Returns:
        bool: 验证是否通过
    """
    target_dir = os.path.expanduser(target_dir)
    
    print("\n" + "="*80)
    print("验证数据")
    print("="*80)
    
    if not os.path.exists(target_dir):
        print(f"错误: 数据目录不存在 - {target_dir}")
        return False
    
    # 检查CSV文件
    csv_files = list(Path(target_dir).glob("*.csv"))
    print(f"\n找到 {len(csv_files)} 个数据文件")
    
    if len(csv_files) == 0:
        print("警告: 数据目录为空")
        return False
    
    # 显示部分文件
    print("\n示例文件:")
    for f in csv_files[:5]:
        print(f"  ✓ {f.name}")
    
    if len(csv_files) > 5:
        print(f"  ... 还有 {len(csv_files) - 5} 个文件")
    
    # 验证数据格式
    try:
        import pandas as pd
        
        sample_file = csv_files[0]
        df = pd.read_csv(sample_file)
        
        print(f"\n示例数据 ({sample_file.name}):")
        print(df.head(10))
        print(f"\n数据形状: {df.shape}")
        print(f"日期范围: {df['日期'].min()} 至 {df['日期'].max()}")
        
        # 检查必要的列
        required_cols = ['日期', '开盘', '收盘', '最高', '最低', '成交量']
        missing_cols = [col for col in required_cols if col not in df.columns]
        
        if missing_cols:
            print(f"\n警告: 缺少列: {missing_cols}")
            return False
        
        print("\n✓ 数据验证通过！")
        print("="*80 + "\n")
        return True
        
    except Exception as e:
        print(f"\n✗ 数据验证失败: {e}")
        return False


def main():
    """主函数"""
    setup_logger()
    
    print("\n" + "="*80)
    print("A股数据下载工具")
    print("="*80)
    print("\n选项:")
    print("  --num NUM        下载股票数量 (默认: 300)")
    print("  --start DATE     开始日期 (默认: 20200101)")
    print("  --dir PATH       存储目录 (默认: ~/.qlib/qlib_data/cn_data)")
    print("  --include-st     包含ST股票")
    print("  -y, --yes        自动确认，不询问")
    print("  --verify-only    仅验证已下载的数据")
    print("="*80 + "\n")
    
    # 解析参数
    target_dir = "~/.qlib/qlib_data/cn_data"
    num_stocks = 300
    start_date = "20200101"
    exclude_st = True
    
    i = 1
    while i < len(sys.argv):
        arg = sys.argv[i]
        
        if arg == '--num' and i + 1 < len(sys.argv):
            num_stocks = int(sys.argv[i + 1])
            i += 2
        elif arg == '--start' and i + 1 < len(sys.argv):
            start_date = sys.argv[i + 1]
            i += 2
        elif arg == '--dir' and i + 1 < len(sys.argv):
            target_dir = sys.argv[i + 1]
            i += 2
        elif arg == '--include-st':
            exclude_st = False
            i += 1
        elif arg == '--verify-only':
            # 仅验证数据
            verify_data(target_dir)
            return
        elif arg in ['-y', '--yes']:
            i += 1
        else:
            i += 1
    
    # 显示配置
    print("配置:")
    print(f"  下载数量: {num_stocks} 只")
    print(f"  开始日期: {start_date}")
    print(f"  存储目录: {target_dir}")
    print(f"  排除ST股: {'是' if exclude_st else '否'}")
    print()
    
    # 下载数据
    success = download_stock_data(
        target_dir=target_dir,
        num_stocks=num_stocks,
        start_date=start_date,
        exclude_st=exclude_st
    )
    
    if success:
        # 验证数据
        verify_data(target_dir)
        
        print("\n" + "="*80)
        print("下一步:")
        print("  1. 运行趋势分析: python example_trend_analysis.py")
        print("  2. 批量筛选股票: (即将支持)")
        print("="*80 + "\n")
    else:
        print("\n下载失败，请检查错误信息")


if __name__ == '__main__':
    main()
