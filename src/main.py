"""
证券交易推荐系统 - 主程序

整合各个模块，执行完整的分析和推送流程
"""

import sys
from pathlib import Path
import yaml
from loguru import logger
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_source import DataFetcher
from src.analysis import TechnicalAnalyzer, FundamentalAnalyzer
from src.backtest import Backtester
from src.report import ReportGenerator
from src.notification.notifier import NotificationManager


class TradingTipsApp:
    """
    证券推荐系统主应用类
    """
    
    def __init__(self, config_path: str = None, config: dict = None):
        """
        初始化应用
        
        Args:
            config_path: 配置文件路径（如果提供，将从文件加载配置）
            config: 配置字典（如果提供，将直接使用该配置，优先级高于config_path）
        """
        # 加载配置：优先使用传入的config字典，其次从文件加载
        if config is not None:
            self.config = config
            logger.info("使用传入的配置字典")
        elif config_path is not None:
            self.config = self._load_config(config_path)
        else:
            # 默认从config/config.yaml加载
            self.config = self._load_config('config/config.yaml')
        
        self._setup_logging()
        self._init_modules()
        
        logger.info("=" * 60)
        logger.info("证券交易推荐系统启动")
        logger.info("=" * 60)
    
    def _load_config(self, config_path: str) -> dict:
        """
        加载配置文件
        
        Args:
            config_path: 配置文件路径
            
        Returns:
            dict: 配置字典
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"配置文件不存在: {config_path}")
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        
        return config
    
    def _setup_logging(self):
        """
        配置日志系统
        """
        log_config = self.config.get('logging', {})
        log_level = log_config.get('level', 'INFO')
        log_file = log_config.get('log_file', 'logs/trading_tips.log')
        
        # 创建日志目录
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        # 配置loguru
        logger.remove()  # 移除默认处理器
        
        # 添加控制台输出
        logger.add(
            sys.stdout,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
                   "<level>{message}</level>"
        )
        
        # 添加文件输出
        logger.add(
            log_file,
            level=log_level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function} - {message}",
            rotation=log_config.get('max_size', '10MB'),
            retention=log_config.get('backup_count', 5),
            encoding='utf-8'
        )
        
        logger.info(f"日志系统初始化完成，级别: {log_level}")
    
    def _init_modules(self):
        """
        初始化各个功能模块
        """
        logger.info("初始化功能模块...")
        
        # 初始化数据源模块
        self.data_fetcher = DataFetcher(self.config.get('data_source', {}))
        
        # 初始化分析模块
        analysis_config = self.config.get('analysis', {})
        self.technical_analyzer = TechnicalAnalyzer(analysis_config)
        self.fundamental_analyzer = FundamentalAnalyzer(analysis_config)
        
        # 初始化回测模块
        self.backtester = Backtester(self.config.get('backtest', {}))
        
        # 初始化报告生成模块
        self.report_generator = ReportGenerator(self.config.get('report', {}))
        
        # 初始化通知推送模块
        self.notification_manager = NotificationManager(
            self.config.get('notification', {})
        )
        
        logger.info("所有功能模块初始化完成")
    
    def run(self):
        """
        运行主流程
        """
        try:
            logger.info("开始执行分析流程...")
            
            # 步骤1: 获取数据
            logger.info("步骤1: 获取证券数据")
            stock_list = self._fetch_data()
            
            # 步骤2: 数据分析
            logger.info("步骤2: 执行数据分析")
            analysis_results = self._analyze_data(stock_list)
            
            # 步骤3: 回测验证
            logger.info("步骤3: 执行回测验证")
            backtest_results = self._run_backtest(analysis_results)
            
            # 步骤4: 生成报告
            logger.info("步骤4: 生成分析报告")
            report_files = self._generate_report(analysis_results, backtest_results)
            
            # 步骤5: 推送通知
            logger.info("步骤5: 推送分析结果")
            self._send_notification(analysis_results, report_files)
            
            logger.info("=" * 60)
            logger.info("分析流程执行完成")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"执行过程中发生错误: {e}", exc_info=True)
            raise
    
    def _fetch_data(self):
        """
        获取证券数据
        
        Returns:
            获取的数据
        """
        # TODO: 实现数据获取逻辑
        logger.info("从数据源获取证券列表和行情数据")
        
        # 获取股票列表
        # stock_list = self.data_fetcher.fetch_stock_list()
        
        # 获取实时数据或历史数据
        # ...
        
        return None
    
    def _analyze_data(self, stock_data):
        """
        分析数据
        
        Args:
            stock_data: 证券数据
            
        Returns:
            分析结果
        """
        # TODO: 实现数据分析逻辑
        logger.info("执行技术分析和基本面分析")
        
        # 技术分析
        # technical_result = self.technical_analyzer.analyze(stock_data)
        
        # 基本面分析
        # fundamental_result = self.fundamental_analyzer.analyze(stock_data)
        
        return {}
    
    def _run_backtest(self, analysis_results):
        """
        运行回测
        
        Args:
            analysis_results: 分析结果
            
        Returns:
            回测结果
        """
        # TODO: 实现回测逻辑
        logger.info("对分析策略进行历史回测")
        
        # backtest_result = self.backtester.run(signals, price_data)
        
        return {}
    
    def _generate_report(self, analysis_results, backtest_results):
        """
        生成报告
        
        Args:
            analysis_results: 分析结果
            backtest_results: 回测结果
            
        Returns:
            报告文件路径字典
        """
        # TODO: 实现报告生成逻辑
        logger.info("生成分析报告和可视化图表")
        
        # report_files = self.report_generator.generate_report(
        #     analysis_results, backtest_results
        # )
        
        return {}
    
    def _send_notification(self, analysis_results, report_files):
        """
        发送通知
        
        Args:
            analysis_results: 分析结果
            report_files: 报告文件
        """
        # TODO: 实现通知推送逻辑
        logger.info("通过配置的渠道推送分析结果")
        
        # 格式化消息
        # message = self.notification_manager.format_message(recommendations)
        
        # 发送通知
        # self.notification_manager.send_all(message, title="今日证券推荐")


def main():
    """
    主函数
    """
    try:
        # 创建应用实例
        app = TradingTipsApp()
        
        # 运行应用
        app.run()
        
    except Exception as e:
        logger.error(f"程序执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
