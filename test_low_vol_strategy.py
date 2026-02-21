#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
低波轮动策略测试脚本

测试低波债券轮动策略的功能
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.analysis import LowVolatilityRotation
from src.data_source import DataFetcher
from loguru import logger
import pandas as pd
import yaml


def load_config():
    """加载配置文件"""
    config_path = project_root / 'config/config.yaml'
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    return config


def get_sample_candidates(fetcher: DataFetcher):
    """
    获取示例候选标的
    
    这里使用债券ETF作为示例
    """
    logger.info("获取债券ETF候选池...")
    
    # 示例债券ETF列表（真实代码）
    bond_etfs = [
        {'code': '511010.SH', 'name': '国债ETF'},
        {'code': '511260.SH', 'name': '上证10年期国债ETF'},
        {'code': '511220.SH', 'name': '城投债ETF'},
        {'code': '511380.SH', 'name': '地方债ETF'},
        {'code': '159650.SZ', 'name': '10年地方债ETF'},
        {'code': '159926.SZ', 'name': '嘉实中证500ETF'},  # 用于对比
    ]
    
    # 计算日期范围
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 最近6个月数据
    
    candidates = []
    
    for etf in bond_etfs:
        try:
            code = etf['code']
            name = etf['name']
            
            logger.info(f"获取 {name}({code}) 数据...")
            
            # 获取历史数据
            price_data = fetcher.fetch_stock_data(
                code,
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d')
            )
            
            if price_data.empty:
                logger.warning(f"{name} 无数据，跳过")
                continue
            
            candidates.append({
                'code': code,
                'name': name,
                'price_data': price_data
            })
            
            logger.info(f"成功获取 {name} 数据: {len(price_data)} 条记录")
            
        except Exception as e:
            logger.error(f"获取 {code} 数据失败: {e}")
            continue
    
    return candidates


def test_low_volatility_rotation():
    """测试低波轮动策略"""
    logger.info("=" * 60)
    logger.info("测试低波债券轮动策略")
    logger.info("=" * 60)
    
    # 加载配置
    config = load_config()
    
    # 初始化数据获取器（使用YFinance，支持债券ETF）
    data_config = config['data_source'].copy()
    data_config['provider'] = 'yfinance'  # 使用YFinance获取数据
    
    fetcher = DataFetcher(data_config)
    
    # 初始化策略
    strategy_config = config['analysis']['strategies']['low_volatility_rotation']
    strategy = LowVolatilityRotation(strategy_config)
    
    # 获取候选标的
    candidates = get_sample_candidates(fetcher)
    
    if not candidates:
        logger.error("未获取到候选标的，测试终止")
        return
    
    logger.info(f"\n共获取 {len(candidates)} 个候选标的")
    
    # 分析候选标的
    logger.info("\n" + "=" * 60)
    logger.info("开始分析...")
    logger.info("=" * 60)
    
    analyzed_data = strategy.analyze(candidates)
    
    if analyzed_data.empty:
        logger.warning("分析结果为空")
        return
    
    # 显示分析结果
    logger.info("\n分析结果:")
    print("\n" + analyzed_data.to_string())
    
    # 生成推荐
    logger.info("\n" + "=" * 60)
    logger.info("生成推荐...")
    logger.info("=" * 60)
    
    recommendations = strategy.generate_recommendations(analyzed_data)
    
    if not recommendations:
        logger.warning("无推荐结果")
        return
    
    # 显示推荐结果
    logger.info(f"\n共生成 {len(recommendations)} 个推荐:\n")
    
    for rec in recommendations:
        print(f"排名 {rec['rank']}: {rec['name']}({rec['code']})")
        print(f"  当前价格: {rec['current_price']:.3f}")
        print(f"  综合得分: {rec['score']:.2f}")
        print(f"  建议持仓: {rec['suggested_position']}")
        print(f"  推荐理由:")
        for reason in rec['reasons']:
            print(f"    - {reason}")
        print()
    
    # 组合统计
    logger.info("=" * 60)
    logger.info("组合统计")
    logger.info("=" * 60)
    
    stats = strategy.get_portfolio_stats(recommendations)
    
    if stats:
        print(f"\n组合数量: {stats['portfolio_count']}")
        print(f"平均波动率: {stats['avg_volatility']:.2f}%")
        print(f"平均动量: {stats['avg_momentum']:.2f}%")
        if not pd.isna(stats['avg_sharpe_ratio']):
            print(f"平均夏普比率: {stats['avg_sharpe_ratio']:.2f}")
        print(f"平均最大回撤: {stats['avg_max_drawdown']:.2f}%")
        print(f"预期年化收益: {stats['expected_annual_return']}")
    
    logger.info("\n" + "=" * 60)
    logger.info("测试完成！")
    logger.info("=" * 60)


def test_with_mock_data():
    """使用模拟数据测试（不需要网络）"""
    logger.info("=" * 60)
    logger.info("使用模拟数据测试策略")
    logger.info("=" * 60)
    
    # 加载配置
    config = load_config()
    strategy_config = config['analysis']['strategies']['low_volatility_rotation']
    strategy = LowVolatilityRotation(strategy_config)
    
    # 生成模拟数据
    dates = pd.date_range(end=datetime.now(), periods=100, freq='D')
    
    candidates = []
    
    # 创建几个不同特征的模拟标的
    for i in range(5):
        # 模拟价格数据（低波动）
        base_price = 100 + i * 5
        volatility = 0.002 + i * 0.001  # 不同的波动率
        
        prices = [base_price]
        for _ in range(99):
            change = np.random.normal(0.0005, volatility)  # 正收益，不同波动
            prices.append(prices[-1] * (1 + change))
        
        price_data = pd.DataFrame({
            'date': dates,
            'close': prices,
            'volume': np.random.randint(10000, 100000, 100),
            'amount': np.random.randint(1000000, 50000000, 100),
        })
        
        candidates.append({
            'code': f'TEST{i:03d}',
            'name': f'测试债券{i+1}号',
            'price_data': price_data
        })
    
    # 分析
    analyzed_data = strategy.analyze(candidates)
    
    if not analyzed_data.empty:
        print("\n分析结果:")
        print(analyzed_data[['code', 'name', 'volatility', 'momentum', 'score']].to_string())
        
        # 生成推荐
        recommendations = strategy.generate_recommendations(analyzed_data)
        
        if recommendations:
            print(f"\n推荐结果 (Top {len(recommendations)}):")
            for rec in recommendations:
                print(f"{rec['rank']}. {rec['name']}: 得分={rec['score']:.2f}, "
                      f"波动率={rec['volatility']:.2f}%, 动量={rec['momentum']:.2f}%")
    
    logger.info("模拟数据测试完成")


def main():
    """主函数"""
    logger.info("开始测试低波轮动策略模块...")
    
    try:
        # 选择测试方式
        # test_low_volatility_rotation()  # 使用真实数据（需要网络）
        test_with_mock_data()  # 使用模拟数据（快速测试）
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    import numpy as np  # 用于模拟数据
    exit(main())
