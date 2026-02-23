"""
趋势分析器

基于价量时空交易系统，实现趋势识别和分类
包括：趋势五阶段、时钟方向分类、均线密集区识别等
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from loguru import logger

from .indicators import TechnicalIndicators


class TrendAnalyzer:
    """
    趋势分析器
    
    实现趋势的识别、分类和推演
    核心理念：趋势 = 市场成本的运动 = 均线运动的方向
    """
    
    # 趋势类型常量
    TREND_DENSE_ZONE = '密集成交区'  # 横向整理，即将突破
    TREND_ACCELERATE_UP = '加速上涨'  # 斜率加速上涨（十二点钟方向）
    TREND_STABLE_UP = '稳定上涨'  # 稳定上涨（两点钟方向）
    TREND_STABLE_DOWN = '稳定下跌'  # 稳定下跌（四点钟方向）
    TREND_ACCELERATE_DOWN = '加速下跌'  # 斜率加速下跌（六点钟方向）
    TREND_UNDEFINED = '未定义'
    
    # 趋势阶段常量
    PHASE_TURNING = '转折'
    PHASE_START = '开始'
    PHASE_DEVELOP = '发展'
    PHASE_EXTREME = '极端'
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化趋势分析器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 趋势分类阈值
        self.dense_threshold = self.config.get('dense_threshold', 0.05)  # 5%
        self.accelerate_threshold = self.config.get('accelerate_threshold', 0.8)  # 80%年化
        self.stable_min = self.config.get('stable_min', 0.15)  # 15%年化
        self.stable_max = self.config.get('stable_max', 0.8)  # 80%年化
        
        logger.info("初始化趋势分析器")
    
    def classify_trend(self, data: pd.DataFrame, 
                      ma_periods: List[int] = [20, 60, 120]) -> str:
        """
        对趋势进行分类（时钟方向分类法）
        
        五种趋势类型：
        1. 密集成交区（横盘）- 6个月以上横向整理
        2. 加速上涨 - 年化收益 > 80%，斜率加速
        3. 稳定上涨 - 15% < 年化收益 <= 80%，多头排列
        4. 稳定下跌 - -80% <= 年化收益 < -15%，空头排列
        5. 加速下跌 - 年化收益 < -80%，斜率加速
        
        Args:
            data: 包含价格和指标的数据
            ma_periods: 均线周期
            
        Returns:
            str: 趋势类型
        """
        if len(data) < max(ma_periods):
            return self.TREND_UNDEFINED
        
        latest = data.iloc[-1]
        
        # 检查必要的列
        required_cols = ['MA_Density', 'Annual_Return', 'MA_Alignment']
        if not all(col in latest.index for col in required_cols):
            logger.warning("缺少必要的指标列，无法分类趋势")
            return self.TREND_UNDEFINED
        
        ma_density = latest['MA_Density']
        annual_return = latest['Annual_Return']
        ma_alignment = latest['MA_Alignment']
        
        # 1. 判断是否为密集成交区（优先级最高）
        if self._is_dense_zone(data, ma_density):
            return self.TREND_DENSE_ZONE
        
        # 2. 判断加速上涨
        if annual_return > self.accelerate_threshold and ma_alignment == 'bull':
            return self.TREND_ACCELERATE_UP
        
        # 3. 判断稳定上涨
        if self.stable_min < annual_return <= self.stable_max and ma_alignment == 'bull':
            return self.TREND_STABLE_UP
        
        # 4. 判断加速下跌
        if annual_return < -self.accelerate_threshold and ma_alignment == 'bear':
            return self.TREND_ACCELERATE_DOWN
        
        # 5. 判断稳定下跌
        if -self.stable_max <= annual_return < -self.stable_min and ma_alignment == 'bear':
            return self.TREND_STABLE_DOWN
        
        return self.TREND_UNDEFINED
    
    def _is_dense_zone(self, data: pd.DataFrame, ma_density: float) -> bool:
        """
        判断是否为密集成交区
        
        标准：
        - 均线密集度 < 5%
        - 横盘时长 >= 6个月（约120个交易日）
        
        Args:
            data: 价格数据
            ma_density: 均线密集度
            
        Returns:
            bool: 是否为密集成交区
        """
        # 密集度检查
        if ma_density >= self.dense_threshold * 100:  # 转换为百分比
            return False
        
        # 横盘时长检查（检查最近120天的波动）
        if len(data) < 120:
            return False
        
        recent_data = data.tail(120)
        price_col = '收盘' if '收盘' in data.columns else 'close'
        
        if price_col not in data.columns:
            return False
        
        high_price = recent_data[price_col].max()
        low_price = recent_data[price_col].min()
        volatility = (high_price - low_price) / low_price
        
        # 波动幅度 < 25% 认为是横盘
        return volatility < 0.25
    
    def identify_trend_phase(self, data: pd.DataFrame,
                           lookback: int = 60) -> str:
        """
        识别趋势所处的阶段
        
        趋势的五个阶段：转折 → 开始 → 发展 → 极端 → 转折
        
        通过观察斜率的变化来判断：
        - 开始阶段：斜率较缓
        - 发展阶段：真实斜率（稳定）
        - 极端阶段：斜率突然加大（加速）
        
        Args:
            data: 包含均线斜率的数据
            lookback: 回溯天数
            
        Returns:
            str: 趋势阶段
        """
        if len(data) < lookback:
            return self.PHASE_UNDEFINED
        
        recent_data = data.tail(lookback)
        
        # 使用MA60的斜率来判断
        slope_col = 'MA60_Slope'
        if slope_col not in recent_data.columns:
            return self.PHASE_UNDEFINED
        
        slopes = recent_data[slope_col].dropna()
        if len(slopes) < 20:
            return self.PHASE_UNDEFINED
        
        # 计算斜率的变化率
        slope_mean = slopes.mean()
        slope_std = slopes.std()
        latest_slope = slopes.iloc[-1]
        
        # 极端阶段：斜率突然加大（> 平均值 + 2倍标准差）
        if abs(latest_slope) > abs(slope_mean) + 2 * slope_std:
            return self.PHASE_EXTREME
        
        # 发展阶段：斜率稳定（在平均值附近）
        if abs(latest_slope - slope_mean) < slope_std:
            return self.PHASE_DEVELOP
        
        # 开始阶段：斜率较缓
        if abs(latest_slope) < abs(slope_mean):
            return self.PHASE_START
        
        return self.PHASE_TURNING
    
    def check_ma_turning(self, data: pd.DataFrame,
                        period: int = 20,
                        price_col: str = '收盘') -> Dict:
        """
        检查均线是否即将拐头（抵扣价推演）
        
        核心原理：
        - 如果 当前价格 > N天前的抵扣价，则MA向上
        - 如果 当前价格 < N天前的抵扣价，则MA向下
        
        Args:
            data: 价格数据
            period: 均线周期
            price_col: 价格列名
            
        Returns:
            Dict: 拐头分析结果
        """
        if len(data) < period:
            return {'can_turn': False, 'reason': '数据不足'}
        
        latest = data.iloc[-1]
        
        discount_col = f'Discount{period}'
        if discount_col not in latest.index:
            return {'can_turn': False, 'reason': f'缺少{discount_col}列'}
        
        current_price = latest[price_col]
        discount_price = latest[discount_col]
        
        if pd.isna(discount_price):
            return {'can_turn': False, 'reason': '抵扣价为空'}
        
        # 判断是否能向上拐头
        can_turn_up = current_price > discount_price
        
        # 计算需要突破的价格水平
        price_diff = abs(current_price - discount_price)
        price_diff_pct = price_diff / discount_price * 100
        
        return {
            'can_turn': True,
            'can_turn_up': can_turn_up,
            'current_price': current_price,
            'discount_price': discount_price,
            'price_diff': price_diff,
            'price_diff_pct': price_diff_pct,
            'direction': 'up' if can_turn_up else 'down'
        }
    
    def find_dense_zones(self, data: pd.DataFrame,
                        lookback: int = 252) -> List[Dict]:
        """
        寻找历史上的均线密集区
        
        均线密集区 = 未来的支撑位或阻力位
        
        Args:
            data: 包含均线数据
            lookback: 回溯天数（默认1年）
            
        Returns:
            List[Dict]: 密集区列表
        """
        if len(data) < lookback:
            lookback = len(data)
        
        recent_data = data.tail(lookback).copy()
        
        # 找出密集区（MA_Density < 5%）
        if 'MA_Density' not in recent_data.columns:
            return []
        
        dense_rows = recent_data[recent_data['MA_Density'] < 5.0]
        
        if len(dense_rows) == 0:
            return []
        
        # 将连续的密集区合并
        zones = []
        current_zone = None
        
        for idx, row in dense_rows.iterrows():
            if current_zone is None:
                current_zone = {
                    'start_date': idx,
                    'end_date': idx,
                    'price_center': row.get('MA60', row.get('收盘', 0)),
                    'count': 1
                }
            else:
                # 检查是否连续（间隔 < 10天）
                days_diff = (idx - current_zone['end_date']).days
                if days_diff <= 10:
                    current_zone['end_date'] = idx
                    current_zone['count'] += 1
                else:
                    zones.append(current_zone)
                    current_zone = {
                        'start_date': idx,
                        'end_date': idx,
                        'price_center': row.get('MA60', row.get('收盘', 0)),
                        'count': 1
                    }
        
        if current_zone is not None:
            zones.append(current_zone)
        
        # 只保留持续时间较长的密集区（>= 20天）
        zones = [z for z in zones if z['count'] >= 20]
        
        logger.info(f"找到 {len(zones)} 个均线密集区")
        
        return zones
    
    def calculate_target_price(self, data: pd.DataFrame,
                              current_price: float) -> List[Dict]:
        """
        计算目标位（基于均线密集区）
        
        方法：向上找到第一个、第二个均线密集区
        
        Args:
            data: 包含均线数据
            current_price: 当前价格
            
        Returns:
            List[Dict]: 目标位列表
        """
        zones = self.find_dense_zones(data)
        
        # 筛选出在当前价格上方的密集区
        upper_zones = [z for z in zones if z['price_center'] > current_price]
        
        # 按价格排序
        upper_zones = sorted(upper_zones, key=lambda x: x['price_center'])
        
        targets = []
        for i, zone in enumerate(upper_zones[:3]):  # 最多3个目标位
            target = {
                'level': i + 1,
                'price': zone['price_center'],
                'gain_pct': (zone['price_center'] - current_price) / current_price * 100,
                'zone_info': zone
            }
            targets.append(target)
        
        return targets
    
    def calculate_stop_loss(self, data: pd.DataFrame,
                          entry_price: float,
                          method: str = 'ma') -> Dict:
        """
        计算止损位
        
        方法：
        1. 'ma': 基于均线（跌破MA20）
        2. 'atr': 基于ATR（动态止损）
        3. 'percentage': 固定百分比
        
        Args:
            data: 价格数据
            entry_price: 入场价格
            method: 止损方法
            
        Returns:
            Dict: 止损信息
        """
        latest = data.iloc[-1]
        
        if method == 'ma':
            # 基于MA20
            ma20 = latest.get('MA20', entry_price * 0.95)
            stop_loss = ma20
            stop_loss_pct = (entry_price - stop_loss) / entry_price * 100
            
        elif method == 'atr':
            # 基于ATR（2倍ATR）
            atr = latest.get('ATR14', entry_price * 0.02)
            stop_loss = entry_price - 2 * atr
            stop_loss_pct = (entry_price - stop_loss) / entry_price * 100
            
        else:  # percentage
            # 固定5%
            stop_loss_pct = 5.0
            stop_loss = entry_price * (1 - stop_loss_pct / 100)
        
        return {
            'stop_loss': stop_loss,
            'stop_loss_pct': stop_loss_pct,
            'method': method
        }
    
    def analyze_trend(self, data: pd.DataFrame,
                     symbol: str = '') -> Dict:
        """
        综合趋势分析（一站式分析）
        
        Args:
            data: 包含所有指标的价格数据
            symbol: 标的代码
            
        Returns:
            Dict: 完整的趋势分析结果
        """
        if len(data) < 120:
            return {
                'symbol': symbol,
                'error': '数据不足（需要至少120天数据）'
            }
        
        latest = data.iloc[-1]
        
        # 1. 趋势分类
        trend_type = self.classify_trend(data)
        
        # 2. 趋势阶段
        trend_phase = self.identify_trend_phase(data)
        
        # 3. 均线拐头检查（20/60/120）
        ma20_turn = self.check_ma_turning(data, 20)
        ma60_turn = self.check_ma_turning(data, 60)
        ma120_turn = self.check_ma_turning(data, 120)
        
        # 4. 寻找密集区和目标位
        price_col = '收盘' if '收盘' in data.columns else 'close'
        current_price = latest[price_col]
        targets = self.calculate_target_price(data, current_price)
        
        # 5. 止损位
        stop_loss = self.calculate_stop_loss(data, current_price, 'ma')
        
        # 6. 盈亏比计算
        risk_reward_ratios = []
        if targets and stop_loss:
            for target in targets:
                potential_gain = target['gain_pct']
                potential_loss = stop_loss['stop_loss_pct']
                if potential_loss > 0:
                    ratio = potential_gain / potential_loss
                    risk_reward_ratios.append(ratio)
        
        analysis = {
            'symbol': symbol,
            'current_price': current_price,
            'trend_type': trend_type,
            'trend_phase': trend_phase,
            'ma_alignment': latest.get('MA_Alignment', 'unknown'),
            'ma_density': latest.get('MA_Density', 0),
            'is_dense': latest.get('Is_Dense', False),
            'annual_return': latest.get('Annual_Return', 0),
            'bias20': latest.get('Bias20', 0),
            'bias60': latest.get('Bias60', 0),
            'bias120': latest.get('Bias120', 0),
            'ma20_turn': ma20_turn,
            'ma60_turn': ma60_turn,
            'ma120_turn': ma120_turn,
            'targets': targets,
            'stop_loss': stop_loss,
            'risk_reward_ratios': risk_reward_ratios,
            'timestamp': latest.name if hasattr(latest, 'name') else None
        }
        
        logger.info(f"完成 {symbol} 的趋势分析：{trend_type}")
        
        return analysis
