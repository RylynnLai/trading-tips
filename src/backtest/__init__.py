"""
回测模块

负责策略回测和性能评估
"""

from .backtester import Backtester, BacktestResult

__all__ = ['Backtester', 'BacktestResult']
