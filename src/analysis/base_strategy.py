"""
策略基类

定义策略的统一接口
"""

from abc import ABC, abstractmethod
from typing import Dict, List
import pandas as pd
from loguru import logger


class BaseStrategy(ABC):
    """
    策略基类
    
    所有策略都应该继承此类并实现相关方法
    """
    
    def __init__(self, config: Dict):
        """
        初始化策略
        
        Args:
            config: 策略配置
        """
        self.config = config
        self.name = self.__class__.__name__
        logger.info(f"初始化策略: {self.name}")
    
    @abstractmethod
    def analyze(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        分析数据并生成信号
        
        Args:
            data: 输入数据
            
        Returns:
            DataFrame: 包含分析结果和信号的数据
        """
        pass
    
    @abstractmethod
    def generate_recommendations(self, analyzed_data: pd.DataFrame) -> List[Dict]:
        """
        根据分析结果生成推荐
        
        Args:
            analyzed_data: 分析后的数据
            
        Returns:
            List[Dict]: 推荐列表，每个推荐包含代码、名称、得分、理由等
        """
        pass
    
    def get_name(self) -> str:
        """
        获取策略名称
        
        Returns:
            str: 策略名称
        """
        return self.name
    
    def validate_config(self) -> bool:
        """
        验证配置是否有效
        
        Returns:
            bool: 配置是否有效
        """
        return True
