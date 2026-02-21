"""
数据提供者基类

定义统一的数据获取接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import pandas as pd
from loguru import logger


class BaseProvider(ABC):
    """
    数据提供者抽象基类
    
    所有数据源提供者都需要继承此类并实现抽象方法
    """
    
    def __init__(self, config: Dict):
        """
        初始化数据提供者
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.api_key = config.get('api_key', '')
        self.provider_name = self.__class__.__name__
        
        logger.info(f"初始化数据提供者: {self.provider_name}")
    
    @abstractmethod
    def fetch_stock_list(self, market: str = 'A') -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            market: 市场类型，如 'A'(A股), 'HK'(港股), 'US'(美股)
            
        Returns:
            DataFrame: 包含股票代码、名称等信息
            列: ['code', 'name', 'market', 'industry', 'list_date']
        """
        pass
    
    @abstractmethod
    def fetch_stock_daily(self, 
                         symbol: str, 
                         start_date: str, 
                         end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            DataFrame: 日线数据
            列: ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
        """
        pass
    
    @abstractmethod
    def fetch_stock_realtime(self, symbols: List[str]) -> pd.DataFrame:
        """
        获取股票实时行情
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            DataFrame: 实时行情数据
            列: ['code', 'name', 'price', 'change', 'change_pct', 
                 'volume', 'amount', 'time']
        """
        pass
    
    @abstractmethod
    def fetch_stock_basic_info(self, symbol: str) -> Dict:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 基本信息字典
            {
                'code': str,
                'name': str,
                'industry': str,
                'market_cap': float,
                'pe_ratio': float,
                'pb_ratio': float,
                ...
            }
        """
        pass
    
    def fetch_index_daily(self, 
                         index_code: str, 
                         start_date: str, 
                         end_date: str) -> pd.DataFrame:
        """
        获取指数日线数据（可选实现）
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 指数日线数据
        """
        logger.warning(f"{self.provider_name} 未实现 fetch_index_daily 方法")
        return pd.DataFrame()
    
    def fetch_fund_list(self) -> pd.DataFrame:
        """
        获取基金列表（可选实现）
        
        Returns:
            DataFrame: 基金列表
        """
        logger.warning(f"{self.provider_name} 未实现 fetch_fund_list 方法")
        return pd.DataFrame()
    
    def fetch_fund_nav(self, 
                      fund_code: str, 
                      start_date: str, 
                      end_date: str) -> pd.DataFrame:
        """
        获取基金净值数据（可选实现）
        
        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 基金净值数据
        """
        logger.warning(f"{self.provider_name} 未实现 fetch_fund_nav 方法")
        return pd.DataFrame()
    
    def _normalize_symbol(self, symbol: str) -> str:
        """
        标准化股票代码
        
        Args:
            symbol: 原始股票代码
            
        Returns:
            str: 标准化后的代码
        """
        # 移除空格
        symbol = symbol.strip().upper()
        return symbol
    
    def _validate_date(self, date_str: str) -> bool:
        """
        验证日期格式
        
        Args:
            date_str: 日期字符串
            
        Returns:
            bool: 是否有效
        """
        try:
            pd.to_datetime(date_str)
            return True
        except:
            return False
