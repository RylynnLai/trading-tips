"""
测试报告生成器

验证报告生成功能的测试脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.report.report_generator import ReportGenerator
import yaml
from datetime import datetime

def test_report_generation():
    """测试报告生成"""
    print("=" * 70)
    print("测试报告生成器")
    print("=" * 70)
    
    # 1. 加载配置
    print("\n1. 加载配置...")
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    report_config = config['report']
    print(f"✓ 配置加载成功: {report_config}")
    
    # 2. 初始化报告生成器
    print("\n2. 初始化报告生成器...")
    generator = ReportGenerator(report_config)
    print(f"✓ 报告生成器初始化成功")
    print(f"  输出路径: {generator.output_path}")
    print(f"  格式: {generator.format}")
    print(f"  Top N: {generator.top_n}")
    
    # 3. 准备测试数据
    print("\n3. 准备测试数据...")
    
    strategy_name = "技术分析策略"
    
    # 模拟推荐列表（基于verify_all.py的验证数据）
    recommendations = [
        {
            'rank': 1,
            'code': '600519',
            'name': '贵州茅台',
            'current_price': '1680.50',
            'score': 9.2,
            'volatility': 12.5,
            'momentum': 8.3,
            'suggested_position': '20%',
            'reasons': [
                'MA均线多头排列，趋势向上',
                '近期动量强劲(+8.3%)',
                '综合得分最高(9.2分)'
            ]
        },
        {
            'rank': 2,
            'code': '000858',
            'name': '五粮液',
            'current_price': '152.30',
            'score': 8.8,
            'volatility': 14.2,
            'momentum': 5.7,
            'suggested_position': '18%',
            'reasons': [
                '波动率适中(14.2%)',
                '稳定的上涨动量(+5.7%)',
                '行业龙头，基本面稳健'
            ]
        },
        {
            'rank': 3,
            'code': '601318',
            'name': '中国平安',
            'current_price': '42.85',
            'score': 8.5,
            'volatility': 11.8,
            'momentum': 3.2,
            'suggested_position': '15%',
            'reasons': [
                '波动率低(11.8%)，风险较小',
                '估值合理',
                '分红稳定'
            ]
        },
        {
            'rank': 4,
            'code': '300750',
            'name': '宁德时代',
            'current_price': '185.60',
            'score': 8.2,
            'volatility': 18.5,
            'momentum': 12.8,
            'suggested_position': '12%',
            'reasons': [
                '行业景气度高',
                '强劲的增长动量(+12.8%)',
                '技术领先'
            ]
        },
        {
            'rank': 5,
            'code': '000333',
            'name': '美的集团',
            'current_price': '56.20',
            'score': 7.9,
            'volatility': 13.6,
            'momentum': 4.5,
            'suggested_position': '10%',
            'reasons': [
                '白马蓝筹，波动率适中(13.6%)',
                '业绩稳定增长',
                '现金流良好'
            ]
        }
    ]
    
    # 模拟组合统计
    portfolio_stats = {
        'portfolio_count': len(recommendations),
        'avg_volatility': 14.12,
        'avg_momentum': 6.9,
        'expected_annual_return': '15-20%',
        'avg_sharpe_ratio': 1.35,
        'avg_max_drawdown': -8.5
    }
    
    # 模拟回测结果（简化版）
    backtest_results = {
        'period': '2023-01-01 to 2024-01-01',
        'total_return': 18.5,
        'annual_return': 18.5,
        'sharpe_ratio': 1.42,
        'max_drawdown': -9.2,
        'win_rate': 62.5
    }
    
    print(f"✓ 测试数据准备完成")
    print(f"  策略: {strategy_name}")
    print(f"  推荐数量: {len(recommendations)}")
    
    # 4. 生成报告
    print("\n4. 生成报告...")
    try:
        report_paths = generator.generate_report(
            strategy_name=strategy_name,
            recommendations=recommendations,
            portfolio_stats=portfolio_stats,
            backtest_results=backtest_results
        )
        
        print(f"✓ 报告生成成功，共 {len(report_paths)} 个文件:")
        for format_type, path in report_paths.items():
            print(f"  - {format_type.upper()}: {path}")
            # 检查文件是否存在
            if Path(path).exists():
                size = Path(path).stat().st_size
                print(f"    文件大小: {size} bytes")
        
    except Exception as e:
        print(f"✗ 报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. 测试简单文本报告
    print("\n5. 测试简单文本报告...")
    try:
        simple_report = generator.generate_simple_report(
            strategy_name=strategy_name,
            recommendations=recommendations
        )
        print(f"✓ 简单文本报告生成成功，长度: {len(simple_report)} 字符")
        print("\n--- 简单文本报告预览 ---")
        print(simple_report[:500] + "..." if len(simple_report) > 500 else simple_report)
        
    except Exception as e:
        print(f"✗ 简单文本报告生成失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ 报告生成器测试全部通过!")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    success = test_report_generation()
    sys.exit(0 if success else 1)
