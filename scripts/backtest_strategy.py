"""
策略回测脚本

执行两个回测场景：
1. 随机时间点回测：多次随机选择时间点，买入所有 70 分以上的股票，统计盈利概率
2. 固定策略回测：重复12次买入所有 70 分以上的股票，统计策略效果
"""

import sys
import random
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from loguru import logger
from typing import Dict, List, Tuple, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.data_source import DataFetcher, AkShareProvider
from src.analysis.trend_strategy import TrendFollowingStrategy


class StrategyBacktester:
    """
    策略回测器
    
    执行买入70分以上股票的策略回测
    """
    
    def __init__(self):
        """初始化回测器"""
        self.data_dir = Path('~/.qlib/qlib_data/cn_data').expanduser()
        self.score_threshold = 70  # 评分阈值
        self.max_hold_days = 30  # 最大持有天数
        self.commission = 0.0003  # 佣金率
        self.stamp_duty = 0.001  # 印花税（卖出时）
        
        # 初始化策略分析器
        config = {
            'min_score': 60,
            'ma_periods': [20, 60, 120]
        }
        self.strategy = TrendFollowingStrategy(config)
        
        logger.info("策略回测器初始化完成")
    
    def load_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> Optional[pd.DataFrame]:
        """
        加载股票数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame: 股票数据
        """
        try:
            # 从 CSV 文件加载数据
            csv_file = self.data_dir / f"{symbol}.csv"
            if not csv_file.exists():
                return None
            
            df = pd.read_csv(csv_file)
            
            # 统一列名
            column_mapping = {
                'date': '日期',
                'open': '开盘',
                'high': '最高',
                'low': '最低',
                'close': '收盘',
                'volume': '成交量'
            }
            
            for old_col, new_col in column_mapping.items():
                if old_col in df.columns and new_col not in df.columns:
                    df[new_col] = df[old_col]
            
            # 确保有日期索引
            if '日期' in df.columns:
                df['日期'] = pd.to_datetime(df['日期'])
                df = df.set_index('日期')
            elif 'date' in df.columns:
                df['date'] = pd.to_datetime(df['date'])
                df = df.set_index('date')
            
            # 按日期排序
            df = df.sort_index()
            
            # 筛选日期范围
            if start_date:
                df = df[df.index >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df.index <= pd.to_datetime(end_date)]
            
            return df
            
        except Exception as e:
            logger.warning(f"加载股票数据失败 {symbol}: {e}")
            return None
    
    def get_available_stocks(self) -> List[str]:
        """
        获取可用的股票列表
        
        Returns:
            List[str]: 股票代码列表
        """
        stocks = []
        
        if not self.data_dir.exists():
            logger.error(f"数据目录不存在: {self.data_dir}")
            return stocks
        
        # 读取所有 CSV 文件
        csv_files = list(self.data_dir.glob("*.csv"))
        
        for csv_file in csv_files:
            symbol = csv_file.stem
            # 只处理6位数字的股票代码
            if len(symbol) == 6 and symbol.isdigit():
                stocks.append(symbol)
        
        logger.info(f"找到 {len(stocks)} 只股票")
        return stocks
    
    def analyze_stock(self, symbol: str, date: str) -> Optional[Dict]:
        """
        分析某只股票在指定日期的评分
        
        Args:
            symbol: 股票代码
            date: 分析日期
            
        Returns:
            Dict: 分析结果，包含评分等信息
        """
        # 加载该日期之前的数据（需要足够的历史数据）
        end_date = pd.to_datetime(date)
        start_date = end_date - timedelta(days=500)  # 加载500天历史数据
        
        df = self.load_stock_data(
            symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if df is None or len(df) < 252:  # 至少需要1年数据
            return None
        
        try:
            # 执行技术分析
            analyzed_data = self.strategy.analyze(df)
            
            # 生成推荐
            recommendations = self.strategy.generate_recommendations(analyzed_data)
            
            if not recommendations:
                return None
            
            rec = recommendations[0]
            
            # 获取当前价格和相关信息
            latest = analyzed_data.iloc[-1]
            price_col = '收盘' if '收盘' in analyzed_data.columns else 'close'
            
            return {
                'symbol': symbol,
                'date': end_date,
                'score': rec.get('score', 0),
                'price': latest[price_col],
                'strategy': rec.get('strategy', ''),
                'stop_loss': rec.get('stop_loss', latest[price_col] * 0.95),
                'stop_loss_pct': rec.get('stop_loss_pct', 5.0),
                'targets': rec.get('targets', []),
                'profit_prediction': rec.get('profit_prediction', {})
            }
            
        except Exception as e:
            logger.debug(f"分析股票失败 {symbol}: {e}")
            return None
    
    def simulate_trade(self, symbol: str, entry_date: str, entry_price: float, 
                      stop_loss: float, targets: List[Dict]) -> Dict:
        """
        模拟交易过程
        
        Args:
            symbol: 股票代码
            entry_date: 买入日期
            entry_price: 买入价格
            stop_loss: 止损价
            targets: 目标价位列表
            
        Returns:
            Dict: 交易结果
        """
        # 加载买入后的数据
        start_date = pd.to_datetime(entry_date)
        end_date = start_date + timedelta(days=self.max_hold_days + 10)
        
        df = self.load_stock_data(
            symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d')
        )
        
        if df is None or len(df) < 2:
            return {
                'symbol': symbol,
                'result': 'no_data',
                'profit_pct': 0,
                'hold_days': 0,
                'profit_within_30_days': False
            }
        
        # 跳过第一天（买入日）
        df = df.iloc[1:]
        
        # 提取第一目标价（如果有）
        first_target = None
        if targets and len(targets) > 0:
            first_target = targets[0].get('price', None)
        
        # 记录是否在30天内盈利过
        profit_within_30_days = False
        commission_pct = self._calculate_total_commission_pct()
        
        # 模拟每一天
        for i, (date, row) in enumerate(df.iterrows()):
            high_col = '最高' if '最高' in df.columns else 'high'
            low_col = '最低' if '最低' in df.columns else 'low'
            close_col = '收盘' if '收盘' in df.columns else 'close'
            
            high = row[high_col]
            low = row[low_col]
            close = row[close_col]
            
            hold_days = i + 1
            
            # 检查当天是否盈利（扣除手续费）
            if hold_days <= 30:
                potential_profit_pct = (high - entry_price) / entry_price * 100
                if potential_profit_pct > commission_pct:
                    profit_within_30_days = True
            
            # 1. 检查止损
            if low <= stop_loss:
                exit_price = min(stop_loss, close)  # 可能滑点
                profit_pct = (exit_price - entry_price) / entry_price * 100
                profit_pct -= self._calculate_total_commission_pct()  # 扣除手续费
                
                return {
                    'symbol': symbol,
                    'result': 'stop_loss',
                    'exit_date': date,
                    'exit_price': exit_price,
                    'profit_pct': profit_pct,
                    'hold_days': hold_days,
                    'profit_within_30_days': profit_within_30_days
                }
            
            # 2. 检查第一目标位
            if first_target and high >= first_target:
                exit_price = first_target
                profit_pct = (exit_price - entry_price) / entry_price * 100
                profit_pct -= self._calculate_total_commission_pct()
                
                return {
                    'symbol': symbol,
                    'result': 'target_reached',
                    'exit_date': date,
                    'exit_price': exit_price,
                    'profit_pct': profit_pct,
                    'hold_days': hold_days,
                    'profit_within_30_days': profit_within_30_days or (profit_pct > 0)
                }
            
            # 3. 检查最大持有天数
            if hold_days >= self.max_hold_days:
                exit_price = close
                profit_pct = (exit_price - entry_price) / entry_price * 100
                profit_pct -= self._calculate_total_commission_pct()
                
                return {
                    'symbol': symbol,
                    'result': 'max_hold_days',
                    'exit_date': date,
                    'exit_price': exit_price,
                    'profit_pct': profit_pct,
                    'hold_days': hold_days,
                    'profit_within_30_days': profit_within_30_days
                }
        
        # 如果数据不足（后续数据缺失），按最后价格卖出
        last_row = df.iloc[-1]
        close_col = '收盘' if '收盘' in df.columns else 'close'
        exit_price = last_row[close_col]
        profit_pct = (exit_price - entry_price) / entry_price * 100
        profit_pct -= self._calculate_total_commission_pct()
        
        return {
            'symbol': symbol,
            'result': 'data_insufficient',
            'exit_date': df.index[-1],
            'exit_price': exit_price,
            'profit_pct': profit_pct,
            'hold_days': len(df),
            'profit_within_30_days': profit_within_30_days
        }
    
    def _calculate_total_commission_pct(self) -> float:
        """
        计算总手续费百分比（买入+卖出）
        
        Returns:
            float: 总手续费百分比
        """
        # 买入佣金 + 卖出佣金 + 卖出印花税
        return (self.commission * 2 + self.stamp_duty) * 100
    
    def backtest_random_dates(self, num_iterations: int = 20) -> Dict:
        """
        场景1：随机时间点回测
        
        随机选择多个时间点，每次买入所有70分以上的股票，统计盈利概率
        
        Args:
            num_iterations: 回测次数
            
        Returns:
            Dict: 回测结果统计
        """
        logger.info(f"开始场景1回测：随机时间点回测，共{num_iterations}次")
        
        # 获取可用股票
        all_stocks = self.get_available_stocks()
        
        if not all_stocks:
            logger.error("没有可用的股票数据")
            return {}
        
        # 确定可选的时间范围（2023-01-01 到 2024-12-31）
        start_range = pd.to_datetime('2023-01-01')
        end_range = pd.to_datetime('2024-12-31')
        
        all_iterations = []
        
        for iteration in range(num_iterations):
            logger.info(f"执行第 {iteration + 1}/{num_iterations} 次随机回测")
            
            # 随机选择一个日期
            days_diff = (end_range - start_range).days
            random_days = random.randint(0, days_diff)
            random_date = start_range + timedelta(days=random_days)
            random_date_str = random_date.strftime('%Y-%m-%d')
            
            logger.info(f"  随机日期: {random_date_str}")
            
            # 分析所有股票，筛选70分以上的
            qualified_stocks = []
            
            sample_size = min(200, len(all_stocks))  # 限制样本大小，加快速度
            stock_sample = random.sample(all_stocks, sample_size)
            
            for symbol in stock_sample:
                analysis = self.analyze_stock(symbol, random_date_str)
                if analysis and analysis['score'] >= self.score_threshold:
                    qualified_stocks.append(analysis)
            
            logger.info(f"  找到 {len(qualified_stocks)} 只符合条件的股票（评分≥70）")
            
            if not qualified_stocks:
                logger.warning(f"  第 {iteration + 1} 次回测: 没有找到符合条件的股票")
                continue
            
            # 模拟交易每只股票
            trades = []
            for stock_info in qualified_stocks:
                trade_result = self.simulate_trade(
                    stock_info['symbol'],
                    random_date_str,
                    stock_info['price'],
                    stock_info['stop_loss'],
                    stock_info['targets']
                )
                trades.append(trade_result)
            
            # 统计本次迭代的结果
            iteration_result = self._calculate_iteration_stats(trades)
            iteration_result['date'] = random_date_str
            iteration_result['num_stocks'] = len(qualified_stocks)
            
            all_iterations.append(iteration_result)
            
            logger.info(f"  第 {iteration + 1} 次回测完成: "
                       f"盈利率={iteration_result['win_rate']:.1f}%, "
                       f"平均收益={iteration_result['avg_profit_pct']:.2f}%")
        
        # 汇总所有迭代的统计
        final_stats = self._aggregate_iterations(all_iterations)
        
        logger.info("=" * 60)
        logger.info("场景1回测完成")
        logger.info(f"总体盈利概率: {final_stats['overall_win_rate']:.1f}%")
        logger.info(f"平均收益: {final_stats['overall_avg_profit']:.2f}%")
        logger.info("=" * 60)
        
        return final_stats
    
    def backtest_fixed_strategy(self, num_iterations: int = 12) -> Dict:
        """
        场景2：固定策略回测
        
        重复12次买入所有70分以上的股票，统计策略效果
        使用不同的随机日期，但策略相同
        
        Args:
            num_iterations: 回测次数（默认12次）
            
        Returns:
            Dict: 回测结果统计
        """
        logger.info(f"开始场景2回测：固定策略回测，共{num_iterations}次")
        
        # 这个场景和场景1类似，但会记录更详细的统计信息
        return self.backtest_random_dates(num_iterations)
    
    def _calculate_iteration_stats(self, trades: List[Dict]) -> Dict:
        """
        计算单次迭代的统计数据
        
        Args:
            trades: 交易列表
            
        Returns:
            Dict: 统计结果
        """
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'avg_profit_pct': 0,
                'max_profit_pct': 0,
                'max_loss_pct': 0,
                'profit_within_30_days_rate': 0
            }
        
        total_trades = len(trades)
        winning_trades = [t for t in trades if t['profit_pct'] > 0]
        losing_trades = [t for t in trades if t['profit_pct'] <= 0]
        
        win_rate = len(winning_trades) / total_trades * 100 if total_trades > 0 else 0
        
        # 统计30天内盈利的比例
        profit_within_30_days_count = sum(1 for t in trades if t.get('profit_within_30_days', False))
        profit_within_30_days_rate = profit_within_30_days_count / total_trades * 100 if total_trades > 0 else 0
        
        profits = [t['profit_pct'] for t in trades]
        avg_profit_pct = np.mean(profits) if profits else 0
        max_profit_pct = max(profits) if profits else 0
        max_loss_pct = min(profits) if profits else 0
        
        # 按退出原因分类
        exit_reasons = {}
        for trade in trades:
            reason = trade['result']
            exit_reasons[reason] = exit_reasons.get(reason, 0) + 1
        
        return {
            'total_trades': total_trades,
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_profit_pct': avg_profit_pct,
            'avg_win_pct': np.mean([t['profit_pct'] for t in winning_trades]) if winning_trades else 0,
            'avg_loss_pct': np.mean([t['profit_pct'] for t in losing_trades]) if losing_trades else 0,
            'max_profit_pct': max_profit_pct,
            'max_loss_pct': max_loss_pct,
            'exit_reasons': exit_reasons,
            'profit_within_30_days_rate': profit_within_30_days_rate,
            'profit_within_30_days_count': profit_within_30_days_count
        }
    
    def _aggregate_iterations(self, iterations: List[Dict]) -> Dict:
        """
        汇总多次迭代的结果
        
        Args:
            iterations: 迭代结果列表
            
        Returns:
            Dict: 汇总统计
        """
        if not iterations:
            return {}
        
        total_trades = sum(it['total_trades'] for it in iterations)
        total_winning = sum(it['winning_trades'] for it in iterations)
        total_profit_within_30 = sum(it.get('profit_within_30_days_count', 0) for it in iterations)
        
        overall_win_rate = total_winning / total_trades * 100 if total_trades > 0 else 0
        overall_profit_within_30_rate = total_profit_within_30 / total_trades * 100 if total_trades > 0 else 0
        
        # 所有收益率的平均
        all_avg_profits = [it['avg_profit_pct'] for it in iterations if it['total_trades'] > 0]
        overall_avg_profit = np.mean(all_avg_profits) if all_avg_profits else 0
        
        # 最好和最差的单次回测
        best_iteration = max(iterations, key=lambda x: x['avg_profit_pct'])
        worst_iteration = min(iterations, key=lambda x: x['avg_profit_pct'])
        
        return {
            'num_iterations': len(iterations),
            'total_trades': total_trades,
            'overall_win_rate': overall_win_rate,
            'overall_avg_profit': overall_avg_profit,
            'overall_profit_within_30_rate': overall_profit_within_30_rate,
            'best_iteration': best_iteration,
            'worst_iteration': worst_iteration,
            'all_iterations': iterations
        }
    
    def print_results(self, results: Dict, scenario_name: str):
        """
        打印回测结果
        
        Args:
            results: 回测结果
            scenario_name: 场景名称
        """
        print("\n" + "=" * 80)
        print(f"  {scenario_name} - 回测结果")
        print("=" * 80)
        
        if not results or 'num_iterations' not in results:
            print("  没有有效的回测结果")
            return
        
        print(f"\n【总体统计】")
        print(f"  回测次数: {results['num_iterations']}")
        print(f"  总交易数: {results['total_trades']}")
        print(f"  整体盈利概率: {results['overall_win_rate']:.2f}%")
        print(f"  平均收益率: {results['overall_avg_profit']:.2f}%")
        print(f"  ⭐ 一个月内盈利概率: {results.get('overall_profit_within_30_rate', 0):.2f}%")
        
        print(f"\n【最佳回测】")
        best = results['best_iteration']
        print(f"  日期: {best.get('date', 'N/A')}")
        print(f"  股票数: {best.get('num_stocks', 0)}")
        print(f"  盈利率: {best['win_rate']:.2f}%")
        print(f"  平均收益: {best['avg_profit_pct']:.2f}%")
        
        print(f"\n【最差回测】")
        worst = results['worst_iteration']
        print(f"  日期: {worst.get('date', 'N/A')}")
        print(f"  股票数: {worst.get('num_stocks', 0)}")
        print(f"  盈利率: {worst['win_rate']:.2f}%")
        print(f"  平均收益: {worst['avg_profit_pct']:.2f}%")
        
        print(f"\n【详细数据】")
        for i, iteration in enumerate(results['all_iterations'][:5], 1):  # 只显示前5次
            print(f"  第{i}次: 日期={iteration.get('date', 'N/A')}, "
                  f"股票数={iteration.get('num_stocks', 0)}, "
                  f"盈利率={iteration['win_rate']:.1f}%, "
                  f"平均收益={iteration['avg_profit_pct']:.2f}%")
        
        if len(results['all_iterations']) > 5:
            print(f"  ... (还有 {len(results['all_iterations']) - 5} 次)")
        
        print("=" * 80)


def main():
    """主函数"""
    # 设置日志级别为WARNING以减少输出
    logger.remove()
    logger.add(sys.stdout, level="WARNING")
    
    print("启动策略回测程序\n")
    
    backtester = StrategyBacktester()
    
    # 场景1: 随机时间点回测（20次）
    print("=" * 80)
    print("场景1: 随机时间点回测（20次）")
    print("=" * 80)
    results_1 = backtester.backtest_random_dates(num_iterations=20)
    backtester.print_results(results_1, "场景1")
    
    # 场景2: 固定策略回测（12次）
    print("\n" + "=" * 80)
    print("场景2: 固定策略回测（12次）")
    print("=" * 80)
    results_2 = backtester.backtest_fixed_strategy(num_iterations=12)
    backtester.print_results(results_2, "场景2")
    
    print("\n回测程序执行完成")


if __name__ == '__main__':
    main()
