"""
Twelve Data API 数据提供者

使用 Twelve Data API 获取全球金融市场数据
Twelve Data: https://twelvedata.com/
"""

from typing import List, Dict
import pandas as pd
import requests
import time
from loguru import logger
from datetime import datetime, timedelta

from .base_provider import BaseProvider


class TwelveDataProvider(BaseProvider):
    """
    Twelve Data API 数据提供者
    
    支持股票、外汇、加密货币、ETF等全球金融数据
    需要 API key（免费版有限制）
    """
    
    def __init__(self, config: Dict):
        """
        初始化 Twelve Data 数据提供者
        
        Args:
            config: 配置字典，需要包含 api_key
        """
        super().__init__(config)
        
        if not self.api_key:
            raise ValueError("Twelve Data API 需要 API key，请在配置中设置")
        
        self.base_url = "https://api.twelvedata.com"
        self.max_retries = 3
        self.retry_delay = 2
        
        logger.info("Twelve Data API 数据提供者初始化完成")
    
    def fetch_stock_list(self, market: str = 'US') -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            market: 市场类型（Twelve Data 支持通过 stocks API 查询）
            
        Returns:
            DataFrame: 股票列表
            
        Note:
            Twelve Data 的免费版可能不支持此功能，建议使用其他数据源
        """
        try:
            logger.info(f"获取{market}市场股票列表...")
            
            url = f"{self.base_url}/stocks"
            params = {
                'exchange': market,
                'apikey': self.api_key
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'data' in data:
                df = pd.DataFrame(data['data'])
                df = df.rename(columns={
                    'symbol': 'code',
                    'name': 'name',
                    'exchange': 'market'
                })
                logger.info(f"获取到 {len(df)} 只股票")
                return df
            else:
                logger.warning(f"未获取到股票列表: {data}")
                return pd.DataFrame(columns=['code', 'name', 'market'])
                
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame(columns=['code', 'name', 'market'])
    
    def fetch_stock_daily(self, 
                         symbol: str, 
                         start_date: str, 
                         end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            symbol: 股票代码（如 'AAPL', 'EUR/USD', 'BTC/USD'）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            DataFrame: 日线数据
        """
        try:
            symbol = self._normalize_symbol(symbol)
            
            logger.info(f"获取 {symbol} 日线数据: {start_date} - {end_date}")
            
            # 计算数据量
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            days = (end - start).days + 1
            
            # 使用带重试的方法获取数据
            df = self._fetch_time_series(
                symbol=symbol,
                interval='1day',
                start_date=start_date,
                end_date=end_date,
                outputsize=min(days * 2, 5000)  # 预留一些余量
            )
            
            if df.empty:
                logger.warning(f"未获取到股票 {symbol} 的数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = df.rename(columns={
                'datetime': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume'
            })
            
            # 确保日期格式
            df['date'] = pd.to_datetime(df['date'])
            
            # 计算成交额（如果有成交量）
            if 'volume' in df.columns and 'close' in df.columns:
                df['amount'] = df['close'] * df['volume']
            else:
                df['amount'] = 0
            
            # 按日期筛选
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            # 选择需要的列
            columns = ['date', 'open', 'high', 'low', 'close', 'volume', 'amount']
            df = df[[col for col in columns if col in df.columns]]
            
            logger.info(f"获取到 {len(df)} 条日线数据")
            return df
            
        except Exception as e:
            logger.error(f"获取股票日线数据失败 ({symbol}): {e}")
            return pd.DataFrame()
    
    def fetch_stock_realtime(self, symbols: List[str]) -> pd.DataFrame:
        """
        获取股票实时行情
        
        Args:
            symbols: 股票代码列表
            
        Returns:
            DataFrame: 实时行情数据
        """
        try:
            logger.info(f"获取 {len(symbols)} 只股票的实时行情...")
            
            all_data = []
            
            for symbol in symbols:
                try:
                    formatted_symbol = self._normalize_symbol(symbol)
                    
                    # 获取实时报价
                    quote_data = self._fetch_quote(formatted_symbol)
                    
                    if not quote_data:
                        continue
                    
                    data = {
                        'code': symbol,
                        'name': quote_data.get('name', symbol),
                        'price': float(quote_data.get('close', 0)),
                        'open': float(quote_data.get('open', 0)),
                        'high': float(quote_data.get('high', 0)),
                        'low': float(quote_data.get('low', 0)),
                        'pre_close': float(quote_data.get('previous_close', 0)),
                        'volume': int(quote_data.get('volume', 0)),
                        'timestamp': quote_data.get('timestamp', ''),
                    }
                    
                    # 计算涨跌额和涨跌幅
                    if data['pre_close'] > 0:
                        data['change'] = data['price'] - data['pre_close']
                        data['change_pct'] = (data['change'] / data['pre_close']) * 100
                    else:
                        data['change'] = 0
                        data['change_pct'] = 0
                    
                    # 计算成交额
                    data['amount'] = data['price'] * data['volume']
                    
                    all_data.append(data)
                    
                    # 避免超过API限制，添加延迟
                    time.sleep(0.1)
                    
                except Exception as e:
                    logger.warning(f"获取 {symbol} 实时数据失败: {e}")
                    continue
            
            if not all_data:
                return pd.DataFrame()
            
            df = pd.DataFrame(all_data)
            logger.info(f"成功获取 {len(df)} 只股票的实时行情")
            return df
            
        except Exception as e:
            logger.error(f"获取实时行情失败: {e}")
            return pd.DataFrame()
    
    def fetch_stock_basic_info(self, symbol: str) -> Dict:
        """
        获取股票基本信息
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 基本信息
        """
        try:
            symbol = self._normalize_symbol(symbol)
            logger.info(f"获取 {symbol} 基本信息...")
            
            # 获取报价信息
            quote_data = self._fetch_quote(symbol)
            
            if not quote_data:
                logger.warning(f"未找到 {symbol} 的信息")
                return {}
            
            # 提取基本信息
            basic_info = {
                'code': symbol,
                'name': quote_data.get('name', ''),
                'exchange': quote_data.get('exchange', ''),
                'currency': quote_data.get('currency', ''),
                'type': quote_data.get('type', ''),
                'price': float(quote_data.get('close', 0)),
                'volume': int(quote_data.get('volume', 0)),
                'market_cap': 0,  # Twelve Data 可能不直接提供
                'pe_ratio': 0,
                'pb_ratio': 0,
            }
            
            return basic_info
            
        except Exception as e:
            logger.error(f"获取股票基本信息失败 ({symbol}): {e}")
            return {}
    
    def fetch_index_daily(self, 
                         index_code: str, 
                         start_date: str, 
                         end_date: str) -> pd.DataFrame:
        """
        获取指数日线数据
        
        Args:
            index_code: 指数代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 指数日线数据
        """
        try:
            logger.info(f"获取指数 {index_code} 日线数据...")
            
            # 指数可以直接使用 fetch_stock_daily
            return self.fetch_stock_daily(index_code, start_date, end_date)
            
        except Exception as e:
            logger.error(f"获取指数数据失败 ({index_code}): {e}")
            return pd.DataFrame()
    
    def _fetch_time_series(self, 
                          symbol: str,
                          interval: str = '1day',
                          start_date: str = None,
                          end_date: str = None,
                          outputsize: int = 5000) -> pd.DataFrame:
        """
        获取时间序列数据（内部方法）
        
        Args:
            symbol: 股票代码
            interval: 时间间隔 ('1min', '5min', '1day' 等)
            start_date: 开始日期
            end_date: 结束日期
            outputsize: 返回数据量
            
        Returns:
            DataFrame: 时间序列数据
        """
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    logger.info(f"第 {attempt + 1}/{self.max_retries} 次尝试...")
                    time.sleep(self.retry_delay)
                
                url = f"{self.base_url}/time_series"
                params = {
                    'symbol': symbol,
                    'interval': interval,
                    'outputsize': min(outputsize, 5000),
                    'apikey': self.api_key
                }
                
                # 添加日期范围（如果支持）
                if start_date:
                    params['start_date'] = start_date
                if end_date:
                    params['end_date'] = end_date
                
                response = requests.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                if 'values' not in data:
                    logger.error(f"API返回异常: {data}")
                    if attempt == self.max_retries - 1:
                        return pd.DataFrame()
                    continue
                
                # 转换为DataFrame
                df = pd.DataFrame(data['values'])
                
                if df.empty:
                    return pd.DataFrame()
                
                # 确保数值类型
                for col in ['open', 'high', 'low', 'close']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce')
                
                if 'volume' in df.columns:
                    df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)
                else:
                    df['volume'] = 0
                
                # 按日期排序（正序）
                df = df.sort_values('datetime').reset_index(drop=True)
                
                return df
                
            except Exception as e:
                logger.warning(f"第 {attempt + 1} 次尝试失败: {e}")
                if attempt == self.max_retries - 1:
                    logger.error(f"所有 {self.max_retries} 次尝试均失败")
        
        return pd.DataFrame()
    
    def _fetch_quote(self, symbol: str) -> Dict:
        """
        获取实时报价（内部方法）
        
        Args:
            symbol: 股票代码
            
        Returns:
            Dict: 报价数据
        """
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    time.sleep(self.retry_delay)
                
                url = f"{self.base_url}/quote"
                params = {
                    'symbol': symbol,
                    'apikey': self.api_key
                }
                
                response = requests.get(url, params=params, timeout=10)
                response.raise_for_status()
                data = response.json()
                
                if 'code' in data and data['code'] != 200:
                    logger.error(f"API错误: {data}")
                    if attempt == self.max_retries - 1:
                        return {}
                    continue
                
                return data
                
            except Exception as e:
                logger.warning(f"获取报价失败 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1:
                    return {}
        
        return {}
    
    def fetch_forex_data(self, 
                        pair: str,
                        start_date: str,
                        end_date: str) -> pd.DataFrame:
        """
        获取外汇数据（Twelve Data 特色功能）
        
        Args:
            pair: 货币对（如 'EUR/USD', 'GBP/USD'）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 外汇数据
        """
        logger.info(f"获取外汇数据: {pair}")
        return self.fetch_stock_daily(pair, start_date, end_date)
    
    def fetch_crypto_data(self,
                         pair: str,
                         start_date: str,
                         end_date: str) -> pd.DataFrame:
        """
        获取加密货币数据（Twelve Data 特色功能）
        
        Args:
            pair: 加密货币对（如 'BTC/USD', 'ETH/USD'）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 加密货币数据
        """
        logger.info(f"获取加密货币数据: {pair}")
        return self.fetch_stock_daily(pair, start_date, end_date)
