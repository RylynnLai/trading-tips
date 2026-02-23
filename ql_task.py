#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
青龙面板定时任务入口脚本

在青龙面板中运行本脚本，支持从环境变量读取配置
支持多种运行模式和完整的错误处理

环境变量说明：
- TASK_MODE: 任务模式 (full/quick/test)
- USE_LOCAL_DATA: 是否使用本地数据 (true/false)
- MAX_STOCKS: 最大分析股票数量
- MIN_SCORE: 最低推荐分数
- ENABLE_NOTIFICATION: 是否启用通知推送 (true/false)
- ENABLE_BACKTEST: 是否启用回测 (true/false)
"""

import os
import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.env_config import load_config_from_env
from src.main import TradingTipsApp
from loguru import logger


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数（支持青龙面板传参）
    
    Returns:
        命令行参数
    """
    parser = argparse.ArgumentParser(
        description='青龙面板 - 证券交易推荐系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 完整模式（分析+回测+通知）
  python ql_task.py --mode full
  
  # 快速模式（仅分析+通知）
  python ql_task.py --mode quick --max-stocks 50
  
  # 测试模式（仅分析前10只股票）
  python ql_task.py --mode test --max-stocks 10 --no-notify
        """
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        default=os.getenv('TASK_MODE', 'full'),
        choices=['full', 'quick', 'test'],
        help='任务模式: full=完整分析, quick=快速分析, test=测试模式 (默认: full)'
    )
    
    parser.add_argument(
        '--local',
        action='store_true',
        default=os.getenv('USE_LOCAL_DATA', 'true').lower() in ('true', '1', 'yes'),
        help='使用本地数据而非在线API (默认: true)'
    )
    
    parser.add_argument(
        '--max-stocks',
        type=int,
        default=int(os.getenv('MAX_STOCKS', '100')),
        help='最大分析股票数量 (默认: 100)'
    )
    
    parser.add_argument(
        '--min-score',
        type=int,
        default=int(os.getenv('MIN_SCORE', '60')),
        help='最低推荐分数 (0-100) (默认: 60)'
    )
    
    parser.add_argument(
        '--notify',
        dest='enable_notify',
        action='store_true',
        default=os.getenv('ENABLE_NOTIFICATION', 'true').lower() in ('true', '1', 'yes'),
        help='启用通知推送 (默认: true)'
    )
    
    parser.add_argument(
        '--no-notify',
        dest='enable_notify',
        action='store_false',
        help='禁用通知推送'
    )
    
    parser.add_argument(
        '--backtest',
        dest='enable_backtest',
        action='store_true',
        default=os.getenv('ENABLE_BACKTEST', 'false').lower() in ('true', '1', 'yes'),
        help='启用回测验证 (默认: false)'
    )
    
    parser.add_argument(
        '--no-backtest',
        dest='enable_backtest',
        action='store_false',
        help='禁用回测验证'
    )
    
    parser.add_argument(
        '--debug',
        action='store_true',
        default=os.getenv('DEBUG_MODE', 'false').lower() in ('true', '1', 'yes'),
        help='启用调试模式（输出详细日志）'
    )
    
    return parser.parse_args()


def configure_logger(debug: bool = False):
    """
    配置日志记录器
    
    Args:
        debug: 是否启用调试模式
    """
    # 移除默认的 logger
    logger.remove()
    
    # 添加控制台输出
    log_level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stdout,
        level=log_level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>"
    )
    
    # 添加文件输出
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    
    logger.add(
        log_dir / "ql_task_{time:YYYY-MM-DD}.log",
        level=log_level,
        rotation="00:00",
        retention="30 days",
        compression="zip",
        encoding="utf-8"
    )


def print_task_summary(
    mode: str,
    args: argparse.Namespace,
    start_time: datetime,
    end_time: datetime,
    success: bool,
    stats: Optional[Dict[str, Any]] = None
):
    """
    打印任务执行摘要
    
    Args:
        mode: 任务模式
        args: 命令行参数
        start_time: 开始时间
        end_time: 结束时间
        success: 是否成功
        stats: 统计数据
    """
    duration = (end_time - start_time).total_seconds()
    
    logger.info("=" * 70)
    logger.info("📊 任务执行摘要")
    logger.info("=" * 70)
    logger.info(f"任务模式: {mode}")
    logger.info(f"开始时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"执行时长: {duration:.2f} 秒")
    logger.info(f"执行状态: {'✅ 成功' if success else '❌ 失败'}")
    
    if stats:
        logger.info("-" * 70)
        logger.info("统计信息:")
        logger.info(f"  分析股票数量: {stats.get('analyzed_stocks', 0)}")
        logger.info(f"  生成推荐数量: {stats.get('recommendations', 0)}")
        if stats.get('avg_score'):
            logger.info(f"  平均推荐分数: {stats['avg_score']:.2f}")
        if stats.get('report_files'):
            logger.info(f"  生成报告文件: {', '.join(stats['report_files'])}")
        if stats.get('notification_sent'):
            logger.info(f"  通知推送状态: ✅ 已发送")
    
    logger.info("=" * 70)


def save_task_result(
    success: bool,
    stats: Optional[Dict[str, Any]] = None,
    error: Optional[str] = None
):
    """
    保存任务执行结果（供青龙面板查看）
    
    Args:
        success: 是否成功
        stats: 统计数据
        error: 错误信息
    """
    result = {
        'timestamp': datetime.now().isoformat(),
        'success': success,
        'stats': stats or {},
        'error': error
    }
    
    result_dir = Path("data/task_results")
    result_dir.mkdir(parents=True, exist_ok=True)
    
    result_file = result_dir / f"ql_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    logger.info(f"任务结果已保存: {result_file}")


def run_task(args: argparse.Namespace) -> tuple[bool, Optional[Dict[str, Any]]]:
    """
    执行任务主逻辑
    
    Args:
        args: 命令行参数
        
    Returns:
        (success, stats): 是否成功和统计信息
    """
    try:
        # 从环境变量加载配置
        config = load_config_from_env()
        
        # 根据参数调整配置
        if args.local:
            config['data_source']['use_local_data'] = True
        
        config['analysis']['max_stocks'] = args.max_stocks
        config['analysis']['min_score'] = args.min_score
        
        # 根据模式调整配置
        if args.mode == 'test':
            config['analysis']['max_stocks'] = min(args.max_stocks, 10)
            logger.info("测试模式：限制最多分析 10 只股票")
        elif args.mode == 'quick':
            args.enable_backtest = False
            logger.info("快速模式：禁用回测功能")
        
        # 创建应用实例
        logger.info(f"创建应用实例 (模式: {args.mode})")
        app = TradingTipsApp(
            config_path=None,
            config=config
        )
        
        # 运行应用
        logger.info("开始执行分析流程...")
        app.run()
        
        # 收集统计信息
        stats = {
            'analyzed_stocks': args.max_stocks,
            'recommendations': 0,
            'report_files': [],
            'notification_sent': args.enable_notify
        }
        
        # 检查生成的报告文件
        report_dir = Path("data/reports")
        if report_dir.exists():
            today = datetime.now().strftime('%Y%m%d')
            report_files = list(report_dir.glob(f"*{today}*.json"))
            if report_files:
                # 读取最新的报告文件统计信息
                latest_report = sorted(report_files)[-1]
                with open(latest_report, 'r', encoding='utf-8') as f:
                    report_data = json.load(f)
                    if 'recommendations' in report_data:
                        stats['recommendations'] = len(report_data['recommendations'])
                        if stats['recommendations'] > 0:
                            scores = [r.get('score', 0) for r in report_data['recommendations']]
                            stats['avg_score'] = sum(scores) / len(scores)
                
                stats['report_files'] = [f.name for f in report_files]
        
        return True, stats
        
    except Exception as e:
        logger.error(f"任务执行失败: {e}", exc_info=True)
        return False, None


def main():
    """
    青龙面板任务主入口
    """
    start_time = datetime.now()
    success = False
    stats = None
    error = None
    
    try:
        # 解析命令行参数
        args = parse_arguments()
        
        # 配置日志
        configure_logger(debug=args.debug)
        
        # 打印任务信息
        logger.info("=" * 70)
        logger.info("🚀 青龙面板 - 证券交易推荐系统")
        logger.info("=" * 70)
        logger.info(f"任务模式: {args.mode}")
        logger.info(f"数据源: {'本地数据' if args.local else '在线API'}")
        logger.info(f"最大股票数: {args.max_stocks}")
        logger.info(f"最低分数: {args.min_score}")
        logger.info(f"通知推送: {'启用' if args.enable_notify else '禁用'}")
        logger.info(f"回测验证: {'启用' if args.enable_backtest else '禁用'}")
        logger.info("=" * 70)
        
        # 执行任务
        success, stats = run_task(args)
        
        # 打印摘要
        end_time = datetime.now()
        print_task_summary(
            mode=args.mode,
            args=args,
            start_time=start_time,
            end_time=end_time,
            success=success,
            stats=stats
        )
        
        # 保存结果
        save_task_result(success=success, stats=stats)
        
        return 0 if success else 1
        
    except Exception as e:
        error = str(e)
        logger.error(f"任务执行过程中发生异常: {e}", exc_info=True)
        
        # 打印摘要
        end_time = datetime.now()
        print_task_summary(
            mode=getattr(args, 'mode', 'unknown') if 'args' in locals() else 'unknown',
            args=args if 'args' in locals() else None,
            start_time=start_time,
            end_time=end_time,
            success=False
        )
        
        # 保存错误结果
        save_task_result(success=False, error=error)
        
        return 1


if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
