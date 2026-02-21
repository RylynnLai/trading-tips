"""
YFinance 数据提供者

使用 yfinance 库获取全球市场股票数据
yfinance: https://github.com/ranaroussi/yfinance
"""

from typing import List, Dict
import pandas as pd
from loguru import logger

try:
    import yfinance as yf
except ImportError:
    logger.warning("yfinance 未安装，请运行: pip install yfinance")
    yf = None

from .base_provider import BaseProvider


class YFinanceProvider(BaseProvider):
    """
    YFinance 数据提供者
    
    主要支持美股、港股等全球市场数据
    """
    
    def __init__(self, config: Dict):
        """
        初始化 YFinance 数据提供者
        
        Args:
            config: 配置字典（yfinance 不需要 API key）
        """
        super().__init__(config)
        
        if yf is None:
            raise ImportError("yfinance 未安装，请运行: pip install yfinance")
        
        logger.info("YFinance 数据提供者初始化完成")
    
    def fetch_stock_list(self, market: str = 'US') -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            market: 市场类型 'US'(美股), 'HK'(港股), 'A'(A股)
            
        Returns:
            DataFrame: 股票列表
            
        Note:
            yfinance 不提供直接的股票列表API，需要其他方式获取
        """
        logger.warning("YFinance 不提供股票列表API，请使用其他数据源获取股票列表")
        return pd.DataFrame(columns=['code', 'name', 'market'])
    
    def fetch_stock_daily(self, 
                         symbol: str, 
                         start_date: str, 
                         end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            symbol: 股票代码（如 'AAPL', '0700.HK', '000001.SZ'）
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            DataFrame: 日线数据
        """
        try:
            symbol = self._format_symbol(symbol)
            
            logger.info(f"获取股票 {symbol} 日线数据: {start_date} - {end_date}")
            
            # 创建股票对象
            stock = yf.Ticker(symbol)
            
            # 获取历史数据
            df = stock.history(start=start_date, end=end_date)
            
            if df.empty:
                logger.warning(f"未获取到股票 {symbol} 的数据")
                return pd.DataFrame()
            
            # 重置索引，将日期从索引转为列
            df.reset_index(inplace=True)
            
            # 标准化列名
            df = df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            # 计算成交额（价格 * 成交量）
            df['amount'] = df['close'] * df['volume']
            
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
                    formatted_symbol = self._format_symbol(symbol)
                    stock = yf.Ticker(formatted_symbol)
                    
                    # 获取实时报价
                    info = stock.info
                    
                    if not info:
                        continue
                    
                    data = {
                        'code': symbol,
                        'name': info.get('longName', info.get('shortName', '')),
                        'price': info.get('currentPrice', info.get('regularMarketPrice', 0)),
                        'open': info.get('regularMarketOpen', 0),
                        'high': info.get('dayHigh', 0),
                        'low': info.get('dayLow', 0),
                        'pre_close': info.get('previousClose', 0),
                        'volume': info.get('volume', 0),
                        'market_cap': info.get('marketCap', 0),
                        'pe_ratio': info.get('trailingPE', 0),
                        'pb_ratio': info.get('priceToBook', 0),
                    }
                    
                    # 计算涨跌额和涨跌幅
                    if data['pre_close'] > 0:
                        data['change'] = data['price'] - data['pre_close']
                        data['change_pct'] = (data['change'] / data['pre_close']) * 100
                    else:
                        data['change'] = 0
                        data['change_pct'] = 0
                    
                    all_data.append(data)
                    
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
            symbol = self._format_symbol(symbol)
            logger.info(f"获取股票 {symbol} 基本信息...")
            
            stock = yf.Ticker(symbol)
            info = stock.info
            
            if not info:
                logger.warning(f"未找到股票 {symbol} 的信息")
                return {}
            
            # 提取关键信息
            basic_info = {
                'code': symbol,
                'name': info.get('longName', info.get('shortName', '')),
                'sector': info.get('sector', ''),
                'industry': info.get('industry', ''),
                'market_cap': info.get('marketCap', 0),
                'pe_ratio': info.get('trailingPE', 0),
                'forward_pe': info.get('forwardPE', 0),
                'pb_ratio': info.get('priceToBook', 0),
                'dividend_yield': info.get('dividendYield', 0),
                'beta': info.get('beta', 0),
                'eps': info.get('trailingEps', 0),
                'revenue': info.get('totalRevenue', 0),
                'profit_margin': info.get('profitMargins', 0),
                'roe': info.get('returnOnEquity', 0),
                'debt_to_equity': info.get('debtToEquity', 0),
                'description': info.get('longBusinessSummary', ''),
                'website': info.get('website', ''),
                'country': info.get('country', ''),
                'currency': info.get('currency', ''),
                'exchange': info.get('exchange', ''),
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
            index_code: 指数代码（如 '^GSPC'=标普500, '^DJI'=道琼斯）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 指数日线数据
        """
        try:
            logger.info(f"获取指数 {index_code} 日线数据...")
            
            # 指数代码通常以 ^ 开头
            if not index_code.startswith('^'):
                index_code = '^' + index_code
            
            return self.fetch_stock_daily(index_code, start_date, end_date)
            
        except Exception as e:
            logger.error(f"获取指数数据失败 ({index_code}): {e}")
            return pd.DataFrame()
    
    def _format_symbol(self, symbol: str) -> str:
        """
        格式化股票代码为 yfinance 格式
        
        Args:
            symbol: 原始股票代码
            
        Returns:
            str: 格式化后的代码
            
        Examples:
            000001 -> 000001.SZ (深圳)
            600000 -> 600000.SS (上海)
            0700 -> 0700.HK (香港)
            AAPL -> AAPL (美股)
        """
        symbol = self._normalize_symbol(symbol)
        
        # 如果已经包含市场后缀，直接返回
        if '.' in symbol or '^' in symbol:
            return symbol
        
        # A股代码格式化
        if symbol.isdigit():
            if len(symbol) == 6:
                # 6位数字代码
                if symbol.startswith('6'):
                    return f"{symbol}.SS"  # 上海
                elif symbol.startswith(('0', '3')):
                    return f"{symbol}.SZ"  # 深圳
            elif len(symbol) == 4:
                # 4位数字可能是港股
                return f"{symbol}.HK"
        
        # 默认返回原代码（美股等）
        return symbol
    
    def fetch_stock_minute(self, 
                          symbol: str, 
                          interval: str = '1m',
                          period: str = '1d') -> pd.DataFrame:
        """
        获取分钟级数据
        
        Args:
            symbol: 股票代码
            interval: 时间间隔 ('1m', '5m', '15m', '30m', '60m')
            period: 时间周期 ('1d', '5d', '1mo', '3mo')
            
        Returns:
            DataFrame: 分钟级数据
        """
        try:
            symbol = self._format_symbol(symbol)
            logger.info(f"获取股票 {symbol} {interval} 分钟数据...")
            
            stock = yf.Ticker(symbol)
            df = stock.history(period=period, interval=interval)
            
            if df.empty:
                return pd.DataFrame()
            
            df.reset_index(inplace=True)
            df = df.rename(columns={
                'Datetime': 'datetime',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Volume': 'volume'
            })
            
            logger.info(f"获取到 {len(df)} 条分钟数据")
            return df
            
        except Exception as e:
            logger.error(f"获取分钟数据失败 ({symbol}): {e}")
            return pd.DataFrame()
