"""
使用本地下载数据进行趋势分析测试

使用 download_stock_data.py 下载的本地CSV文件进行趋势分析
"""

import sys
import os
from pathlib import Path
import pandas as pd
from loguru import logger
from datetime import datetime

# 添加项目根目录到path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.analysis.trend_strategy import TrendFollowingStrategy
from src.analysis.analyzer import TechnicalAnalyzer


def load_local_data(stock_code: str, data_dir: Path) -> pd.DataFrame:
    """
    从本地CSV文件加载股票数据
    
    Args:
        stock_code: 股票代码（如 '600519'）
        data_dir: 数据目录路径
    
    Returns:
        DataFrame: 标准化后的股票数据
    """
    csv_file = data_dir / f"{stock_code}.csv"
    
    if not csv_file.exists():
        logger.error(f"数据文件不存在: {csv_file}")
        return pd.DataFrame()
    
    # 读取CSV数据
    df = pd.read_csv(csv_file)
    
    # 标准化列名（将中文列名映射为英文）
    column_mapping = {
        '日期': 'date',
        '股票代码': 'symbol',
        '开盘': 'open',
        '收盘': 'close',
        '最高': 'high',
        '最低': 'low',
        '成交量': 'volume',
        '成交额': 'amount',
        '振幅': 'amplitude',
        '涨跌幅': 'pct_change',
        '涨跌额': 'change',
        '换手率': 'turnover'
    }
    
    df = df.rename(columns=column_mapping)
    
    # 确保日期列是datetime类型
    df['date'] = pd.to_datetime(df['date'])
    
    # 按日期排序（升序）
    df = df.sort_values('date')
    
    # 设置日期为索引
    df.set_index('date', inplace=True)
    
    logger.info(f"加载 {stock_code} 数据: {len(df)} 条记录，日期范围 {df.index[0]} 至 {df.index[-1]}")
    
    return df


