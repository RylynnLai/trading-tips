"""
趋势交易策略

基于价量时空交易系统的完整策略实现
整合技术指标、趋势分析和信号检测，生成交易推荐
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from loguru import logger

from .base_strategy import BaseStrategy
from .indicators import TechnicalIndicators, calculate_annual_return
from .trend_analyzer import TrendAnalyzer
from .signal_detector import SignalDetector
from .profit_predictor import ProfitPredictor, add_profit_prediction


class TrendFollowingStrategy(BaseStrategy):
    """
    趋势跟随策略
    
    基于价量时空交易系统，实现三大类交易机会的识别：
    1. 密集成交区突破策略（最推荐）- 横盘突破，空间大
    2. 稳定趋势回撤策略（最稳健）- 趋势回调，风险小
    3. 斜率加速策略（高风险高收益）- 只持有不追高
    """
    
    def __init__(self, config: Dict):
        """
        初始化趋势跟随策略
        
        Args:
            config: 策略配置
        """
        super().__init__(config)
        
        # 初始化各个分析器
        self.indicator_calculator = TechnicalIndicators()
        self.trend_analyzer = TrendAnalyzer(config.get('trend_analyzer', {}))
        self.signal_detector = SignalDetector(config.get('signal_detector', {}))
        self.profit_predictor = ProfitPredictor(config.get('profit_predictor', {}))
        
        # 策略参数
        self.ma_periods = config.get('ma_periods', [20, 60, 120])
        self.min_data_points = config.get('min_data_points', 252)  # 至少1年数据
        
        # 推荐阈值
        self.min_score = config.get('min_score', 60)  # 最低评分
        self.max_recommendations = config.get('max_recommendations', 20)  # 最多推荐数量
        
        logger.info(f"初始化趋势跟随策略: {self.name}")
    
    def analyze(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        分析数据并生成信号
        
        Args:
            data: 输入数据（必须包含：日期、开盘、最高、最低、收盘、成交量）
            
        Returns:
            DataFrame: 包含分析结果和信号的数据
        """
        logger.info(f"开始分析数据，数据量: {len(data)} 条")
        
        # 数据验证
        if len(data) < self.min_data_points:
            logger.warning(f"数据不足（{len(data)} < {self.min_data_points}），跳过分析")
            return data
        
        # 1. 计算所有技术指标
        df = self.indicator_calculator.calculate_all_indicators(
            data,
            ma_periods=self.ma_periods
        )
        
        # 2. 计算年化收益率（用于趋势分类）
        df = calculate_annual_return(df)
        
        logger.info("技术指标计算完成")
        
        return df
    
    def generate_recommendations(self, analyzed_data: pd.DataFrame) -> List[Dict]:
        """
        根据分析结果生成推荐
        
        Args:
            analyzed_data: 分析后的数据
            
        Returns:
            List[Dict]: 推荐列表
        """
        if len(analyzed_data) == 0:
            return []
        
        logger.info("开始生成推荐")
        
        # 1. 趋势分析
        trend_analysis = self.trend_analyzer.analyze_trend(analyzed_data)
        
        # 2. 信号检测
        signals = self.signal_detector.detect_all_signals(analyzed_data)
        
        # 3. 综合评分和推荐生成
        recommendation = self._generate_recommendation(
            analyzed_data,
            trend_analysis,
            signals
        )
        
        return [recommendation] if recommendation else []
    
    def _generate_recommendation(self,
                                data: pd.DataFrame,
                                trend_analysis: Dict,
                                signals: Dict) -> Optional[Dict]:
        """
        生成单个标的的推荐
        
        Args:
            data: 分析后的数据
            trend_analysis: 趋势分析结果
            signals: 信号检测结果
            
        Returns:
            Dict or None: 推荐信息
        """
        trend_type = trend_analysis.get('trend_type')
        
        # 根据趋势类型选择策略
        if trend_type == TrendAnalyzer.TREND_DENSE_ZONE:
            return self._recommend_breakout(data, trend_analysis, signals)
        
        elif trend_type == TrendAnalyzer.TREND_STABLE_UP:
            return self._recommend_pullback(data, trend_analysis, signals)
        
        elif trend_type == TrendAnalyzer.TREND_ACCELERATE_UP:
            return self._recommend_hold(data, trend_analysis, signals)
        
        # 其他趋势类型暂不推荐
        return None
    
    def _recommend_breakout(self,
                          data: pd.DataFrame,
                          trend_analysis: Dict,
                          signals: Dict) -> Optional[Dict]:
        """
        密集成交区突破推荐
        
        适用场景：横向整理6个月以上，即将突破
        
        Args:
            data: 数据
            trend_analysis: 趋势分析
            signals: 信号检测
            
        Returns:
            Dict or None: 推荐
        """
        breakout_signal = signals.get('breakout', {})
        
        if not breakout_signal.get('has_signal'):
            return None
        
        # 计算评分（0-100）
        score = 0
        reasons = []
        
        # 1. 均线密集（30分）
        if breakout_signal.get('is_dense'):
            score += 30
            reasons.append(f"均线密集度{trend_analysis['ma_density']:.2f}%")
        
        # 2. 多头排列（25分）
        if breakout_signal.get('is_bull_aligned'):
            score += 25
            if breakout_signal.get('just_aligned'):
                score += 10
                reasons.append("刚刚形成多头排列")
            else:
                reasons.append("多头排列")
        
        # 3. 价格站上MA20（15分）
        if breakout_signal.get('price_above_ma20'):
            score += 15
            reasons.append("价格突破MA20")
        
        # 4. 成交量放大（10分）
        if breakout_signal.get('volume_surge'):
            score += 10
            reasons.append("成交量放大")
        
        # 5. 盈亏比优势（20分）
        risk_reward_ratios = trend_analysis.get('risk_reward_ratios', [])
        if risk_reward_ratios and max(risk_reward_ratios) > 3:
            score += 20
            reasons.append(f"盈亏比{max(risk_reward_ratios):.1f}:1")
        
        if score < self.min_score:
            return None
        
        # 生成推荐
        latest = data.iloc[-1]
        price_col = '收盘' if '收盘' in data.columns else 'close'
        
        recommendation = {
            'symbol': trend_analysis.get('symbol', ''),
            'strategy': '密集成交区突破',
            'priority': '⭐⭐⭐',  # 最推荐
            'score': score,
            'current_price': latest[price_col],
            'trend_type': trend_analysis['trend_type'],
            'ma_alignment': trend_analysis['ma_alignment'],
            'entry_signal': '突破MA20且均线密集',
            'stop_loss': trend_analysis['stop_loss']['stop_loss'],
            'stop_loss_pct': trend_analysis['stop_loss']['stop_loss_pct'],
            'targets': trend_analysis.get('targets', []),
            'risk_reward': max(risk_reward_ratios) if risk_reward_ratios else 0,
            'reasons': reasons,
            'signals': {
                'breakout': True,
                'strength': breakout_signal.get('strength', 0)
            }
        }
        
        # 添加盈利预测
        recommendation = add_profit_prediction(
            recommendation, data, trend_analysis, self.config.get('profit_predictor', {})
        )
        
        logger.info(f"生成突破推荐，评分: {score}")
        
        return recommendation
    
    def _recommend_pullback(self,
                          data: pd.DataFrame,
                          trend_analysis: Dict,
                          signals: Dict) -> Optional[Dict]:
        """
        稳定趋势回撤推荐
        
        适用场景：稳定上升趋势，回踩关键均线
        
        Args:
            data: 数据
            trend_analysis: 趋势分析
            signals: 信号检测
            
        Returns:
            Dict or None: 推荐
        """
        pullback_signal = signals.get('pullback', {})
        
        if not pullback_signal.get('has_signal'):
            return None
        
        # 计算评分（0-100）
        score = 0
        reasons = []
        
        # 1. 多头排列（20分）
        if trend_analysis['ma_alignment'] == 'bull':
            score += 20
            reasons.append("完美多头排列")
        
        # 2. 回撤到关键均线（30-50分，根据均线级别）
        pullback_to = pullback_signal.get('pullback_to')
        if pullback_to == 'MA120':
            score += 50
            reasons.append("第一次回撤到MA120")
        elif pullback_to == 'MA60':
            score += 40
            reasons.append("回撤到MA60")
        elif pullback_to == 'MA20':
            score += 30
            reasons.append("回撤到MA20")
        
        # 3. 第一次回撤（加15分）
        if pullback_signal.get('is_first_pullback'):
            score += 15
            reasons.append("首次回撤（质量最好）")
        
        # 4. 抵扣价安全（10分）
        if pullback_signal.get('safe_from_turn'):
            score += 10
            reasons.append("抵扣价安全，均线不会拐头")
        
        # 5. 底部构造（15分）
        top_bottom = signals.get('top_bottom', {})
        if top_bottom.get('has_structure') and top_bottom.get('double_bottom', {}).get('found'):
            score += 15
            reasons.append("出现双底构造")
        
        if score < self.min_score:
            return None
        
        # 生成推荐
        latest = data.iloc[-1]
        price_col = '收盘' if '收盘' in data.columns else 'close'
        
        recommendation = {
            'symbol': trend_analysis.get('symbol', ''),
            'strategy': '稳定趋势回撤',
            'priority': '⭐⭐⭐',  # 最稳健
            'score': score,
            'current_price': latest[price_col],
            'trend_type': trend_analysis['trend_type'],
            'ma_alignment': trend_analysis['ma_alignment'],
            'entry_signal': f"回撤到{pullback_to}",
            'stop_loss': trend_analysis['stop_loss']['stop_loss'],
            'stop_loss_pct': trend_analysis['stop_loss']['stop_loss_pct'],
            'targets': trend_analysis.get('targets', []),
            'risk_reward': max(trend_analysis.get('risk_reward_ratios', [0])),
            'reasons': reasons,
            'signals': {
                'pullback': True,
                'pullback_to': pullback_to,
                'is_first': pullback_signal.get('is_first_pullback'),
                'strength': pullback_signal.get('strength', 0)
            }
        }
        
        # 添加盈利预测
        recommendation = add_profit_prediction(
            recommendation, data, trend_analysis, self.config.get('profit_predictor', {})
        )
        
        logger.info(f"生成回撤推荐，评分: {score}")
        
        return recommendation
    
    def _recommend_hold(self,
                       data: pd.DataFrame,
                       trend_analysis: Dict,
                       signals: Dict) -> Optional[Dict]:
        """
        加速行情持有推荐
        
        适用场景：已有持仓，加速上涨中，持有不追高
        
        Args:
            data: 数据
            trend_analysis: 趋势分析
            signals: 信号检测
            
        Returns:
            Dict or None: 推荐（提示持有）
        """
        # 检查是否出现顶部构造
        top_bottom = signals.get('top_bottom', {})
        has_top = top_bottom.get('double_top', {}).get('found', False)
        
        # 检查是否乖离过大
        bias120 = trend_analysis.get('bias120', 0)
        extreme_bias = abs(bias120) > 50
        
        latest = data.iloc[-1]
        price_col = '收盘' if '收盘' in data.columns else 'close'
        
        # 如果出现危险信号
        if has_top or extreme_bias:
            recommendation = {
                'symbol': trend_analysis.get('symbol', ''),
                'strategy': '加速行情-警惕',
                'priority': '⚠️',
                'score': 0,
                'current_price': latest[price_col],
                'trend_type': trend_analysis['trend_type'],
                'ma_alignment': trend_analysis['ma_alignment'],
                'entry_signal': '不建议追高',
                'exit_signal': '关注顶部构造和均线死叉',
                'reasons': [],
                'warnings': []
            }
            
            if has_top:
                recommendation['warnings'].append("出现双顶构造")
            
            if extreme_bias:
                recommendation['warnings'].append(f"乖离率{bias120:.1f}%，严重偏离")
            
            # 添加盈利预测（警惕状态）
            recommendation = add_profit_prediction(
                recommendation, data, trend_analysis, self.config.get('profit_predictor', {})
            )
            
            logger.info("生成加速行情警惕提示")
            return recommendation
        
        # 否则，建议继续持有
        recommendation = {
            'symbol': trend_analysis.get('symbol', ''),
            'strategy': '加速行情-持有',
            'priority': '⭐',
            'score': 50,
            'current_price': latest[price_col],
            'trend_type': trend_analysis['trend_type'],
            'ma_alignment': trend_analysis['ma_alignment'],
            'entry_signal': '不建议追高',
            'hold_signal': '已有持仓继续持有',
            'exit_signal': '等待均线死叉或顶部构造',
            'reasons': [
                '加速上涨中',
                '尚未出现顶部构造',
                f'乖离率{bias120:.1f}%，未到极端'
            ],
            'signals': {}
        }
        
        # 添加盈利预测
        recommendation = add_profit_prediction(
            recommendation, data, trend_analysis, self.config.get('profit_predictor', {})
        )
        
        logger.info("生成加速行情持有建议")
        return recommendation
    
    def batch_analyze(self, symbols_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """
        批量分析多个标的
        
        Args:
            symbols_data: {symbol: DataFrame} 字典
            
        Returns:
            List[Dict]: 所有推荐列表，按评分排序
        """
        logger.info(f"开始批量分析 {len(symbols_data)} 个标的")
        
        all_recommendations = []
        
        for symbol, data in symbols_data.items():
            try:
                # 分析单个标的
                analyzed_data = self.analyze(data)
                
                # 生成推荐
                trend_analysis = self.trend_analyzer.analyze_trend(analyzed_data, symbol)
                signals = self.signal_detector.detect_all_signals(analyzed_data)
                
                recommendation = self._generate_recommendation(
                    analyzed_data,
                    trend_analysis,
                    signals
                )
                
                if recommendation:
                    recommendation['symbol'] = symbol
                    all_recommendations.append(recommendation)
                    
            except Exception as e:
                logger.error(f"分析 {symbol} 时出错: {e}")
                continue
        
        # 按评分排序
        all_recommendations.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # 限制推荐数量
        all_recommendations = all_recommendations[:self.max_recommendations]
        
        logger.info(f"批量分析完成，生成 {len(all_recommendations)} 个推荐")
        
        return all_recommendations
    
    def format_recommendation(self, recommendation: Dict) -> str:
        """
        格式化推荐为易读的文本
        
        Args:
            recommendation: 推荐字典
            
        Returns:
            str: 格式化后的文本
        """
        lines = []
        
        lines.append(f"\n{'='*60}")
        lines.append(f"标的: {recommendation['symbol']}")
        lines.append(f"策略: {recommendation['strategy']} {recommendation['priority']}")
        lines.append(f"评分: {recommendation['score']}/100")
        lines.append(f"当前价格: {recommendation['current_price']:.2f}")
        lines.append(f"趋势类型: {recommendation['trend_type']}")
        lines.append(f"均线排列: {recommendation['ma_alignment']}")
        lines.append(f"{'='*60}")
        
        # 入场信号
        if 'entry_signal' in recommendation:
            lines.append(f"\n入场信号: {recommendation['entry_signal']}")
        
        # 止损
        if 'stop_loss' in recommendation:
            lines.append(f"止损位: {recommendation['stop_loss']:.2f} (-{recommendation['stop_loss_pct']:.1f}%)")
        
        # 目标位
        if recommendation.get('targets'):
            lines.append(f"\n目标位:")
            for target in recommendation['targets']:
                lines.append(f"  T{target['level']}: {target['price']:.2f} (+{target['gain_pct']:.1f}%)")
        
        # 盈亏比
        if recommendation.get('risk_reward'):
            lines.append(f"\n盈亏比: {recommendation['risk_reward']:.1f}:1")
        
        # 推荐理由
        if recommendation.get('reasons'):
            lines.append(f"\n推荐理由:")
            for reason in recommendation['reasons']:
                lines.append(f"  ✓ {reason}")
        
        # 警告
        if recommendation.get('warnings'):
            lines.append(f"\n⚠️ 警告:")
            for warning in recommendation['warnings']:
                lines.append(f"  ! {warning}")
        
        lines.append(f"{'='*60}\n")
        
        return '\n'.join(lines)


class TrendReversalStrategy(BaseStrategy):
    """
    趋势反转策略（基于2B结构）
    
    专注于捕捉过度偏离后的反转机会
    风险较高，建议小仓位参与
    """
    
    def __init__(self, config: Dict):
        """初始化反转策略"""
        super().__init__(config)
        
        self.indicator_calculator = TechnicalIndicators()
        self.signal_detector = SignalDetector(config.get('signal_detector', {}))
        
        logger.info(f"初始化趋势反转策略: {self.name}")
    
    def analyze(self, data: pd.DataFrame) -> pd.DataFrame:
        """分析数据"""
        df = self.indicator_calculator.calculate_all_indicators(data)
        return df
    
    def generate_recommendations(self, analyzed_data: pd.DataFrame) -> List[Dict]:
        """生成推荐"""
        # 检测2B结构
        result_2b = self.signal_detector.detect_2b_structure(analyzed_data)
        
        if not result_2b.get('has_2b'):
            return []
        
        latest = analyzed_data.iloc[-1]
        price_col = '收盘' if '收盘' in analyzed_data.columns else 'close'
        
        # 判断看涨还是看跌
        if result_2b['bullish_2b']['found']:
            signal_type = '看涨2B结构'
            bias = latest.get('Bias120', 0)
            
            recommendation = {
                'strategy': '趋势反转-做多',
                'priority': '⭐⭐',
                'signal': signal_type,
                'current_price': latest[price_col],
                'entry': '2B结构确认后',
                'stop_loss': result_2b['bullish_2b']['recent_low'],
                'reasons': [
                    '出现看涨2B结构',
                    f'乖离率{bias:.1f}%，可能过度偏离',
                    '短期反弹机会'
                ],
                'risk_note': '仅为短期反弹，不代表大趋势反转'
            }
            
            return [recommendation]
        
        elif result_2b['bearish_2b']['found']:
            signal_type = '看跌2B结构'
            bias = latest.get('Bias120', 0)
            
            recommendation = {
                'strategy': '趋势反转-做空',
                'priority': '⭐⭐',
                'signal': signal_type,
                'current_price': latest[price_col],
                'entry': '2B结构确认后',
                'stop_loss': result_2b['bearish_2b']['recent_high'],
                'reasons': [
                    '出现看跌2B结构',
                    f'乖离率{bias:.1f}%，可能过度偏离',
                    '短期回调机会'
                ],
                'risk_note': '仅为短期回调，不代表大趋势反转'
            }
            
            return [recommendation]
        
        return []
