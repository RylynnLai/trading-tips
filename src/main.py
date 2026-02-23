"""
证券交易推荐系统 - 主程序

整合各个模块，执行完整的分析和推送流程
"""

import sys
import os
from pathlib import Path
import yaml
from loguru import logger
from datetime import datetime, timedelta
import pandas as pd
from typing import Dict, List, Optional

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_source import DataFetcher
from src.analysis.analyzer import TechnicalAnalyzer
from src.analysis.trend_strategy import TrendFollowingStrategy
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
        data_source_config = self.config.get('data_source', {})
        self.data_fetcher = DataFetcher(data_source_config)
        
        # 初始化分析模块
        analysis_config = self.config.get('analysis', {})
        self.technical_analyzer = TechnicalAnalyzer(analysis_config)
        
        # 初始化趋势策略
        trend_config = analysis_config.get('trend_strategy', {})
        self.trend_strategy = TrendFollowingStrategy(trend_config)
        
        # 初始化回测模块
        self.backtester = Backtester(self.config.get('backtest', {}))
        
        # 初始化报告生成模块
        self.report_generator = ReportGenerator(self.config.get('report', {}))
        
        # 初始化通知推送模块
        self.notification_manager = NotificationManager(
            self.config.get('notification', {})
        )
        
        # 本地数据配置
        self.use_local_data = self.config.get('data_source', {}).get('use_local_data', False)
        self.local_data_dir = Path(self.config.get('data_source', {}).get('local_data_dir', 
                                   '~/.qlib/qlib_data/cn_data')).expanduser()
        
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
            
            # 收集数据时间范围信息
            data_info = self._collect_data_info(stock_list)
            
            # 保存数据信息供通知使用
            self._last_data_info = data_info
            
            # 步骤2: 数据分析
            logger.info("步骤2: 执行数据分析")
            analysis_results = self._analyze_data(stock_list)
            
            # 步骤3: 回测验证（仅在启用时执行）
            backtest_results = {}
            if self.config.get('backtest', {}).get('enabled', False):
                logger.info("步骤3: 执行回测验证")
                backtest_results = self._run_backtest(analysis_results)
            else:
                logger.info("步骤3: 回测验证已跳过（未启用）")
            
            # 步骤4: 生成报告
            logger.info("步骤4: 生成分析报告")
            report_files = self._generate_report(analysis_results, backtest_results, data_info)
            
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
            Dict[str, pd.DataFrame]: 股票代码到数据的映射
        """
        logger.info("开始获取证券数据...")
        
        stock_data = {}
        
        if self.use_local_data:
            # 从本地加载数据
            logger.info(f"从本地目录加载数据: {self.local_data_dir}")
            stock_data = self._load_local_data()
        else:
            # 从API获取数据
            logger.info("从API获取实时数据")
            stock_data = self._fetch_online_data()
        
        logger.info(f"成功获取 {len(stock_data)} 只股票的数据")
        return stock_data
    
    def _load_local_data(self) -> Dict[str, pd.DataFrame]:
        """
        从本地CSV文件加载数据
        
        Returns:
            Dict[str, pd.DataFrame]: 股票数据字典
        """
        stock_data = {}
        
        if not self.local_data_dir.exists():
            logger.error(f"本地数据目录不存在: {self.local_data_dir}")
            return stock_data
        
        csv_files = list(self.local_data_dir.glob("*.csv"))
        logger.info(f"找到 {len(csv_files)} 个数据文件")
        
        # 限制加载数量
        max_stocks = self.config.get('analysis', {}).get('max_stocks', 100)
        csv_files = csv_files[:max_stocks]
        
        for csv_file in csv_files:
            try:
                stock_code = csv_file.stem
                df = pd.read_csv(csv_file)
                
                # 标准化列名
                column_mapping = {
                    '日期': 'date',
                    '股票代码': 'symbol',
                    '开盘': '开盘',
                    '收盘': '收盘',
                    '最高': '最高',
                    '最低': '最低',
                    '成交量': '成交量',
                    '成交额': '成交额'
                }
                
                # 只重命名日期列
                if '日期' in df.columns:
                    df['date'] = pd.to_datetime(df['日期'])
                    df = df.set_index('date').sort_index()
                
                if not df.empty and len(df) >= 60:  # 至少需要60个交易日
                    stock_data[stock_code] = df
                    
            except Exception as e:
                logger.warning(f"加载 {csv_file.name} 失败: {e}")
        
        return stock_data
    
    def _fetch_online_data(self) -> Dict[str, pd.DataFrame]:
        """
        从在线API获取数据
        
        Returns:
            Dict[str, pd.DataFrame]: 股票数据字典
        """
        stock_data = {}
        
        # 获取股票列表
        market = self.config.get('analysis', {}).get('market', 'A')
        stock_list = self.data_fetcher.fetch_stock_list(market)
        
        if stock_list.empty:
            logger.error("未能获取股票列表")
            return stock_data
        
        # 限制数量
        max_stocks = self.config.get('analysis', {}).get('max_stocks', 50)
        stock_list = stock_list.head(max_stocks)
        
        # 日期配置
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=365*2)).strftime('%Y-%m-%d')
        
        # 获取每只股票的数据
        for idx, row in stock_list.iterrows():
            try:
                symbol = row.get('代码', row.get('symbol', ''))
                
                df = self.data_fetcher.fetch_stock_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if not df.empty and len(df) >= 60:
                    stock_data[symbol] = df
                    
            except Exception as e:
                logger.warning(f"获取 {symbol} 数据失败: {e}")
        
        return stock_data
    
    def _collect_data_info(self, stock_data: Dict[str, pd.DataFrame]) -> Dict:
        """
        收集数据信息（时间范围、数据量等）
        
        Args:
            stock_data: 股票数据字典
            
        Returns:
            Dict: 数据信息
        """
        if not stock_data:
            return {
                'total_stocks': 0,
                'date_range': None,
                'start_date': None,
                'end_date': None,
                'avg_data_points': 0
            }
        
        # 收集所有数据的时间范围
        all_dates = []
        total_data_points = 0
        
        for symbol, df in stock_data.items():
            if not df.empty:
                # 获取索引（日期）
                dates = df.index if df.index.name == 'date' or isinstance(df.index, pd.DatetimeIndex) else pd.to_datetime(df['date']) if 'date' in df.columns else None
                if dates is not None:
                    all_dates.extend(dates)
                    total_data_points += len(df)
        
        if all_dates:
            start_date = min(all_dates)
            end_date = max(all_dates)
            avg_data_points = total_data_points // len(stock_data) if stock_data else 0
        else:
            start_date = None
            end_date = None
            avg_data_points = 0
        
        data_info = {
            'total_stocks': len(stock_data),
            'date_range': f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}" if start_date and end_date else "未知",
            'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
            'end_date': end_date.strftime('%Y-%m-%d') if end_date else None,
            'avg_data_points': avg_data_points
        }
        
        logger.info(f"数据时间范围: {data_info['date_range']}, 平均数据点数: {avg_data_points}")
        
        return data_info
    
    def _analyze_data(self, stock_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """
        分析数据
        
        Args:
            stock_data: 股票数据字典
            
        Returns:
            List[Dict]: 推荐结果列表
        """
        logger.info("执行趋势分析...")
        
        if not stock_data:
            logger.warning("无可用数据进行分析")
            return []
        
        # 使用趋势跟随策略进行批量分析
        recommendations = self.trend_strategy.batch_analyze(stock_data)
        
        # 过滤和排序
        min_score = self.config.get('analysis', {}).get('min_score', 60)
        recommendations = [
            rec for rec in recommendations 
            if rec.get('score', 0) >= min_score
        ]
        
        # 限制推荐数量
        max_recommendations = self.config.get('analysis', {}).get('max_recommendations', 20)
        recommendations = recommendations[:max_recommendations]
        
        logger.info(f"分析完成，生成 {len(recommendations)} 个推荐")
        
        return recommendations
    
    def _run_backtest(self, analysis_results: List[Dict]) -> Dict:
        """
        运行回测
        
        Args:
            analysis_results: 分析结果
            
        Returns:
            Dict: 回测结果
        """
        if not self.config.get('backtest', {}).get('enabled', False):
            logger.info("回测功能未启用，跳过")
            return {}
        
        logger.info("对分析策略进行历史回测")
        
        # TODO: 实现完整的回测逻辑
        # backtest_result = self.backtester.run(signals, price_data)
        
        return {}
    
    def _generate_report(self, analysis_results: List[Dict], backtest_results: Dict, data_info: Dict = None) -> Dict:
        """
        生成报告
        
        Args:
            analysis_results: 分析结果
            backtest_results: 回测结果
            data_info: 数据信息（时间范围等）
            
        Returns:
            Dict: 报告文件路径字典
        """
        logger.info("生成分析报告...")
        
        if not analysis_results:
            logger.warning("无分析结果，跳过报告生成")
            return {}
        
        # 生成报告
        try:
            report_files = self.report_generator.generate_report(
                strategy_name="trend_following",
                recommendations=analysis_results,
                portfolio_stats=None,
                backtest_results=backtest_results,
                data_info=data_info
            )
            
            logger.info(f"报告生成完成: {report_files}")
            return report_files
            
        except Exception as e:
            logger.error(f"报告生成失败: {e}")
            return {}
    
    def _send_notification(self, analysis_results: List[Dict], report_files: Dict):
        """
        发送通知
        
        Args:
            analysis_results: 分析结果
            report_files: 报告文件
        """
        if not self.config.get('notification', {}).get('enabled', False):
            logger.info("通知功能未启用，跳过")
            return
        
        logger.info("通过配置的渠道推送分析结果")
        
        if not analysis_results:
            logger.warning("无推荐结果，跳过通知推送")
            return
        
        # 发送通知
        try:
            # 检查是否启用飞书
            notification_config = self.config.get('notification', {})
            enabled_channels = notification_config.get('enabled_channels', [])
            
            if 'feishu' in enabled_channels:
                # 发送飞书卡片通知
                from src.notification.notifier import FeishuNotifier
                
                feishu = FeishuNotifier(notification_config)
                
                # 获取数据信息
                data_info = getattr(self, '_last_data_info', None)
                
                # 发送推荐报告卡片
                success = feishu.send_report_card(
                    strategy_name='趋势跟随策略',
                    recommendations=analysis_results,
                    data_info=data_info
                )
                
                if success:
                    logger.info("飞书通知推送成功")
                else:
                    logger.warning("飞书通知推送失败")
            else:
                # 其他渠道使用简单消息格式
                message = self._format_notification_message(analysis_results)
                self.notification_manager.send_all(
                    message=message,
                    title=f"趋势交易推荐 - {datetime.now().strftime('%Y-%m-%d')}"
                )
                logger.info("通知推送成功")
        except Exception as e:
            logger.error(f"通知推送失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    def _format_notification_message(self, recommendations: List[Dict]) -> str:
        """
        格式化通知消息
        
        Args:
            recommendations: 推荐列表
            
        Returns:
            str: 格式化后的消息
        """
        lines = [
            f"📊 趋势交易推荐 ({datetime.now().strftime('%Y-%m-%d')})",
            f"共 {len(recommendations)} 个推荐",
            "",
            "🔝 Top 5 推荐:",
            ""
        ]
        
        for i, rec in enumerate(recommendations[:5], 1):
            symbol = rec.get('symbol', 'N/A')
            action = rec.get('action', 'N/A')
            score = rec.get('score', 0)
            trend_type = rec.get('trend_type', 'N/A')
            reason = rec.get('reason', 'N/A')
            
            lines.append(f"{i}. {symbol}")
            lines.append(f"   推荐: {action} | 得分: {score:.1f}")
            lines.append(f"   趋势: {trend_type}")
            lines.append(f"   理由: {reason}")
            
            if 'entry_price' in rec:
                lines.append(f"   入场: {rec['entry_price']:.2f}")
            if 'stop_loss' in rec:
                lines.append(f"   止损: {rec['stop_loss']:.2f}")
            
            lines.append("")
        
        return "\n".join(lines)


def main():
    """
    主函数
    """
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='证券交易推荐系统')
    parser.add_argument('--config', type=str, default='config/config.yaml',
                       help='配置文件路径')
    parser.add_argument('--local', action='store_true',
                       help='使用本地数据')
    parser.add_argument('--max-stocks', type=int,
                       help='最大分析股票数量')
    parser.add_argument('--min-score', type=float,
                       help='最低推荐分数')
    parser.add_argument('--notify', action='store_true',
                       help='启用通知推送')
    parser.add_argument('--backtest', action='store_true',
                       help='启用回测')
    
    args = parser.parse_args()
    
    try:
        # 加载配置
        config_path = args.config
        if not Path(config_path).exists():
            # 尝试从config目录加载
            config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        
        # 创建应用实例
        app = TradingTipsApp(config_path=str(config_path))
        
        # 应用命令行参数覆盖配置
        if args.local:
            app.config['data_source']['use_local_data'] = True
        if args.max_stocks:
            app.config.setdefault('analysis', {})['max_stocks'] = args.max_stocks
        if args.min_score:
            app.config.setdefault('analysis', {})['min_score'] = args.min_score
        if args.notify:
            app.config.setdefault('notification', {})['enabled'] = True
        if args.backtest:
            app.config.setdefault('backtest', {})['enabled'] = True
        
        # 运行应用
        app.run()
        
        logger.info("✅ 程序执行成功")
        
    except Exception as e:
        logger.error(f"❌ 程序执行失败: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