def test_single_stock_analysis():
    """
    测试单个股票的趋势分析
    """
    logger.info("="*80)
    logger.info("测试1：单个股票趋势分析")
    logger.info("="*80)
    
    # 配置数据目录
    data_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data"
    
    if not data_dir.exists():
        logger.error(f"数据目录不存在: {data_dir}")
        logger.info("请先运行: python download_stock_data.py --num 100 -y")
        return
    
    # 获取所有可用的股票代码
    csv_files = list(data_dir.glob("*.csv"))
    if not csv_files:
        logger.error(f"数据目录为空: {data_dir}")
        return
    
    # 选择第一个股票进行测试
    test_stock = csv_files[0].stem  # 文件名（不含扩展名）
    logger.info(f"选择测试股票: {test_stock}")
    
    # 加载数据
    df = load_local_data(test_stock, data_dir)
    
    if df.empty:
        logger.error("数据加载失败")
        return
    
    # 显示数据基本信息
    logger.info(f"\n数据概览:\n{df[['open', 'close', 'high', 'low', 'volume']].head()}")
    logger.info(f"\n数据统计:\n{df[['open', 'close', 'high', 'low', 'volume']].describe()}")
    
    # 创建技术分析器（需要config参数）
    # 由于数据列名是英文，需要先转换为中文（因为indicators.py使用中文列名）
    # 或者更简单的方法：创建一个中文列名的副本
    df_cn = df.copy()
    df_cn = df_cn.rename(columns={
        'open': '开盘',
        'close': '收盘', 
        'high': '最高',
        'low': '最低',
        'volume': '成交量',
        'amount': '成交额'
    })
    
    analyzer_config = {
        'indicators': ['ma', 'ema', 'volume'],
        'filters': {}
    }
    analyzer = TechnicalAnalyzer(analyzer_config)
    
    # 进行综合分析
    logger.info("\n开始趋势分析...")
    result = analyzer.comprehensive_analysis(df_cn)
    
    # 显示分析结果
    logger.info("\n" + "="*80)
    logger.info(f"趋势分析结果 - {test_stock}")
    logger.info("="*80)
    
    # 趋势信息
    if 'trend' in result:
        trend = result['trend']
        logger.info(f"\n【趋势类型】: {trend.get('trend_type', 'N/A')}")
        logger.info(f"【趋势阶段】: {trend.get('trend_phase', 'N/A')}")
        logger.info(f"【年化收益】: {trend.get('annual_return', 0):.2f}%")
        
        if 'ma_turning' in trend:
            ma_turning = trend['ma_turning']
            logger.info(f"\n【均线转折预测】:")
            for ma_type, info in ma_turning.items():
                logger.info(f"  {ma_type}: 下一周期预测 {info.get('next_direction', 'N/A')}")
    
    # 信号检测
    if 'signals' in result:
        signals = result['signals']
        
        # 突破信号
        if 'breakout' in signals and signals['breakout']:
            logger.info(f"\n【突破信号】:")
            breakout_list = signals['breakout'] if isinstance(signals['breakout'], list) else [signals['breakout']]
            for sig in breakout_list:
                if isinstance(sig, dict):
                    logger.info(f"  日期: {sig.get('date', 'N/A')}")
                    logger.info(f"  价格: {sig.get('price', 0):.2f}")
                    logger.info(f"  得分: {sig.get('strength', 0):.1f}")
                else:
                    logger.info(f"  {sig}")
        
        # 回调信号
        if 'pullback' in signals and signals['pullback']:
            logger.info(f"\n【回调信号】:")
            pullback_list = signals['pullback'] if isinstance(signals['pullback'], list) else [signals['pullback']]
            for sig in pullback_list:
                if isinstance(sig, dict):
                    logger.info(f"  日期: {sig.get('date', 'N/A')}")
                    logger.info(f"  价格: {sig.get('price', 0):.2f}")
                    logger.info(f"  得分: {sig.get('strength', 0):.1f}")
                else:
                    logger.info(f"  {sig}")
        
        # 2B结构信号
        if '2b_structure' in signals and signals['2b_structure']:
            logger.info(f"\n【2B结构信号】:")
            structure_list = signals['2b_structure'] if isinstance(signals['2b_structure'], list) else [signals['2b_structure']]
            for sig in structure_list:
                if isinstance(sig, dict):
                    logger.info(f"  类型: {sig.get('type', 'N/A')}")
                    logger.info(f"  日期: {sig.get('date', 'N/A')}")
                    logger.info(f"  价格: {sig.get('price', 0):.2f}")
                else:
                    logger.info(f"  {sig}")
        
        # 顶底结构信号
        if 'top_bottom' in signals and signals['top_bottom']:
            logger.info(f"\n【顶底结构信号】:")
            tb_list = signals['top_bottom'] if isinstance(signals['top_bottom'], list) else [signals['top_bottom']]
            for sig in tb_list:
                if isinstance(sig, dict):
                    logger.info(f"  类型: {sig.get('type', 'N/A')}")
                    logger.info(f"  日期: {sig.get('date', 'N/A')}")
                    logger.info(f"  价格: {sig.get('price', 0):.2f}")
                else:
                    logger.info(f"  {sig}")
    
    logger.info("\n" + "="*80)
    

