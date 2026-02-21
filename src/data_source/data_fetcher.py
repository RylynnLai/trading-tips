"""
数据获取器

负责从不同的数据源获取证券数据
"""

from typing import Dict, List, Optional
import pandas as pd
from loguru import logger

from .akshare_provider import AkShareProvider
from .yfinance_provider import YFinanceProvider
from .twelvedata_provider import TwelveDataProvider


class DataFetcher:
    """
    数据获取器类
    
    支持从多个数据源获取证券数据，包括股票、基金、ETF等
    支持的数据源：akshare, yfinance, tushare（待实现）
    """
    
    def __init__(self, config: Dict):
        """
        初始化数据获取器
        
        Args:
            config: 配置字典，包含数据源类型、API密钥等信息
        """
        self.config = config
        self.provider_name = config.get('provider', 'akshare').lower()
        self.api_key = config.get('api_key')
        self.cache_enabled = config.get('cache', {}).get('enabled', True)
        self.cache = {}  # 简单的内存缓存
        
        # 初始化数据提供者
        self.provider = self._init_provider()
        
        logger.info(f"初始化数据获取器，数据源: {self.provider_name}")
    
    def _init_provider(self):
        """
        初始化数据提供者
        
        Returns:
            数据提供者对象
        """
        if self.provider_name == 'akshare':
            return AkShareProvider(self.config)
        elif self.provider_name == 'yfinance':
            return YFinanceProvider(self.config)
        elif self.provider_name == 'twelvedata':
            return TwelveDataProvider(self.config)
        elif self.provider_name == 'tushare':
            logger.warning("Tushare 数据源尚未实现，使用 AkShare 作为替代")
            return AkShareProvider(self.config)
        else:
            logger.warning(f"未知的数据源 {self.provider_name}，使用 AkShare 作为默认")
            return AkShareProvider(self.config)
        
    def fetch_stock_list(self, market: str = 'A') -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            market: 市场类型 'A'(A股), 'HK'(港股), 'US'(美股)
        
        Returns:
            DataFrame: 包含股票代码、名称等信息的数据框
        """
        logger.info(f"获取{market}股票列表")
        
        cache_key = f"stock_list_{market}"
        if self.cache_enabled and cache_key in self.cache:
            logger.info("从缓存获取股票列表")
            return self.cache[cache_key]
        
        df = self.provider.fetch_stock_list(market)
        
        if not df.empty and self.cache_enabled:
            self.cache[cache_key] = df
        
        return df
    
    def fetch_stock_data(self, 
                        symbol: str, 
                        start_date: str, 
                        end_date: str) -> pd.DataFrame:
        """
        获取指定股票的历史数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            DataFrame: 包含开高低收量等数据的数据框
        """
        logger.info(f"获取股票数据: {symbol}, {start_date} 至 {end_date}")
        
        cache_key = f"stock_data_{symbol}_{start_date}_{end_date}"
        if self.cache_enabled and cache_key in self.cache:
            logger.info("从缓存获取股票数据")
            return self.cache[cache_key]
        
        df = self.provider.fetch_stock_daily(symbol, start_date, end_date)
        
        if not df.empty and self.cache_enabled:
            self.cache[cache_key] = df
        
        return df
    
    def fetch_realtime_data(self, symbols: List[str]) -> pd.DataFrame:
        """
        获取实时行情数据
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            DataFrame: 实时行情数据
        """
        logger.info(f"获取实时数据: {symbols}")
        return self.provider.fetch_stock_realtime(symbols)
    
    def fetch_fundamental_data(self, symbol: str) -> Dict:
        """
        获取基本面数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 基本面数据字典，包括市盈率、市净率、ROE等
        """
        logger.info(f"获取基本面数据: {symbol}")
        
        cache_key = f"fundamental_{symbol}"
        if self.cache_enabled and cache_key in self.cache:
            logger.info("从缓存获取基本面数据")
            return self.cache[cache_key]
        
        data = self.provider.fetch_stock_basic_info(symbol)
        
        if data and self.cache_enabled:
            self.cache[cache_key] = data
        
        return data
    
    def fetch_fund_list(self) -> pd.DataFrame:
        """
        获取基金列表
        
        Returns:
            DataFrame: 基金列表数据
        """
        logger.info("获取基金列表")
        
        cache_key = "fund_list"
        if self.cache_enabled and cache_key in self.cache:
            logger.info("从缓存获取基金列表")
            return self.cache[cache_key]
        
        df = self.provider.fetch_fund_list()
        
        if not df.empty and self.cache_enabled:
            self.cache[cache_key] = df
        
        return df
    
    def fetch_fund_data(self, 
                       symbol: str, 
                       start_date: str, 
                       end_date: str) -> pd.DataFrame:
        """
        获取基金净值数据
        
        Args:
            symbol: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 基金净值数据
        """
        logger.info(f"获取基金数据: {symbol}, {start_date} 至 {end_date}")
        
        cache_key = f"fund_data_{symbol}_{start_date}_{end_date}"
        if self.cache_enabled and cache_key in self.cache:
            logger.info("从缓存获取基金数据")
            return self.cache[cache_key]
        
        df = self.provider.fetch_fund_nav(symbol, start_date, end_date)
        
        if not df.empty and self.cache_enabled:
            self.cache[cache_key] = df
        
        return df
    
    def fetch_index_data(self,
                        index_code: str,
                        start_date: str,
                        end_date: str) -> pd.DataFrame:
        """
        获取指数数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 指数数据
        """
        logger.info(f"获取指数数据: {index_code}, {start_date} 至 {end_date}")
        return self.provider.fetch_index_daily(index_code, start_date, end_date)
    
    def clear_cache(self):
        """
        清空缓存
        """
        self.cache.clear()
        logger.info("缓存已清空")
    
    def get_provider_name(self) -> str:
        """
        获取当前数据源名称
        
        Returns:
            str: 数据源名称
        """
        return self.provider_name
    
    def switch_provider(self, provider_name: str):
        """
        切换数据源
        
        Args:
            provider_name: 新数据源名称
        """
        logger.info(f"切换数据源: {self.provider_name} -> {provider_name}")
        self.provider_name = provider_name
        self.config['provider'] = provider_name
        self.provider = self._init_provider()
        self.clear_cache()
