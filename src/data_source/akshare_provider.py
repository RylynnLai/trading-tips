"""
AkShare 数据提供者

使用 AkShare 库获取中国股票市场数据
AkShare: https://github.com/akfamily/akshare
"""

from typing import List, Dict
import pandas as pd
from loguru import logger

try:
    import akshare as ak
except ImportError:
    logger.warning("AkShare 未安装，请运行: pip install akshare")
    ak = None

from .base_provider import BaseProvider


class AkShareProvider(BaseProvider):
    """
    AkShare 数据提供者
    
    主要支持A股市场数据获取
    """
    
    def __init__(self, config: Dict):
        """
        初始化 AkShare 数据提供者
        
        Args:
            config: 配置字典（AkShare 大部分接口不需要 API key）
        """
        super().__init__(config)
        
        if ak is None:
            raise ImportError("AkShare 未安装，请运行: pip install akshare")
        
        logger.info("AkShare 数据提供者初始化完成")
    
    def fetch_stock_list(self, market: str = 'A') -> pd.DataFrame:
        """
        获取股票列表
        
        Args:
            market: 市场类型 'A'(A股), 'HK'(港股), 'US'(美股)
            
        Returns:
            DataFrame: 股票列表
        """
        try:
            logger.info(f"获取{market}股票票列表...")
            
            if market == 'A':
                # 获取A股股票列表
                df = ak.stock_info_a_code_name()
                # 重命名列
                df = df.rename(columns={
                    'code': 'code',
                    'name': 'name'
                })
                df['market'] = 'A'
                
                logger.info(f"获取到 {len(df)} 只A股股票")
                return df
                
            elif market == 'HK':
                # 获取港股股票列表
                df = ak.stock_hk_spot()
                df = df.rename(columns={
                    '代码': 'code',
                    '名称': 'name'
                })
                df['market'] = 'HK'
                
                logger.info(f"获取到 {len(df)} 只港股股票")
                return df
                
            elif market == 'US':
                # 获取美股股票列表
                logger.warning("AkShare 对美股支持有限，建议使用 YFinance")
                return pd.DataFrame(columns=['code', 'name', 'market'])
            
            else:
                logger.error(f"不支持的市场类型: {market}")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"获取股票列表失败: {e}")
            return pd.DataFrame()
    
    def fetch_stock_daily(self, 
                         symbol: str, 
                         start_date: str, 
                         end_date: str) -> pd.DataFrame:
        """
        获取股票日线数据
        
        Args:
            symbol: 股票代码（如 '000001' 或 '600000'）
            start_date: 开始日期 (YYYYMMDD 或 YYYY-MM-DD)
            end_date: 结束日期
            
        Returns:
            DataFrame: 日线数据
        """
        try:
            symbol = self._normalize_symbol(symbol)
            # 转换日期格式
            start_date = start_date.replace('-', '')
            end_date = end_date.replace('-', '')
            
            logger.info(f"获取股票 {symbol} 日线数据: {start_date} - {end_date}")
            
            # 使用 AkShare 的股票历史行情接口
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date,
                end_date=end_date,
                adjust="qfq"  # 前复权
            )
            
            if df.empty:
                logger.warning(f"未获取到股票 {symbol} 的数据")
                return pd.DataFrame()
            
            # 标准化列名
            df = df.rename(columns={
                '日期': 'date',
                '开盘': 'open',
                '收盘': 'close',
                '最高': 'high',
                '最低': 'low',
                '成交量': 'volume',
                '成交额': 'amount',
                '振幅': 'amplitude',
                '涨跌幅': 'change_pct',
                '涨跌额': 'change',
                '换手率': 'turnover'
            })
            
            # 确保日期格式
            df['date'] = pd.to_datetime(df['date'])
            
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
            
            # 获取A股实时行情
            df = ak.stock_zh_a_spot_em()
            
            # 标准化列名
            df = df.rename(columns={
                '代码': 'code',
                '名称': 'name',
                '最新价': 'price',
                '涨跌额': 'change',
                '涨跌幅': 'change_pct',
                '成交量': 'volume',
                '成交额': 'amount',
                '今开': 'open',
                '最高': 'high',
                '最低': 'low',
                '昨收': 'pre_close',
                '换手率': 'turnover',
                '市盈率-动态': 'pe_ratio',
                '市净率': 'pb_ratio',
                '总市值': 'market_cap',
                '流通市值': 'circulating_market_cap'
            })
            
            # 筛选指定股票
            if symbols:
                symbols = [self._normalize_symbol(s) for s in symbols]
                df = df[df['code'].isin(symbols)]
            
            logger.info(f"获取到 {len(df)} 只股票的实时行情")
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
            logger.info(f"获取股票 {symbol} 基本信息...")
            
            # 获取实时行情（包含基本信息）
            df = self.fetch_stock_realtime([symbol])
            
            if df.empty:
                logger.warning(f"未找到股票 {symbol} 的信息")
                return {}
            
            # 转换为字典
            info = df.iloc[0].to_dict()
            
            return info
            
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
            index_code: 指数代码（如 'sh000001'=上证指数, 'sz399001'=深证成指）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 指数日线数据
        """
        try:
            start_date = start_date.replace('-', '')
            end_date = end_date.replace('-', '')
            
            logger.info(f"获取指数 {index_code} 日线数据...")
            
            df = ak.stock_zh_index_daily(symbol=index_code)
            
            # 筛选日期范围
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
            
            logger.info(f"获取到 {len(df)} 条指数数据")
            return df
            
        except Exception as e:
            logger.error(f"获取指数数据失败 ({index_code}): {e}")
            return pd.DataFrame()
    
    def fetch_fund_list(self) -> pd.DataFrame:
        """
        获取基金列表
        
        Returns:
            DataFrame: 基金列表
        """
        try:
            logger.info("获取基金列表...")
            
            # 获取开放式基金列表
            df = ak.fund_open_fund_info_em()
            
            df = df.rename(columns={
                '基金代码': 'code',
                '基金简称': 'name',
                '基金类型': 'type'
            })
            
            logger.info(f"获取到 {len(df)} 只基金")
            return df
            
        except Exception as e:
            logger.error(f"获取基金列表失败: {e}")
            return pd.DataFrame()
    
    def fetch_fund_nav(self, 
                      fund_code: str, 
                      start_date: str, 
                      end_date: str) -> pd.DataFrame:
        """
        获取基金净值数据
        
        Args:
            fund_code: 基金代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 基金净值数据
        """
        try:
            logger.info(f"获取基金 {fund_code} 净值数据...")
            
            # 获取基金历史净值
            df = ak.fund_open_fund_info_em(fund=fund_code, indicator="单位净值走势")
            
            if df.empty:
                return pd.DataFrame()
            
            # 标准化列名
            df = df.rename(columns={
                '净值日期': 'date',
                '单位净值': 'nav',
                '累计净值': 'acc_nav',
                '日增长率': 'daily_return'
            })
            
            # 筛选日期范围
            df['date'] = pd.to_datetime(df['date'])
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            df = df[(df['date'] >= start) & (df['date'] <= end)]
            
            logger.info(f"获取到 {len(df)} 条净值数据")
            return df
            
        except Exception as e:
            logger.error(f"获取基金净值失败 ({fund_code}): {e}")
            return pd.DataFrame()
