"""
信号检测器

基于价量时空交易系统，实现交易信号的识别
包括：2B结构、突破信号、回撤信号、顶底构造等
"""

from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from loguru import logger


class SignalDetector:
    """
    交易信号检测器
    
    实现三大类交易机会的信号识别：
    1. 密集成交区突破信号
    2. 稳定趋势回撤信号
    3. 极端位置反转信号（2B结构）
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        初始化信号检测器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        logger.info("初始化信号检测器")
    
    def detect_2b_structure(self, data: pd.DataFrame,
                          lookback: int = 60,
                          price_col: str = '收盘',
                          tolerance: float = 0.01) -> Dict:
        """
        检测2B结构（趋势反转信号）
        
        2B结构定义：
        1. 出现一个低点A（或高点）
        2. 价格跌破A创新低（或突破创新高）
        3. 迅速回到A上方（或下方）
        
        2B结构的作用：
        - 只能解决过度偏离后的回归问题
        - 不代表大趋势反转，只代表短期反弹
        
        Args:
            data: 价格数据
            lookback: 回溯天数
            price_col: 价格列名
            tolerance: 容差（1%）
            
        Returns:
            Dict: 2B结构检测结果
        """
        if len(data) < lookback:
            return {'has_2b': False, 'reason': '数据不足'}
        
        recent_data = data.tail(lookback)
        
        # 检测2B底部结构（看涨）
        bullish_2b = self._detect_bullish_2b(recent_data, price_col, tolerance)
        
        # 检测2B顶部结构（看跌）
        bearish_2b = self._detect_bearish_2b(recent_data, price_col, tolerance)
        
        result = {
            'has_2b': bullish_2b['found'] or bearish_2b['found'],
            'bullish_2b': bullish_2b,
            'bearish_2b': bearish_2b
        }
        
        if result['has_2b']:
            signal_type = '看涨2B' if bullish_2b['found'] else '看跌2B'
            logger.info(f"检测到{signal_type}结构")
        
        return result
    
    def _detect_bullish_2b(self, data: pd.DataFrame,
                          price_col: str,
                          tolerance: float) -> Dict:
        """
        检测看涨2B结构（底部反转）
        
        Args:
            data: 价格数据
            price_col: 价格列名
            tolerance: 容差
            
        Returns:
            Dict: 检测结果
        """
        prices = data[price_col].values
        
        # 寻找前低点（最近30天的最低点之前的低点）
        recent_30 = prices[-30:] if len(prices) >= 30 else prices
        recent_low_idx = len(prices) - 30 + np.argmin(recent_30)
        
        if recent_low_idx < 10:  # 需要前面有足够数据
            return {'found': False}
        
        # 前低点
        prev_low_idx = np.argmin(prices[:recent_low_idx-5])
        prev_low = prices[prev_low_idx]
        
        # 最近低点
        recent_low = np.min(recent_30)
        
        # 当前价格
        current_price = prices[-1]
        
        # 检查是否满足2B条件：
        # 1. 最近低点跌破前低点
        # 2. 当前价格回到前低点上方
        broke_below = recent_low < prev_low * (1 - tolerance)
        recovered_above = current_price > prev_low * (1 + tolerance)
        
        if broke_below and recovered_above:
            return {
                'found': True,
                'type': 'bullish',
                'prev_low': prev_low,
                'recent_low': recent_low,
                'current_price': current_price,
                'break_pct': (prev_low - recent_low) / prev_low * 100,
                'recovery_pct': (current_price - recent_low) / recent_low * 100
            }
        
        return {'found': False}
    
    def _detect_bearish_2b(self, data: pd.DataFrame,
                          price_col: str,
                          tolerance: float) -> Dict:
        """
        检测看跌2B结构（顶部反转）
        
        Args:
            data: 价格数据
            price_col: 价格列名
            tolerance: 容差
            
        Returns:
            Dict: 检测结果
        """
        prices = data[price_col].values
        
        # 寻找前高点
        recent_30 = prices[-30:] if len(prices) >= 30 else prices
        recent_high_idx = len(prices) - 30 + np.argmax(recent_30)
        
        if recent_high_idx < 10:
            return {'found': False}
        
        # 前高点
        prev_high_idx = np.argmax(prices[:recent_high_idx-5])
        prev_high = prices[prev_high_idx]
        
        # 最近高点
        recent_high = np.max(recent_30)
        
        # 当前价格
        current_price = prices[-1]
        
        # 检查是否满足2B条件
        broke_above = recent_high > prev_high * (1 + tolerance)
        fell_below = current_price < prev_high * (1 - tolerance)
        
        if broke_above and fell_below:
            return {
                'found': True,
                'type': 'bearish',
                'prev_high': prev_high,
                'recent_high': recent_high,
                'current_price': current_price,
                'break_pct': (recent_high - prev_high) / prev_high * 100,
                'fall_pct': (recent_high - current_price) / recent_high * 100
            }
        
        return {'found': False}
    
    def detect_breakout_signal(self, data: pd.DataFrame,
                              ma_periods: List[int] = [20, 60, 120]) -> Dict:
        """
        检测密集成交区突破信号
        
        突破信号特征：
        1. 均线刚刚形成多头排列（MA20 > MA60 > MA120）
        2. 价格站上20日均线组
        3. 均线密集度 < 5%
        4. 成交量放大（> 1.5倍）
        
        Args:
            data: 包含指标的价格数据
            ma_periods: 均线周期
            
        Returns:
            Dict: 突破信号检测结果
        """
        if len(data) < max(ma_periods) + 10:
            return {'has_signal': False, 'reason': '数据不足'}
        
        latest = data.iloc[-1]
        prev = data.iloc[-2]
        
        # 检查必要的列
        required_cols = ['MA_Alignment', 'MA_Density', 'Is_Dense']
        if not all(col in latest.index for col in required_cols):
            return {'has_signal': False, 'reason': '缺少必要指标'}
        
        # 1. 检查多头排列
        is_bull_aligned = latest['MA_Alignment'] == 'bull'
        just_aligned = prev['MA_Alignment'] != 'bull' and is_bull_aligned  # 刚刚形成
        
        # 2. 检查均线密集
        is_dense = latest['Is_Dense'] or latest['MA_Density'] < 5.0
        
        # 3. 检查价格位置（站上MA20）
        price_col = '收盘' if '收盘' in data.columns else 'close'
        price_above_ma20 = latest[price_col] > latest['MA20']
        
        # 4. 检查成交量（如果有）
        volume_surge = False
        if 'Vol_Ratio' in latest.index:
            volume_surge = latest['Vol_Ratio'] > 1.5
        
        # 综合判断
        has_signal = is_bull_aligned and is_dense and price_above_ma20
        
        # 计算信号强度（0-100）
        strength = 0
        if is_bull_aligned:
            strength += 30
        if just_aligned:
            strength += 20
        if is_dense:
            strength += 20
        if price_above_ma20:
            strength += 20
        if volume_surge:
            strength += 10
        
        result = {
            'has_signal': has_signal,
            'signal_type': 'breakout',
            'strength': strength,
            'is_bull_aligned': is_bull_aligned,
            'just_aligned': just_aligned,
            'is_dense': is_dense,
            'price_above_ma20': price_above_ma20,
            'volume_surge': volume_surge,
            'ma_density': latest['MA_Density']
        }
        
        if has_signal:
            logger.info(f"检测到突破信号，强度: {strength}")
        
        return result
    
    def detect_pullback_signal(self, data: pd.DataFrame,
                              ma_periods: List[int] = [20, 60, 120]) -> Dict:
        """
        检测稳定趋势回撤信号
        
        回撤信号特征：
        1. 完美多头排列（MA20 > MA60 > MA120）
        2. 价格回撤到关键均线附近（MA20/60/120）
        3. 当前价 > 对应均线的抵扣价（确保均线不会拐头）
        4. 出现底部构造（可选）
        
        Args:
            data: 包含指标的价格数据
            ma_periods: 均线周期
            
        Returns:
            Dict: 回撤信号检测结果
        """
        if len(data) < max(ma_periods) + 10:
            return {'has_signal': False, 'reason': '数据不足'}
        
        latest = data.iloc[-1]
        
        # 1. 检查多头排列
        if latest.get('MA_Alignment') != 'bull':
            return {'has_signal': False, 'reason': '非多头排列'}
        
        price_col = '收盘' if '收盘' in data.columns else 'close'
        current_price = latest[price_col]
        
        # 2. 检查是否回撤到关键均线
        pullback_to = None
        pullback_pct = 100  # 距离百分比
        
        for period in ma_periods:
            ma_col = f'MA{period}'
            if ma_col not in latest.index:
                continue
            
            ma_value = latest[ma_col]
            distance_pct = abs(current_price - ma_value) / ma_value * 100
            
            # 如果价格在均线附近（±3%）
            if distance_pct < 3.0 and distance_pct < pullback_pct:
                pullback_to = period
                pullback_pct = distance_pct
        
        if pullback_to is None:
            return {'has_signal': False, 'reason': '未回撤到关键均线'}
        
        # 3. 检查抵扣价（确保均线不会拐头）
        discount_col = f'Discount{pullback_to}'
        if discount_col in latest.index:
            discount_price = latest[discount_col]
            if pd.notna(discount_price):
                safe_from_turn = current_price > discount_price
            else:
                safe_from_turn = True  # 无抵扣价数据，假设安全
        else:
            safe_from_turn = True
        
        # 4. 检查是否第一次回撤（更优质）
        is_first_pullback = self._is_first_pullback(data, pullback_to)
        
        # 综合判断
        has_signal = pullback_to is not None and safe_from_turn
        
        # 计算信号强度
        strength = 0
        if pullback_to == 20:
            strength += 30
        elif pullback_to == 60:
            strength += 40
        elif pullback_to == 120:
            strength += 50
        
        if is_first_pullback:
            strength += 30
        
        if safe_from_turn:
            strength += 20
        
        result = {
            'has_signal': has_signal,
            'signal_type': 'pullback',
            'strength': strength,
            'pullback_to': f'MA{pullback_to}' if pullback_to else None,
            'pullback_pct': pullback_pct,
            'is_first_pullback': is_first_pullback,
            'safe_from_turn': safe_from_turn
        }
        
        if has_signal:
            logger.info(f"检测到回撤信号: {result['pullback_to']}, 强度: {strength}")
        
        return result
    
    def _is_first_pullback(self, data: pd.DataFrame, ma_period: int) -> bool:
        """
        判断是否为第一次回撤到该均线
        
        Args:
            data: 价格数据
            ma_period: 均线周期
            
        Returns:
            bool: 是否第一次回撤
        """
        if len(data) < 60:
            return False
        
        recent_60 = data.tail(60)
        price_col = '收盘' if '收盘' in data.columns else 'close'
        ma_col = f'MA{ma_period}'
        
        if ma_col not in recent_60.columns:
            return False
        
        # 检查在过去60天内，价格触及该均线的次数
        touch_count = 0
        for _, row in recent_60.iterrows():
            distance_pct = abs(row[price_col] - row[ma_col]) / row[ma_col] * 100
            if distance_pct < 2.0:  # 在均线±2%范围内
                touch_count += 1
        
        # 如果触及次数 <= 5天，认为是第一次回撤
        return touch_count <= 5
    
    def detect_top_bottom_structure(self, data: pd.DataFrame,
                                   lookback: int = 30) -> Dict:
        """
        检测顶底构造
        
        没有构造就不会见顶见底
        
        顶部构造：M顶、头肩顶
        底部构造：W底、双底、圆弧底
        
        Args:
            data: 价格数据
            lookback: 回溯天数
            
        Returns:
            Dict: 顶底构造检测结果
        """
        if len(data) < lookback:
            return {'has_structure': False, 'reason': '数据不足'}
        
        recent_data = data.tail(lookback)
        price_col = '收盘' if '收盘' in data.columns else 'close'
        
        # 检测双底（W底）
        double_bottom = self._detect_double_bottom(recent_data, price_col)
        
        # 检测双顶（M顶）
        double_top = self._detect_double_top(recent_data, price_col)
        
        result = {
            'has_structure': double_bottom['found'] or double_top['found'],
            'double_bottom': double_bottom,
            'double_top': double_top
        }
        
        if result['has_structure']:
            structure_type = '双底' if double_bottom['found'] else '双顶'
            logger.info(f"检测到{structure_type}构造")
        
        return result
    
    def _detect_double_bottom(self, data: pd.DataFrame, price_col: str) -> Dict:
        """
        检测双底构造（W底）
        
        特征：
        1. 出现两个低点
        2. 两个低点价格相近（差距 < 3%）
        3. 中间有一个高点
        
        Args:
            data: 价格数据
            price_col: 价格列名
            
        Returns:
            Dict: 检测结果
        """
        prices = data[price_col].values
        
        if len(prices) < 15:
            return {'found': False}
        
        # 简单的波峰波谷检测
        from scipy.signal import find_peaks
        
        # 找波谷（低点）
        valleys, _ = find_peaks(-prices, distance=5)
        
        if len(valleys) < 2:
            return {'found': False}
        
        # 取最后两个波谷
        valley1_idx = valleys[-2]
        valley2_idx = valleys[-1]
        
        valley1_price = prices[valley1_idx]
        valley2_price = prices[valley2_idx]
        
        # 检查两个低点是否相近（差距 < 3%）
        price_diff_pct = abs(valley1_price - valley2_price) / valley1_price * 100
        
        if price_diff_pct < 3.0:
            # 检查中间是否有高点
            between_prices = prices[valley1_idx:valley2_idx+1]
            peak_price = np.max(between_prices)
            
            rebound_pct = (peak_price - valley1_price) / valley1_price * 100
            
            # 反弹幅度 > 3% 才算有效
            if rebound_pct > 3.0:
                return {
                    'found': True,
                    'type': 'double_bottom',
                    'valley1_price': valley1_price,
                    'valley2_price': valley2_price,
                    'peak_price': peak_price,
                    'price_diff_pct': price_diff_pct,
                    'rebound_pct': rebound_pct
                }
        
        return {'found': False}
    
    def _detect_double_top(self, data: pd.DataFrame, price_col: str) -> Dict:
        """
        检测双顶构造（M顶）
        
        Args:
            data: 价格数据
            price_col: 价格列名
            
        Returns:
            Dict: 检测结果
        """
        prices = data[price_col].values
        
        if len(prices) < 15:
            return {'found': False}
        
        from scipy.signal import find_peaks
        
        # 找波峰（高点）
        peaks, _ = find_peaks(prices, distance=5)
        
        if len(peaks) < 2:
            return {'found': False}
        
        # 取最后两个波峰
        peak1_idx = peaks[-2]
        peak2_idx = peaks[-1]
        
        peak1_price = prices[peak1_idx]
        peak2_price = prices[peak2_idx]
        
        # 检查两个高点是否相近
        price_diff_pct = abs(peak1_price - peak2_price) / peak1_price * 100
        
        if price_diff_pct < 3.0:
            # 检查中间是否有低点
            between_prices = prices[peak1_idx:peak2_idx+1]
            valley_price = np.min(between_prices)
            
            pullback_pct = (peak1_price - valley_price) / peak1_price * 100
            
            # 回调幅度 > 3% 才算有效
            if pullback_pct > 3.0:
                return {
                    'found': True,
                    'type': 'double_top',
                    'peak1_price': peak1_price,
                    'peak2_price': peak2_price,
                    'valley_price': valley_price,
                    'price_diff_pct': price_diff_pct,
                    'pullback_pct': pullback_pct
                }
        
        return {'found': False}
    
    def detect_all_signals(self, data: pd.DataFrame) -> Dict:
        """
        检测所有交易信号（一站式检测）
        
        Args:
            data: 包含所有指标的价格数据
            
        Returns:
            Dict: 所有信号检测结果
        """
        logger.info("开始检测所有交易信号")
        
        signals = {
            '2b_structure': self.detect_2b_structure(data),
            'breakout': self.detect_breakout_signal(data),
            'pullback': self.detect_pullback_signal(data),
            'top_bottom': self.detect_top_bottom_structure(data)
        }
        
        # 统计有效信号数量
        active_signals = []
        for signal_type, signal_data in signals.items():
            if signal_data.get('has_signal') or signal_data.get('has_2b') or signal_data.get('has_structure'):
                active_signals.append(signal_type)
        
        signals['active_signals'] = active_signals
        signals['signal_count'] = len(active_signals)
        
        logger.info(f"检测到 {len(active_signals)} 个活跃信号: {active_signals}")
        
        return signals
