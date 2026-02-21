#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据源模块测试脚本

测试 AkShare、YFinance 和 Twelve Data 数据源功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.data_source import DataFetcher
from loguru import logger


def test_akshare():
    """测试 AkShare 数据源"""
    logger.info("=" * 60)
    logger.info("测试 AkShare 数据源")
    logger.info("=" * 60)
    
    config = {
        'provider': 'akshare',
        'cache': {'enabled': True}
    }
    
    fetcher = DataFetcher(config)
    
    # 测试获取股票列表
    logger.info("\n1. 获取A股股票列表（前10条）...")
    stock_list = fetcher.fetch_stock_list('A')
    if not stock_list.empty:
        print(stock_list.head(10))
        print(f"总共 {len(stock_list)} 只股票\n")
    
    # 测试获取股票历史数据
    logger.info("\n2. 获取平安银行(000001)最近30天数据...")
    stock_data = fetcher.fetch_stock_data('000001', '2024-01-01', '2024-01-30')
    if not stock_data.empty:
        print(stock_data.head())
        print(f"总共 {len(stock_data)} 条数据\n")
    
    # 测试获取实时行情
    logger.info("\n3. 获取平安银行和招商银行实时行情...")
    realtime = fetcher.fetch_realtime_data(['000001', '600036'])
    if not realtime.empty:
        print(realtime[['code', 'name', 'price', 'change_pct']])
        print()
    
    # 测试获取基本信息
    logger.info("\n4. 获取平安银行基本信息...")
    info = fetcher.fetch_fundamental_data('000001')
    if info:
        for key, value in list(info.items())[:5]:
            print(f"{key}: {value}")
        print()


def test_yfinance():
    """测试 YFinance 数据源"""
    logger.info("=" * 60)
    logger.info("测试 YFinance 数据源")
    logger.info("=" * 60)
    
    config = {
        'provider': 'yfinance',
        'cache': {'enabled': True}
    }
    
    fetcher = DataFetcher(config)
    
    # 测试获取美股数据
    logger.info("\n1. 获取苹果(AAPL)最近30天数据...")
    stock_data = fetcher.fetch_stock_data('AAPL', '2024-01-01', '2024-01-30')
    if not stock_data.empty:
        print(stock_data.head())
        print(f"总共 {len(stock_data)} 条数据\n")
    
    # 测试获取实时行情
    logger.info("\n2. 获取苹果和微软实时行情...")
    realtime = fetcher.fetch_realtime_data(['AAPL', 'MSFT'])
    if not realtime.empty:
        print(realtime[['code', 'name', 'price', 'change_pct']])
        print()
    
    # 测试获取基本信息
    logger.info("\n3. 获取苹果基本信息...")
    info = fetcher.fetch_fundamental_data('AAPL')
    if info:
        for key, value in list(info.items())[:10]:
            print(f"{key}: {value}")
        print()
    
    # 测试获取A股数据（使用YFinance格式）
    logger.info("\n4. 获取平安银行(000001.SZ)数据...")
    stock_data = fetcher.fetch_stock_data('000001.SZ', '2024-01-01', '2024-01-30')
    if not stock_data.empty:
        print(stock_data.head())
        print(f"总共 {len(stock_data)} 条数据\n")


def test_twelvedata():
    """测试 Twelve Data 数据源"""
    logger.info("=" * 60)
    logger.info("测试 Twelve Data 数据源")
    logger.info("=" * 60)
    
    # 注意：需要设置有效的 API key
    config = {
        'provider': 'twelvedata',
        'api_key': 'your_twelvedata_api_key',  # 请替换为真实的 API key
        'cache': {'enabled': True}
    }
    
    fetcher = DataFetcher(config)
    
    # 测试获取美股数据
    logger.info("\n1. 获取苹果(AAPL)最近30天数据...")
    stock_data = fetcher.fetch_stock_data('AAPL', '2024-01-01', '2024-01-30')
    if not stock_data.empty:
        print(stock_data.head())
        print(f"总共 {len(stock_data)} 条数据\n")
    
    # 测试获取实时行情
    logger.info("\n2. 获取苹果和微软实时行情...")
    realtime = fetcher.fetch_realtime_data(['AAPL', 'MSFT'])
    if not realtime.empty:
        print(realtime[['code', 'name', 'price', 'change_pct']])
        print()
    
    # 测试获取基本信息
    logger.info("\n3. 获取苹果基本信息...")
    info = fetcher.fetch_fundamental_data('AAPL')
    if info:
        for key, value in info.items():
            print(f"{key}: {value}")
        print()
    
    # 测试获取外汇数据
    logger.info("\n4. 获取欧元/美元外汇数据...")
    forex_data = fetcher.fetch_stock_data('EUR/USD', '2024-01-01', '2024-01-30')
    if not forex_data.empty:
        print(forex_data.head())
        print(f"总共 {len(forex_data)} 条数据\n")
    
    # 测试获取加密货币数据
    logger.info("\n5. 获取比特币/美元数据...")
    crypto_data = fetcher.fetch_stock_data('BTC/USD', '2024-01-01', '2024-01-30')
    if not crypto_data.empty:
        print(crypto_data.head())
        print(f"总共 {len(crypto_data)} 条数据\n")


def test_switch_provider():
    """测试切换数据源"""
    logger.info("=" * 60)
    logger.info("测试切换数据源")
    logger.info("=" * 60)
    
    config = {
        'provider': 'akshare',
        'cache': {'enabled': True}
    }
    
    fetcher = DataFetcher(config)
    
    logger.info(f"\n当前数据源: {fetcher.get_provider_name()}")
    
    # 使用AkShare获取数据
    logger.info("\n使用 AkShare 获取平安银行数据...")
    data1 = fetcher.fetch_stock_data('000001', '2024-01-01', '2024-01-10')
    if not data1.empty:
        print(f"获取到 {len(data1)} 条数据")
    
    # 切换到YFinance
    fetcher.switch_provider('yfinance')
    logger.info(f"\n切换后的数据源: {fetcher.get_provider_name()}")
    
    # 使用YFinance获取数据
    logger.info("\n使用 YFinance 获取苹果数据...")
    data2 = fetcher.fetch_stock_data('AAPL', '2024-01-01', '2024-01-10')
    if not data2.empty:
        print(f"获取到 {len(data2)} 条数据")


def main():
    """主函数"""
    logger.info("开始测试数据源模块...")
    
    try:
        # 测试 AkShare
        test_akshare()
        
        # 测试 YFinance
        # test_yfinance()
        
        # 测试 Twelve Data（需要设置有效的 API key）
        # test_twelvedata()
        
        # 测试切换数据源
        # test_switch_provider()
        
        logger.info("=" * 60)
        logger.info("所有测试完成！")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"测试失败: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
