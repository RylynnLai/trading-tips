"""
低波债券轮动策略

基于低波动率异象和动量轮动的债券/债基投资策略
"""

from typing import Dict, List, Optional
import pandas as pd
import numpy as np
from loguru import logger
from datetime import datetime, timedelta

from .base_strategy import BaseStrategy


class LowVolatilityRotation(BaseStrategy):
    """
    低波债券轮动策略
    
    策略逻辑：
    1. 计算候选标的的60日年化波动率
    2. 筛选波动率最低的30%标的
    3. 在低波池中筛选20日收益率>0的标的
    4. 按夏普比率（收益/波动率）排序，选择Top N
    5. 月度调仓，单只持仓限制，设置止损
    
    适用标的：
    - 债券ETF
    - 债券基金
    - 可转债基金
    """
    
    def __init__(self, config: Dict):
        """
        初始化低波轮动策略
        
        Args:
            config: 策略配置
        """
        super().__init__(config)
        
        # 策略参数
        self.volatility_window = config.get('volatility_window', 60)  # 波动率计算窗口
        self.momentum_window = config.get('momentum_window', 20)  # 动量计算窗口
        self.low_vol_percentile = config.get('low_vol_percentile', 30)  # 低波百分位
        self.top_n = config.get('top_n', 10)  # 推荐数量
        self.min_liquidity = config.get('min_liquidity', 10000000)  # 最小日均成交额
        self.max_position_pct = config.get('max_position_pct', 15)  # 单只最大持仓比例
        self.stop_loss_pct = config.get('stop_loss_pct', 3)  # 止损比例
        self.min_momentum = config.get('min_momentum', 0)  # 最小动量要求
        
        logger.info(f"低波轮动策略参数: 波动率窗口={self.volatility_window}天, "
                   f"动量窗口={self.momentum_window}天, "
                   f"低波百分位={self.low_vol_percentile}%, "
                   f"推荐数量={self.top_n}")
    
    def calculate_volatility(self, prices: pd.Series) -> float:
        """
        计算年化波动率
        
        Args:
            prices: 价格序列
            
        Returns:
            float: 年化波动率（百分比）
        """
        if len(prices) < 2:
            return np.nan
        
        # 计算日收益率
        returns = prices.pct_change().dropna()
        
        if len(returns) == 0:
            return np.nan
        
        # 年化波动率 = 日波动率 * sqrt(252)
        volatility = returns.std() * np.sqrt(252) * 100
        
        return volatility
    
    def calculate_momentum(self, prices: pd.Series, window: int) -> float:
        """
        计算动量（累计收益率）
        
        Args:
            prices: 价格序列
            window: 计算窗口
            
        Returns:
            float: 累计收益率（百分比）
        """
        if len(prices) < window:
            return np.nan
        
        # 获取窗口期的首尾价格
        start_price = prices.iloc[-window]
        end_price = prices.iloc[-1]
        
        if start_price <= 0:
            return np.nan
        
        # 计算累计收益率
        momentum = ((end_price - start_price) / start_price) * 100
        
        return momentum
    
    def calculate_sharpe_ratio(self, returns: pd.Series, risk_free_rate: float = 0.02) -> float:
        """
        计算夏普比率
        
        Args:
            returns: 收益率序列
            risk_free_rate: 无风险利率（年化）
            
        Returns:
            float: 夏普比率
        """
        if len(returns) == 0 or returns.std() == 0:
            return np.nan
        
        # 年化收益率
        annual_return = returns.mean() * 252
        
        # 年化波动率
        annual_volatility = returns.std() * np.sqrt(252)
        
        # 夏普比率
        sharpe = (annual_return - risk_free_rate) / annual_volatility
        
        return sharpe
    
    def calculate_max_drawdown(self, prices: pd.Series) -> float:
        """
        计算最大回撤
        
        Args:
            prices: 价格序列
            
        Returns:
            float: 最大回撤（百分比）
        """
        if len(prices) == 0:
            return np.nan
        
        # 计算累计最大值
        cummax = prices.expanding().max()
        
        # 计算回撤
        drawdown = (prices - cummax) / cummax * 100
        
        # 最大回撤
        max_dd = drawdown.min()
        
        return abs(max_dd)
    
    def analyze_single_security(self, 
                                code: str,
                                name: str,
                                price_data: pd.DataFrame) -> Optional[Dict]:
        """
        分析单个标的
        
        Args:
            code: 证券代码
            name: 证券名称
            price_data: 价格数据，需包含 date, close, volume, amount 列
            
        Returns:
            Dict: 分析结果，如果不符合条件则返回 None
        """
        try:
            if price_data.empty or len(price_data) < self.volatility_window:
                logger.debug(f"{code} 数据不足")
                return None
            
            # 确保数据按日期排序
            price_data = price_data.sort_values('date').reset_index(drop=True)
            
            # 提取收盘价序列
            prices = price_data['close']
            
            # 1. 计算波动率
            volatility = self.calculate_volatility(prices.tail(self.volatility_window))
            
            if np.isnan(volatility):
                return None
            
            # 2. 计算动量
            momentum = self.calculate_momentum(prices, self.momentum_window)
            
            if np.isnan(momentum):
                return None
            
            # 3. 计算夏普比率
            returns = prices.pct_change().dropna()
            sharpe = self.calculate_sharpe_ratio(returns.tail(self.volatility_window))
            
            # 4. 计算最大回撤
            max_dd = self.calculate_max_drawdown(prices.tail(self.volatility_window))
            
            # 5. 计算流动性指标
            if 'amount' in price_data.columns:
                avg_amount = price_data['amount'].tail(20).mean()
            else:
                avg_amount = 0
            
            # 6. 当前价格和涨跌幅
            current_price = prices.iloc[-1]
            price_change = self.calculate_momentum(prices, 1)  # 1日涨跌幅
            
            # 7. 计算综合得分（收益风险比）
            if volatility > 0:
                score = momentum / volatility  # 简化的夏普比率
            else:
                score = 0
            
            result = {
                'code': code,
                'name': name,
                'current_price': current_price,
                'volatility': volatility,  # 年化波动率
                'momentum': momentum,  # 动量得分
                'sharpe_ratio': sharpe,  # 夏普比率
                'max_drawdown': max_dd,  # 最大回撤
                'avg_amount': avg_amount,  # 平均成交额
                'price_change': price_change,  # 最新涨跌幅
                'score': score,  # 综合得分
            }
            
            return result
            
        except Exception as e:
            logger.error(f"分析 {code} 时出错: {e}")
            return None
    
    def analyze(self, candidates: List[Dict]) -> pd.DataFrame:
        """
        分析候选标的池
        
        Args:
            candidates: 候选标的列表，每个包含 code, name, price_data
            
        Returns:
            DataFrame: 分析结果
        """
        logger.info(f"开始分析 {len(candidates)} 个候选标的...")
        
        results = []
        
        for candidate in candidates:
            code = candidate.get('code')
            name = candidate.get('name', code)
            price_data = candidate.get('price_data')
            
            if price_data is None or price_data.empty:
                logger.debug(f"跳过 {code}：无价格数据")
                continue
            
            result = self.analyze_single_security(code, name, price_data)
            
            if result is not None:
                results.append(result)
        
        if not results:
            logger.warning("没有符合条件的标的")
            return pd.DataFrame()
        
        # 转换为DataFrame
        df = pd.DataFrame(results)
        
        logger.info(f"完成分析，共 {len(df)} 个标的符合基本条件")
        
        return df
    
    def filter_by_criteria(self, analyzed_data: pd.DataFrame) -> pd.DataFrame:
        """
        根据策略标准筛选标的
        
        Args:
            analyzed_data: 分析后的数据
            
        Returns:
            DataFrame: 筛选后的数据
        """
        if analyzed_data.empty:
            return analyzed_data
        
        df = analyzed_data.copy()
        initial_count = len(df)
        
        # 1. 筛选波动率最低的N%
        vol_threshold = df['volatility'].quantile(self.low_vol_percentile / 100)
        df = df[df['volatility'] <= vol_threshold]
        logger.info(f"波动率筛选: {len(df)}/{initial_count} "
                   f"(阈值: {vol_threshold:.2f}%)")
        
        if df.empty:
            return df
        
        # 2. 筛选动量为正的标的
        df = df[df['momentum'] > self.min_momentum]
        logger.info(f"动量筛选: {len(df)} (动量>{self.min_momentum}%)")
        
        if df.empty:
            return df
        
        # 3. 流动性筛选
        if self.min_liquidity > 0:
            df = df[df['avg_amount'] >= self.min_liquidity]
            logger.info(f"流动性筛选: {len(df)} "
                       f"(日均成交额>{self.min_liquidity:,.0f})")
        
        return df
    
    def generate_recommendations(self, analyzed_data: pd.DataFrame) -> List[Dict]:
        """
        生成推荐列表
        
        Args:
            analyzed_data: 分析后的数据
            
        Returns:
            List[Dict]: 推荐列表
        """
        if analyzed_data.empty:
            logger.warning("没有可推荐的标的")
            return []
        
        # 筛选符合条件的标的
        filtered = self.filter_by_criteria(analyzed_data)
        
        if filtered.empty:
            logger.warning("筛选后没有符合条件的标的")
            return []
        
        # 按综合得分排序
        filtered = filtered.sort_values('score', ascending=False)
        
        # 选择Top N
        top_n = filtered.head(self.top_n)
        
        # 生成推荐列表
        recommendations = []
        
        for idx, row in top_n.iterrows():
            # 生成推荐理由
            reasons = []
            reasons.append(f"波动率: {row['volatility']:.2f}% (低波)")
            reasons.append(f"动量: {row['momentum']:.2f}% (正向)")
            
            if not np.isnan(row['sharpe_ratio']):
                reasons.append(f"夏普比率: {row['sharpe_ratio']:.2f}")
            
            reasons.append(f"最大回撤: {row['max_drawdown']:.2f}%")
            reasons.append(f"综合得分: {row['score']:.2f}")
            
            # 建议持仓比例
            position_pct = min(100 / self.top_n, self.max_position_pct)
            
            recommendation = {
                'rank': len(recommendations) + 1,
                'code': row['code'],
                'name': row['name'],
                'current_price': row['current_price'],
                'score': row['score'],
                'volatility': row['volatility'],
                'momentum': row['momentum'],
                'sharpe_ratio': row['sharpe_ratio'],
                'max_drawdown': row['max_drawdown'],
                'suggested_position': f"{position_pct:.1f}%",
                'reasons': reasons,
                'action': 'BUY',
            }
            
            recommendations.append(recommendation)
        
        logger.info(f"生成 {len(recommendations)} 个推荐")
        
        return recommendations
    
    def get_portfolio_stats(self, recommendations: List[Dict]) -> Dict:
        """
        获取组合统计信息
        
        Args:
            recommendations: 推荐列表
            
        Returns:
            Dict: 组合统计
        """
        if not recommendations:
            return {}
        
        # 计算组合平均指标
        volatilities = [r['volatility'] for r in recommendations]
        momentums = [r['momentum'] for r in recommendations]
        sharpes = [r['sharpe_ratio'] for r in recommendations if not np.isnan(r['sharpe_ratio'])]
        drawdowns = [r['max_drawdown'] for r in recommendations]
        
        stats = {
            'portfolio_count': len(recommendations),
            'avg_volatility': np.mean(volatilities),
            'avg_momentum': np.mean(momentums),
            'avg_sharpe_ratio': np.mean(sharpes) if sharpes else np.nan,
            'avg_max_drawdown': np.mean(drawdowns),
            'expected_annual_return': f"{np.mean(momentums) * 12 / self.momentum_window:.2f}%",
        }
        
        return stats