def test_batch_stock_screening():
    """
    测试批量股票筛选推荐
    """
    logger.info("="*80)
    logger.info("测试2：批量股票筛选")
    logger.info("="*80)
    
    # 配置数据目录
    data_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data"
    
    if not data_dir.exists():
        logger.error(f"数据目录不存在: {data_dir}")
        return
    
    # 获取所有股票代码
    csv_files = list(data_dir.glob("*.csv"))
    
    if not csv_files:
        logger.error(f"数据目录为空: {data_dir}")
        return
    
    logger.info(f"找到 {len(csv_files)} 个股票数据文件")
    
    # 限制分析数量（避免太慢）
    max_stocks = min(20, len(csv_files))
    logger.info(f"将分析前 {max_stocks} 只股票\n")
    
    # 准备数据（转换为中文列名）
    stock_data = {}
    for csv_file in csv_files[:max_stocks]:
        stock_code = csv_file.stem
        df = load_local_data(stock_code, data_dir)
        if not df.empty:
            # 转换为中文列名
            df_cn = df.rename(columns={
                'open': '开盘',
                'close': '收盘', 
                'high': '最高',
                'low': '最低',
                'volume': '成交量',
                'amount': '成交额'
            })
            stock_data[stock_code] = df_cn
    
    logger.info(f"成功加载 {len(stock_data)} 只股票的数据")
    
    # 创建趋势策略（需要config）
    strategy_config = {
        'ma_periods': [20, 60, 120],
        'min_data_points': 60
    }
    strategy = TrendFollowingStrategy(strategy_config)
    
    # 批量分析
    logger.info("\n开始批量分析...")
    recommendations = strategy.batch_analyze(stock_data)
    
    # 只取前10个
    recommendations = recommendations[:10]
    
    # 显示推荐结果
    logger.info("\n" + "="*80)
    logger.info("趋势跟随推荐结果（前10只）")
    logger.info("="*80)
    
    for i, rec in enumerate(recommendations, 1):
        logger.info(f"\n【推荐 {i}】")
        logger.info(f"股票代码: {rec.get('symbol', 'N/A')}")
        logger.info(f"推荐类型: {rec.get('action', 'N/A')}")
        logger.info(f"综合得分: {rec.get('score', 0):.1f}")
        logger.info(f"趋势类型: {rec.get('trend_type', 'N/A')}")
        logger.info(f"年化收益: {rec.get('annual_return', 0):.2f}%")
        
        if 'entry_price' in rec:
            logger.info(f"建议入场: {rec['entry_price']:.2f}")
        if 'stop_loss' in rec:
            logger.info(f"止损价位: {rec['stop_loss']:.2f}")
        if 'target_price' in rec:
            logger.info(f"目标价位: {rec['target_price']:.2f}")
        
        logger.info(f"推荐理由: {rec.get('reason', 'N/A')}")
    
    logger.info("\n" + "="*80)


def test_data_quality():
    """
    测试数据质量
    """
    logger.info("="*80)
    logger.info("测试3：数据质量检查")
    logger.info("="*80)
    
    data_dir = Path.home() / ".qlib" / "qlib_data" / "cn_data"
    
    if not data_dir.exists():
        logger.error(f"数据目录不存在: {data_dir}")
        return
    
    csv_files = list(data_dir.glob("*.csv"))
    
    logger.info(f"总文件数: {len(csv_files)}")
    
    stats = {
        'total': len(csv_files),
        'valid': 0,
        'empty': 0,
        'error': 0,
        'min_rows': float('inf'),
        'max_rows': 0,
        'total_rows': 0
    }
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file)
            
            if df.empty:
                stats['empty'] += 1
            else:
                stats['valid'] += 1
                rows = len(df)
                stats['total_rows'] += rows
                stats['min_rows'] = min(stats['min_rows'], rows)
                stats['max_rows'] = max(stats['max_rows'], rows)
        except Exception as e:
            stats['error'] += 1
            logger.error(f"读取文件失败 {csv_file}: {e}")
    
    logger.info(f"\n数据质量统计:")
    logger.info(f"  有效文件: {stats['valid']}")
    logger.info(f"  空文件: {stats['empty']}")
    logger.info(f"  错误文件: {stats['error']}")
    
    if stats['valid'] > 0:
        logger.info(f"  平均行数: {stats['total_rows'] // stats['valid']}")
        logger.info(f"  最少行数: {stats['min_rows']}")
        logger.info(f"  最多行数: {stats['max_rows']}")
    
    logger.info("\n" + "="*80)


def main():
    """主函数"""
    # 配置日志
    logger.remove()  # 移除默认handler
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    logger.info("="*80)
    logger.info("本地数据趋势分析测试")
    logger.info(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    try:
        # 测试1：数据质量检查
        test_data_quality()
        
        # 测试2：单个股票分析
        test_single_stock_analysis()
        
        # 测试3：批量股票筛选
        test_batch_stock_screening()
        
        logger.info("\n" + "="*80)
        logger.info("所有测试完成！")
        logger.info("="*80)
        
    except Exception as e:
        logger.exception(f"测试过程中发生错误: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
