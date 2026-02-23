"""
盈利预测和离场时机判断模块

基于价量时空交易系统的理念，为不同策略类型提供：
1. 盈利预测（目标价位、预期收益率、持有周期）
2. 离场时机（明确的出场信号）
3. 风险评估（盈亏比、止损位）
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from loguru import logger


class ProfitPredictor:
    """
    盈利预测器
    
    根据策略类型和技术分析提供：
    - 盈利目标（多个目标位）
    - 离场信号（具体的出场条件）
    - 风险收益比
    - 建议持有周期
    """
    
    def __init__(self, config: Dict = None):
        """
        初始化盈利预测器
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 默认配置
        self.default_targets = {
            '密集成交区突破': {
                'expected_gain': [10, 25, 50],  # 三个目标位的预期收益（%）
                'success_rate': 0.65,  # 成功率
                'holding_period': [5, 20, 60],  # 持有周期（交易日）
                'max_holding_period': 90,  # 最长持有
            },
            '稳定趋势回撤': {
                'expected_gain': [8, 18, 35],
                'success_rate': 0.75,  # 最稳健，成功率高
                'holding_period': [10, 30, 90],
                'max_holding_period': 180,
            },
            '加速行情-持有': {
                'expected_gain': [15, 35, 70],  # 高风险高收益
                'success_rate': 0.45,  # 成功率较低
                'holding_period': [3, 10, 20],
                'max_holding_period': 30,  # 短期行情
            }
        }
        
    def predict_profit(self,
                      strategy_type: str,
                      current_price: float,
                      data: pd.DataFrame,
                      trend_analysis: Dict) -> Dict:
        """
        综合盈利预测
        
        Args:
            strategy_type: 策略类型（密集成交区突破/稳定趋势回撤/加速行情-持有）
            current_price: 当前价格
            data: 历史数据
            trend_analysis: 趋势分析结果
            
        Returns:
            Dict: 盈利预测结果
        """
        # 1. 计算目标价位
        targets = self._calculate_targets(
            strategy_type, current_price, data, trend_analysis
        )
        
        # 2. 计算离场信号
        exit_signals = self._generate_exit_signals(
            strategy_type, data, trend_analysis
        )
        
        # 3. 预测持有周期
        holding_period = self._estimate_holding_period(
            strategy_type, data, trend_analysis
        )
        
        # 4. 风险收益评估
        risk_reward = self._assess_risk_reward(
            strategy_type, current_price, targets, 
            trend_analysis.get('stop_loss', {})
        )
        
        # 5. 成功概率评估
        success_probability = self._estimate_success_rate(
            strategy_type, data, trend_analysis
        )
        
        prediction = {
            'strategy_type': strategy_type,
            'current_price': current_price,
            
            # 盈利目标
            'targets': targets,  # 多个目标位
            'expected_total_gain': targets[-1]['gain_pct'] if targets else 0,
            
            # 离场信号
            'exit_signals': exit_signals,
            
            # 时间预测
            'holding_period': holding_period,
            
            # 风险评估
            'risk_reward': risk_reward,
            'success_probability': success_probability,
            
            # 综合建议
            'recommendation': self._generate_recommendation(
                targets, exit_signals, risk_reward, success_probability
            )
        }
        
        logger.info(
            f"盈利预测完成 - 策略: {strategy_type}, "
            f"预期收益: {prediction['expected_total_gain']:.1f}%, "
            f"成功率: {success_probability:.0%}"
        )
        
        return prediction
    
    def _calculate_targets(self,
                          strategy_type: str,
                          current_price: float,
                          data: pd.DataFrame,
                          trend_analysis: Dict) -> List[Dict]:
        """
        计算多个目标价位
        
        方法：
        1. 基于均线密集区（阻力位）
        2. 基于策略类型的典型收益
        3. 基于ATR的动态目标
        
        Args:
            strategy_type: 策略类型
            current_price: 当前价格
            data: 历史数据
            trend_analysis: 趋势分析
            
        Returns:
            List[Dict]: 目标价位列表
        """
        targets = []
        
        # 获取策略默认收益预期
        default_gains = self.default_targets.get(
            strategy_type, 
            self.default_targets['稳定趋势回撤']
        )['expected_gain']
        
        latest = data.iloc[-1]
        
        # 方法1: 基于均线密集区（技术阻力位）
        ma_targets = trend_analysis.get('targets', [])
        
        # 方法2: 基于ATR的动态目标（波动率调整）
        atr = latest.get('ATR14', current_price * 0.02)
        volatility_multiplier = atr / current_price
        
        # 综合三个目标位
        for i, default_gain in enumerate(default_gains):
            # 基础目标（默认收益）
            base_target_price = current_price * (1 + default_gain / 100)
            
            # 如果有技术位，优先使用技术位
            if i < len(ma_targets):
                technical_price = ma_targets[i]['price']
                # 取技术位和默认目标的平均（结合两种方法）
                target_price = (technical_price + base_target_price) / 2
            else:
                target_price = base_target_price
            
            # 根据波动率调整
            if volatility_multiplier > 0.03:  # 高波动
                target_price *= 1.1  # 目标上调
            elif volatility_multiplier < 0.015:  # 低波动
                target_price *= 0.9  # 目标下调
            
            gain_pct = (target_price - current_price) / current_price * 100
            
            targets.append({
                'level': i + 1,
                'price': target_price,
                'gain_pct': gain_pct,
                'probability': self._target_probability(i, strategy_type),
                'description': self._target_description(i, gain_pct)
            })
        
        return targets
    
    def _target_probability(self, level: int, strategy_type: str) -> float:
        """
        估算各目标位的达成概率
        
        Args:
            level: 目标位级别（0, 1, 2）
            strategy_type: 策略类型
            
        Returns:
            float: 达成概率
        """
        base_success = self.default_targets.get(
            strategy_type,
            self.default_targets['稳定趋势回撤']
        )['success_rate']
        
        # 目标位越高，概率递减
        probabilities = [
            base_success,  # 第一目标
            base_success * 0.65,  # 第二目标
            base_success * 0.35,  # 第三目标
        ]
        
        return probabilities[level] if level < len(probabilities) else 0.1
    
    def _target_description(self, level: int, gain_pct: float) -> str:
        """
        目标位描述
        
        Args:
            level: 目标级别
            gain_pct: 收益百分比
            
        Returns:
            str: 描述文本
        """
        descriptions = [
            f"第一目标 (+{gain_pct:.1f}%) - 短期目标，建议部分止盈",
            f"第二目标 (+{gain_pct:.1f}%) - 中期目标，建议再次减仓",
            f"第三目标 (+{gain_pct:.1f}%) - 理想目标，全部兑现利润"
        ]
        
        return descriptions[level] if level < len(descriptions) else f"目标{level+1}"
    
    def _generate_exit_signals(self,
                              strategy_type: str,
                              data: pd.DataFrame,
                              trend_analysis: Dict) -> Dict:
        """
        生成离场信号（关键！）
        
        根据策略类型，给出明确的出场条件
        
        Args:
            strategy_type: 策略类型
            data: 历史数据
            trend_analysis: 趋势分析
            
        Returns:
            Dict: 离场信号
        """
        latest = data.iloc[-1]
        
        # 通用离场信号（所有策略）
        common_signals = {
            'stop_loss': {
                'trigger': '止损',
                'condition': f"价格跌破 {trend_analysis.get('stop_loss', {}).get('stop_loss', 0):.2f}",
                'priority': '⚠️ 必须执行',
                'action': '立即止损出局'
            }
        }
        
        # 策略特定离场信号
        if strategy_type == '密集成交区突破':
            specific_signals = {
                '假突破': {
                    'trigger': '假突破识别',
                    'condition': '突破后迅速跌回密集区，且跌破MA20',
                    'priority': '⚠️ 立即出局',
                    'action': '假突破，立即止损或反手做空'
                },
                '均线死叉': {
                    'trigger': '均线死叉',
                    'condition': 'MA20下穿MA60（即将死叉）',
                    'priority': '⚠️ 必须离场',
                    'action': '多头排列被破坏，清仓离场'
                },
                '磨蹭不走': {
                    'trigger': '横盘过久',
                    'condition': '突破后5个交易日内未继续上涨',
                    'priority': '⚠️ 主动止损',
                    'action': '突破失败，主动离场'
                },
                '达到目标': {
                    'trigger': '目标位',
                    'condition': '价格达到目标位',
                    'priority': '✅ 分批止盈',
                    'action': '第一目标减仓30%，第二目标减仓40%，第三目标全部清仓'
                }
            }
            
        elif strategy_type == '稳定趋势回撤':
            specific_signals = {
                '均线拐头': {
                    'trigger': '均线拐头向下',
                    'condition': 'MA60或MA120开始拐头向下',
                    'priority': '⚠️ 警惕',
                    'action': '趋势可能改变，准备离场'
                },
                '均线死叉': {
                    'trigger': '均线死叉',
                    'condition': 'MA20下穿MA60',
                    'priority': '⚠️ 必须离场',
                    'action': '多头排列被破坏，清仓离场'
                },
                '抵扣价破位': {
                    'trigger': '抵扣价破位',
                    'condition': '价格跌破MA120抵扣价',
                    'priority': '⚠️ 立即出局',
                    'action': 'MA120方向即将改变，果断离场'
                },
                '破线-拐头-交叉': {
                    'trigger': '三步骤确认',
                    'condition': '跌破关键线 → 均线拐头 → 死叉',
                    'priority': '⚠️ 确定性最高',
                    'action': '趋势反转确认，全部清仓'
                },
                '达到目标': {
                    'trigger': '目标位',
                    'condition': '价格达到目标位',
                    'priority': '✅ 分批止盈',
                    'action': '第一目标减仓20%，第二目标减仓30%，保留50%继续持有'
                }
            }
            
        elif strategy_type == '加速行情-持有':
            specific_signals = {
                '顶部构造': {
                    'trigger': '顶部形态出现',
                    'condition': 'M顶、头肩顶等顶部构造',
                    'priority': '⚠️ 高度警惕',
                    'action': '这是路牌，提醒重视，准备随时离场'
                },
                '关键性波动': {
                    'trigger': '关键性下跌',
                    'condition': '价格跌破重要支撑位，可能改变均线方向',
                    'priority': '⚠️ 准备离场',
                    'action': '观察是否导致MA20拐头向下'
                },
                'MA20拐头': {
                    'trigger': 'MA20拐头向下',
                    'condition': 'MA20明显拐头向下',
                    'priority': '⚠️ 立即离场',
                    'action': '短期趋势改变，减仓50%'
                },
                '均线死叉': {
                    'trigger': 'MA20与MA60即将死叉',
                    'condition': 'MA20下穿MA60（最确定信号）',
                    'priority': '⚠️⚠️⚠️ 必须全部清仓',
                    'action': '加速行情结束，全部离场'
                },
                '极端信号': {
                    'trigger': '顶部极端特征',
                    'condition': '连续巨量、乖离>30%、长上影线',
                    'priority': '⚠️⚠️ 立即减仓',
                    'action': '人性之极=趋势之极，减仓至少70%'
                }
            }
            
        else:
            specific_signals = {}
        
        # 合并信号
        exit_signals = {**common_signals, **specific_signals}
        
        # 当前状态检查（哪些信号已触发）
        current_status = self._check_exit_signals_status(
            data, trend_analysis, exit_signals
        )
        
        return {
            'signals': exit_signals,
            'current_status': current_status,
            'active_warnings': [k for k, v in current_status.items() if v['triggered']]
        }
    
    def _check_exit_signals_status(self,
                                   data: pd.DataFrame,
                                   trend_analysis: Dict,
                                   exit_signals: Dict) -> Dict:
        """
        检查当前哪些离场信号已触发
        
        Args:
            data: 历史数据
            trend_analysis: 趋势分析
            exit_signals: 离场信号定义
            
        Returns:
            Dict: 各信号的触发状态
        """
        latest = data.iloc[-1]
        status = {}
        
        # 检查止损
        if 'stop_loss' in exit_signals:
            stop_loss_price = trend_analysis.get('stop_loss', {}).get('stop_loss', 0)
            price_col = '收盘' if '收盘' in data.columns else 'close'
            current_price = latest[price_col]
            
            status['stop_loss'] = {
                'triggered': current_price < stop_loss_price,
                'urgency': 'critical' if current_price < stop_loss_price else 'normal'
            }
        
        # 检查均线死叉
        if '均线死叉' in exit_signals:
            ma20 = latest.get('MA20', 0)
            ma60 = latest.get('MA60', 0)
            prev_ma20 = data.iloc[-2].get('MA20', 0) if len(data) > 1 else ma20
            prev_ma60 = data.iloc[-2].get('MA60', 0) if len(data) > 1 else ma60
            
            # 检查是否即将死叉或已死叉
            approaching_cross = (prev_ma20 > prev_ma60 and ma20 < ma60 * 1.02)
            dead_cross = ma20 < ma60
            
            status['均线死叉'] = {
                'triggered': approaching_cross or dead_cross,
                'urgency': 'critical' if dead_cross else 'high' if approaching_cross else 'normal'
            }
        
        # 检查顶部构造（如果适用）
        if '顶部构造' in exit_signals:
            top_bottom = trend_analysis.get('top_bottom_structure', {})
            has_top = top_bottom.get('double_top', {}).get('found', False)
            
            status['顶部构造'] = {
                'triggered': has_top,
                'urgency': 'high' if has_top else 'normal'
            }
        
        # 检查极端乖离（如果适用）
        if '极端信号' in exit_signals:
            bias120 = trend_analysis.get('bias120', 0)
            extreme = abs(bias120) > 30
            
            status['极端信号'] = {
                'triggered': extreme,
                'urgency': 'high' if extreme else 'normal'
            }
        
        return status
    
    def _estimate_holding_period(self,
                                strategy_type: str,
                                data: pd.DataFrame,
                                trend_analysis: Dict) -> Dict:
        """
        预测建议持有周期
        
        Args:
            strategy_type: 策略类型
            data: 历史数据
            trend_analysis: 趋势分析
            
        Returns:
            Dict: 持有周期预测
        """
        default_periods = self.default_targets.get(
            strategy_type,
            self.default_targets['稳定趋势回撤']
        )
        
        # 基于趋势强度调整
        trend_strength = trend_analysis.get('trend_strength', 0.5)
        
        # 趋势越强，可以持有越久
        multiplier = 0.8 + (trend_strength * 0.4)  # 0.8-1.2
        
        return {
            'min_days': int(default_periods['holding_period'][0] * multiplier),
            'target_days': int(default_periods['holding_period'][1] * multiplier),
            'max_days': int(default_periods['max_holding_period'] * multiplier),
            'description': self._holding_period_description(strategy_type),
            'note': '实际持有时间以离场信号为准，而非固定天数'
        }
    
    def _holding_period_description(self, strategy_type: str) -> str:
        """
        持有周期描述
        
        Args:
            strategy_type: 策略类型
            
        Returns:
            str: 描述
        """
        descriptions = {
            '密集成交区突破': '突破后通常会有5-20天的快速上涨，随后进入整理',
            '稳定趋势回撤': '稳定趋势可持续数月，建议持有到均线死叉',
            '加速行情-持有': '加速行情通常3-10天见顶，不要贪心'
        }
        
        return descriptions.get(strategy_type, '根据市场情况灵活调整')
    
    def _assess_risk_reward(self,
                           strategy_type: str,
                           current_price: float,
                           targets: List[Dict],
                           stop_loss_info: Dict) -> Dict:
        """
        评估风险收益比
        
        Args:
            strategy_type: 策略类型
            current_price: 当前价格
            targets: 目标价位列表
            stop_loss_info: 止损信息
            
        Returns:
            Dict: 风险收益评估
        """
        if not targets or not stop_loss_info:
            return {
                'ratio': 0,
                'evaluation': '数据不足'
            }
        
        # 潜在亏损
        stop_loss_pct = stop_loss_info.get('stop_loss_pct', 5.0)
        
        # 对应每个目标位的盈亏比
        ratios = []
        for target in targets:
            gain_pct = target['gain_pct']
            ratio = gain_pct / stop_loss_pct if stop_loss_pct > 0 else 0
            ratios.append({
                'target_level': target['level'],
                'gain': gain_pct,
                'loss': stop_loss_pct,
                'ratio': ratio,
                'probability': target['probability']
            })
        
        # 期望收益 = Σ(收益 × 概率)
        expected_value = sum(
            r['gain'] * r['probability'] / 100 for r in ratios
        )
        expected_loss = stop_loss_pct * (1 - ratios[0]['probability'])
        
        overall_ratio = ratios[0]['ratio'] if ratios else 0
        
        # 评估
        if overall_ratio >= 3:
            evaluation = "优秀 - 风险收益比理想"
        elif overall_ratio >= 2:
            evaluation = "良好 - 风险收益比合理"
        elif overall_ratio >= 1.5:
            evaluation = "一般 - 勉强可以接受"
        else:
            evaluation = "较差 - 不建议交易"
        
        return {
            'overall_ratio': overall_ratio,
            'ratios_by_target': ratios,
            'expected_value': expected_value,
            'expected_loss': expected_loss,
            'evaluation': evaluation
        }
    
    def _estimate_success_rate(self,
                              strategy_type: str,
                              data: pd.DataFrame,
                              trend_analysis: Dict) -> float:
        """
        估算成功概率
        
        基于：
        1. 策略类型的历史成功率
        2. 当前技术形态的质量
        3. 市场环境
        
        Args:
            strategy_type: 策略类型
            data: 历史数据
            trend_analysis: 趋势分析
            
        Returns:
            float: 成功概率（0-1）
        """
        # 基础成功率
        base_rate = self.default_targets.get(
            strategy_type,
            self.default_targets['稳定趋势回撤']
        )['success_rate']
        
        # 根据技术形态质量调整
        adjustments = 0
        
        # 1. 均线密集度（越密集，突破后涨幅越大）
        ma_density = trend_analysis.get('ma_density', 0)
        if ma_density < 0.02:
            adjustments += 0.1  # 非常密集，加分
        
        # 2. 多头排列完美度
        if trend_analysis.get('ma_alignment') == 'bull':
            adjustments += 0.05
        
        # 3. 趋势强度
        trend_strength = trend_analysis.get('trend_strength', 0.5)
        if trend_strength > 0.7:
            adjustments += 0.08
        elif trend_strength < 0.3:
            adjustments -= 0.1
        
        # 4. 成交量配合
        latest = data.iloc[-1]
        volume_surge = latest.get('Volume_Surge', False)
        if volume_surge:
            adjustments += 0.05
        
        # 5. 首次回撤（如果适用）
        if strategy_type == '稳定趋势回撤':
            # 假设有首次回撤标志
            # 这里简化处理
            pass
        
        final_rate = max(0.1, min(0.95, base_rate + adjustments))
        
        return final_rate
    
    def _generate_recommendation(self,
                                targets: List[Dict],
                                exit_signals: Dict,
                                risk_reward: Dict,
                                success_probability: float) -> str:
        """
        生成综合操作建议
        
        Args:
            targets: 目标列表
            exit_signals: 离场信号
            risk_reward: 风险收益
            success_probability: 成功概率
            
        Returns:
            str: 操作建议
        """
        recommendations = []
        
        # 1. 根据盈亏比判断
        if risk_reward['overall_ratio'] >= 2:
            recommendations.append("✅ 盈亏比理想，可以参与")
        else:
            recommendations.append("⚠️ 盈亏比一般，谨慎参与")
        
        # 2. 根据成功率判断
        if success_probability >= 0.7:
            recommendations.append(f"✅ 成功率较高({success_probability:.0%})，建议标准仓位")
        elif success_probability >= 0.5:
            recommendations.append(f"⚠️ 成功率中等({success_probability:.0%})，建议半仓操作")
        else:
            recommendations.append(f"⚠️ 成功率较低({success_probability:.0%})，建议轻仓或观望")
        
        # 3. 离场纪律
        active_warnings = exit_signals.get('active_warnings', [])
        if active_warnings:
            recommendations.append(f"⚠️⚠️ 当前已触发离场信号：{', '.join(active_warnings)}")
        else:
            recommendations.append("✅ 当前无离场信号，可以持有")
        
        # 4. 分批止盈建议
        if len(targets) >= 2:
            recommendations.append(
                f"💡 建议分批止盈：第一目标({targets[0]['gain_pct']:.1f}%)减仓30%，"
                f"第二目标({targets[1]['gain_pct']:.1f}%)减仓50%"
            )
        
        return "\n".join(recommendations)


def add_profit_prediction(recommendation: Dict,
                         data: pd.DataFrame,
                         trend_analysis: Dict,
                         config: Dict = None) -> Dict:
    """
    给推荐添加盈利预测（便捷函数）
    
    Args:
        recommendation: 原推荐
        data: 历史数据
        trend_analysis: 趋势分析
        config: 配置
        
    Returns:
        Dict: 增强后的推荐（包含盈利预测）
    """
    predictor = ProfitPredictor(config)
    
    strategy_type = recommendation.get('strategy', '未知')
    current_price = recommendation.get('current_price', 0)
    
    # 生成盈利预测
    prediction = predictor.predict_profit(
        strategy_type, current_price, data, trend_analysis
    )
    
    # 合并到推荐中
    enhanced = recommendation.copy()
    enhanced['profit_prediction'] = prediction
    
    return enhanced
