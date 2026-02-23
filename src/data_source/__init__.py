"""
数据源模块

负责从各种数据源获取证券数据
"""

from .data_fetcher import DataFetcher
from .base_provider import BaseProvider
from .akshare_provider import AkShareProvider

__all__ = [
    'DataFetcher', 
    'BaseProvider',
    'AkShareProvider',
]
