"""
技术指标计算模块

基于价量时空交易系统，实现核心技术指标的计算
包括：MA、EMA、抵扣价、乖离率、ATR等
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from loguru import logger


class TechnicalIndicators:
    """
    技术指标计算器
    
    实现价量时空交易系统中的核心指标
    """
    
    @staticmethod
    def calculate_ma(data: pd.DataFrame, periods: List[int] = [20, 60, 120], 
                     price_col: str = '收盘') -> pd.DataFrame:
        """
        计算移动平均线（MA）
        
        MA的本质 = 市场平均成本
        
        Args:
            data: 价格数据，必须包含收盘价列
            periods: 周期列表，默认[20, 60, 120]
            price_col: 价格列名
            
        Returns:
            DataFrame: 添加了MA列的数据
        """
        df = data.copy()
        
        for period in periods:
            col_name = f'MA{period}'
            df[col_name] = df[price_col].rolling(window=period, min_periods=period).mean()
            logger.debug(f"计算 {col_name}")
        
        return df
    
    @staticmethod
    def calculate_ema(data: pd.DataFrame, periods: List[int] = [20, 60, 120],
                      price_col: str = '收盘') -> pd.DataFrame:
        """
        计算指数移动平均线（EMA）
        
        EMA特点：对近期价格赋予更大权重
        只要价格站上EMA，EMA就开始向上
        
        Args:
            data: 价格数据
            periods: 周期列表
            price_col: 价格列名
            
        Returns:
            DataFrame: 添加了EMA列的数据
        """
        df = data.copy()
        
        for period in periods:
            col_name = f'EMA{period}'
            df[col_name] = df[price_col].ewm(span=period, adjust=False).mean()
            logger.debug(f"计算 {col_name}")
        
        return df
    
    @staticmethod
    def calculate_discount_price(data: pd.DataFrame, periods: List[int] = [20, 60, 120],
                                price_col: str = '收盘') -> pd.DataFrame:
        """
        计算抵扣价（核心中的核心）
        
        抵扣价原理：
        - MA5(明天) = (明天收盘 + 今天 + 昨天 + 前天 + 大前天) / 5
        - 如果 明天收盘 > 5天前收盘，则MA5向上
        - 抵扣价 = N天前的收盘价
        
        Args:
            data: 价格数据
            periods: 周期列表
            price_col: 价格列名
            
        Returns:
            DataFrame: 添加了抵扣价列的数据
        """
        df = data.copy()
        
        for period in periods:
            col_name = f'Discount{period}'
            # 抵扣价 = N天前的收盘价
            df[col_name] = df[price_col].shift(period)
            logger.debug(f"计算 {col_name}")
        
        return df
    
    @staticmethod
    def calculate_bias(data: pd.DataFrame, periods: List[int] = [20, 60, 120],
                      price_col: str = '收盘') -> pd.DataFrame:
        """
        计算乖离率
        
        乖离率 = (当前价格 - MA均线) / MA均线 × 100%
        
        极端乖离：
        - > 50%：严重超涨，警惕回调
        - < -50%：严重超跌，关注反弹
        
        Args:
            data: 价格数据
            periods: 周期列表
            price_col: 价格列名
            
        Returns:
            DataFrame: 添加了乖离率列的数据
        """
        df = data.copy()
        
        # 先计算MA（如果还没有）
        for period in periods:
            ma_col = f'MA{period}'
            if ma_col not in df.columns:
                df[ma_col] = df[price_col].rolling(window=period).mean()
            
            bias_col = f'Bias{period}'
            df[bias_col] = (df[price_col] - df[ma_col]) / df[ma_col] * 100
            logger.debug(f"计算 {bias_col}")
        
        return df
    
    @staticmethod
    def calculate_atr(data: pd.DataFrame, period: int = 14,
                     high_col: str = '最高', low_col: str = '最低', 
                     close_col: str = '收盘') -> pd.DataFrame:
        """
        计算ATR（真实波幅）
        
        用于动态止损位的设置
        
        Args:
            data: 价格数据
            period: 周期，默认14
            high_col: 最高价列名
            low_col: 最低价列名
            close_col: 收盘价列名
            
        Returns:
            DataFrame: 添加了ATR列的数据
        """
        df = data.copy()
        
        # 计算真实波幅TR
        df['H-L'] = df[high_col] - df[low_col]
        df['H-PC'] = abs(df[high_col] - df[close_col].shift(1))
        df['L-PC'] = abs(df[low_col] - df[close_col].shift(1))
        
        df['TR'] = df[['H-L', 'H-PC', 'L-PC']].max(axis=1)
        
        # 计算ATR（TR的移动平均）
        df[f'ATR{period}'] = df['TR'].rolling(window=period).mean()
        
        # 删除中间列
        df.drop(['H-L', 'H-PC', 'L-PC', 'TR'], axis=1, inplace=True)
        
        logger.debug(f"计算 ATR{period}")
        
        return df
    
    @staticmethod
    def calculate_ma_density(data: pd.DataFrame, 
                           periods: List[int] = [20, 60, 120]) -> pd.DataFrame:
        """
        计算均线密集度
        
        均线密集 = 各个均线之间的价差很小
        本质：市场各个时期交易者的成本趋于一致
        
        密集标准：
        - 周线：价差 < 5-10%
        - 日线：价差 < 3-5%
        
        Args:
            data: 包含MA列的数据
            periods: 均线周期列表
            
        Returns:
            DataFrame: 添加了密集度指标的数据
        """
        df = data.copy()
        
        # 确保MA列存在
        ma_cols = [f'MA{p}' for p in periods]
        missing_cols = [col for col in ma_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"缺少均线列: {missing_cols}，将先计算")
            df = TechnicalIndicators.calculate_ma(df, periods)
        
        # 计算密集度：最高均线与最低均线的差距百分比
        ma_values = df[ma_cols]
        df['MA_Max'] = ma_values.max(axis=1)
        df['MA_Min'] = ma_values.min(axis=1)
        df['MA_Density'] = (df['MA_Max'] - df['MA_Min']) / df['MA_Min'] * 100
        
        # 判断是否密集（< 5%）
        df['Is_Dense'] = df['MA_Density'] < 5.0
        
        logger.debug("计算均线密集度")
        
        return df
    
    @staticmethod
    def check_ma_alignment(data: pd.DataFrame, 
                          periods: List[int] = [20, 60, 120]) -> pd.DataFrame:
        """
        检查均线排列状态
        
        多头排列：MA20 > MA60 > MA120（短期成本 > 中期成本 > 长期成本）
        空头排列：MA20 < MA60 < MA120
        
        Args:
            data: 包含MA列的数据
            periods: 均线周期列表（必须是递增的）
            
        Returns:
            DataFrame: 添加了排列状态列的数据
        """
        df = data.copy()
        
        # 确保周期是递增的
        periods = sorted(periods)
        
        # 检查多头排列
        is_bull = True
        for i in range(len(periods) - 1):
            col1 = f'MA{periods[i]}'
            col2 = f'MA{periods[i+1]}'
            is_bull = is_bull & (df[col1] > df[col2])
        
        df['MA_Bull_Aligned'] = is_bull
        
        # 检查空头排列
        is_bear = True
        for i in range(len(periods) - 1):
            col1 = f'MA{periods[i]}'
            col2 = f'MA{periods[i+1]}'
            is_bear = is_bear & (df[col1] < df[col2])
        
        df['MA_Bear_Aligned'] = is_bear
        
        # 排列类型：bull, bear, mixed
        df['MA_Alignment'] = 'mixed'
        df.loc[df['MA_Bull_Aligned'], 'MA_Alignment'] = 'bull'
        df.loc[df['MA_Bear_Aligned'], 'MA_Alignment'] = 'bear'
        
        logger.debug("检查均线排列状态")
        
        return df
    
    @staticmethod
    def calculate_ma_slope(data: pd.DataFrame, 
                          periods: List[int] = [20, 60, 120],
                          slope_period: int = 5) -> pd.DataFrame:
        """
        计算均线斜率
        
        斜率 = 趋势强度
        - 开始阶段：斜率较缓
        - 发展阶段：真实斜率（稳定）
        - 极端阶段：斜率突然加大（加速）
        
        Args:
            data: 包含MA列的数据
            periods: 均线周期列表
            slope_period: 用于计算斜率的天数
            
        Returns:
            DataFrame: 添加了斜率列的数据
        """
        df = data.copy()
        
        for period in periods:
            ma_col = f'MA{period}'
            slope_col = f'MA{period}_Slope'
            
            # 斜率 = (当前MA - N天前MA) / N天前MA
            df[slope_col] = (df[ma_col] - df[ma_col].shift(slope_period)) / df[ma_col].shift(slope_period) * 100
        
        logger.debug("计算均线斜率")
        
        return df
    
    @staticmethod
    def calculate_volume_indicators(data: pd.DataFrame,
                                   periods: List[int] = [5, 60],
                                   volume_col: str = '成交量') -> pd.DataFrame:
        """
        计算成交量指标
        
        成交量的本质 = 市场分歧
        - 分歧越大 → 换手越多 → 成交量暴增
        - 没有分歧 → 换手越少 → 成交量萎缩
        
        Args:
            data: 包含成交量的数据
            periods: 均量周期
            volume_col: 成交量列名
            
        Returns:
            DataFrame: 添加了成交量指标的数据
        """
        df = data.copy()
        
        # 计算均量
        for period in periods:
            df[f'Vol_MA{period}'] = df[volume_col].rolling(window=period).mean()
        
        # 计算成交量比率（当前成交量 / 均量）
        if 'Vol_MA60' in df.columns:
            df['Vol_Ratio'] = df[volume_col] / df['Vol_MA60']
        
        # 识别放量（> 1.5倍均量）
        if 'Vol_Ratio' in df.columns:
            df['Is_High_Volume'] = df['Vol_Ratio'] > 1.5
            df['Is_Low_Volume'] = df['Vol_Ratio'] < 0.5
        
        logger.debug("计算成交量指标")
        
        return df
    
    @staticmethod
    def calculate_all_indicators(data: pd.DataFrame,
                                ma_periods: List[int] = [20, 60, 120],
                                price_col: str = '收盘',
                                high_col: str = '最高',
                                low_col: str = '最低',
                                volume_col: str = '成交量') -> pd.DataFrame:
        """
        计算所有技术指标（一站式计算）
        
        Args:
            data: 原始价格数据
            ma_periods: 均线周期
            price_col: 收盘价列名
            high_col: 最高价列名
            low_col: 最低价列名
            volume_col: 成交量列名
            
        Returns:
            DataFrame: 包含所有指标的数据
        """
        df = data.copy()
        
        logger.info("开始计算所有技术指标")
        
        # 1. 基础均线
        df = TechnicalIndicators.calculate_ma(df, ma_periods, price_col)
        df = TechnicalIndicators.calculate_ema(df, ma_periods, price_col)
        
        # 2. 抵扣价
        df = TechnicalIndicators.calculate_discount_price(df, ma_periods, price_col)
        
        # 3. 乖离率
        df = TechnicalIndicators.calculate_bias(df, ma_periods, price_col)
        
        # 4. ATR
        df = TechnicalIndicators.calculate_atr(df, 14, high_col, low_col, price_col)
        
        # 5. 均线密集度
        df = TechnicalIndicators.calculate_ma_density(df, ma_periods)
        
        # 6. 均线排列
        df = TechnicalIndicators.check_ma_alignment(df, ma_periods)
        
        # 7. 均线斜率
        df = TechnicalIndicators.calculate_ma_slope(df, ma_periods)
        
        # 8. 成交量指标
        if volume_col in df.columns:
            df = TechnicalIndicators.calculate_volume_indicators(df, [5, 60], volume_col)
        
        logger.info("所有技术指标计算完成")
        
        return df


def calculate_annual_return(data: pd.DataFrame, 
                           price_col: str = '收盘',
                           period_days: int = 252) -> pd.DataFrame:
    """
    计算年化收益率（用于趋势斜率分类）
    
    Args:
        data: 价格数据
        price_col: 价格列名
        period_days: 一年的交易日数量，默认252
        
    Returns:
        DataFrame: 添加了年化收益率的数据
    """
    df = data.copy()
    
    # 计算1年期收益率
    df['Price_1Y_Ago'] = df[price_col].shift(period_days)
    df['Annual_Return'] = (df[price_col] / df['Price_1Y_Ago']) - 1
    
    return df
