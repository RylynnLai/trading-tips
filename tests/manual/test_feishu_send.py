#!/usr/bin/env python3
"""
测试飞书通知发送功能

使用方法:
1. 在配置文件中设置飞书webhook_url
2. 运行: python test_feishu_send.py
"""

import yaml
from pathlib import Path
from src.notification.notifier import FeishuNotifier
from datetime import datetime

def load_config():
    """加载配置"""
    config_path = Path(__file__).parent / 'config' / 'config.yaml'
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def create_test_recommendations():
    """创建测试推荐数据"""
    return [
        {
            'symbol': '600519',
            'name': '贵州茅台',
            'score': 85.5,
            'current_price': 1850.50,
            'action': '买入',
            'strategy': '加速行情-持有',
            'reason': '价格突破均线密集区，成交量放大，趋势向上',
            'profit_prediction': {
                'expected_return_pct': 15.5,
                'success_probability_pct': 75,
                'target_prices': {
                    'conservative': 1920.0,
                    'moderate': 2050.0,
                    'aggressive': 2180.0
                },
                'stop_loss': 1750.0,
                'holding_period_days': 30
            }
        },
        {
            'symbol': '000858',
            'name': '五粮液',
            'score': 78.3,
            'current_price': 168.80,
            'action': '买入',
            'strategy': '回调买入',
            'reason': '回调至MA60支撑位，MACD金叉，RSI超卖反弹',
            'profit_prediction': {
                'expected_return_pct': 12.3,
                'success_probability_pct': 68,
                'target_prices': {
                    'conservative': 175.0,
                    'moderate': 182.0,
                    'aggressive': 190.0
                },
                'stop_loss': 162.0,
                'holding_period_days': 20
            }
        },
        {
            'symbol': '300750',
            'name': '宁德时代',
            'score': 82.1,
            'current_price': 185.60,
            'action': '买入',
            'strategy': '突破买入',
            'reason': '突破前高压力位，量价齐升，行业景气度提升',
            'profit_prediction': {
                'expected_return_pct': 18.2,
                'success_probability_pct': 70,
                'target_prices': {
                    'conservative': 198.0,
                    'moderate': 215.0,
                    'aggressive': 230.0
                },
                'stop_loss': 178.0,
                'holding_period_days': 25
            }
        },
        {
            'symbol': '601318',
            'name': '中国平安',
            'score': 71.5,
            'current_price': 43.20,
            'action': '买入',
            'strategy': '价值回归',
            'reason': '估值处于历史低位，政策利好，基本面稳健',
            'profit_prediction': {
                'expected_return_pct': 10.5,
                'success_probability_pct': 65,
                'target_prices': {
                    'conservative': 46.0,
                    'moderate': 48.5,
                    'aggressive': 51.0
                },
                'stop_loss': 41.0,
                'holding_period_days': 35
            }
        },
        {
            'symbol': '002594',
            'name': '比亚迪',
            'score': 80.8,
            'current_price': 248.30,
            'action': '买入',
            'strategy': '加速行情-持有',
            'reason': '新能源车销量持续增长，技术创新领先，市场份额扩大',
            'profit_prediction': {
                'expected_return_pct': 16.8,
                'success_probability_pct': 72,
                'target_prices': {
                    'conservative': 265.0,
                    'moderate': 285.0,
                    'aggressive': 305.0
                },
                'stop_loss': 235.0,
                'holding_period_days': 28
            }
        }
    ]

def create_test_portfolio_stats():
    """创建测试组合统计信息"""
    return {
        'portfolio_count': 5,
        'avg_volatility': 28.5,
        'avg_momentum': 15.2,
        'expected_annual_return': '25.8%'
    }

def main():
    """主函数"""
    print("=" * 60)
    print("飞书通知发送测试")
    print("=" * 60)
    
    # 加载配置
    print("\n1. 加载配置文件...")
    config = load_config()
    notification_config = config.get('notification', {})
    
    # 检查飞书配置
    feishu_config = notification_config.get('feishu', {})
    webhook_url = feishu_config.get('webhook_url', '')
    
    if not webhook_url or 'your_webhook_token' in webhook_url:
        print("\n❌ 错误: 请先在 config/config.yaml 中配置飞书 webhook_url")
        print("\n配置步骤:")
        print("1. 在飞书群组中添加自定义机器人")
        print("2. 复制机器人的 webhook 地址")
        print("3. 在 config/config.yaml 中更新 notification.feishu.webhook_url")
        print("4. 如果启用了签名校验，同时配置 secret")
        return
    
    print(f"✓ 飞书配置已找到: {webhook_url[:50]}...")
    
    # 创建飞书通知器
    print("\n2. 初始化飞书通知器...")
    notifier = FeishuNotifier(notification_config)
    
    # 创建测试数据
    print("\n3. 创建测试推荐数据...")
    recommendations = create_test_recommendations()
    portfolio_stats = create_test_portfolio_stats()
    print(f"✓ 创建了 {len(recommendations)} 个测试推荐")
    
    # 发送测试通知
    print("\n4. 发送飞书通知...")
    print(f"   策略名称: 趋势跟随策略")
    print(f"   推荐数量: {len(recommendations)}")
    print(f"   预期年化收益: {portfolio_stats['expected_annual_return']}")
    
    success = notifier.send_report_card(
        strategy_name='趋势跟随策略',
        recommendations=recommendations,
        portfolio_stats=portfolio_stats
    )
    
    # 显示结果
    print("\n" + "=" * 60)
    if success:
        print("✅ 飞书通知发送成功！")
        print("\n请检查您的飞书群组，应该已经收到推荐报告卡片")
        print("\n卡片内容包括:")
        print("  - 数据信息（分析股票数、时间范围等）")
        print("  - 推荐列表（前10个推荐）")
        print("  - 盈利预测（预期收益、成功率、目标价格等）")
        print("  - 风险提示")
    else:
        print("❌ 飞书通知发送失败")
        print("\n可能的原因:")
        print("  1. webhook_url 配置错误")
        print("  2. 网络连接问题")
        print("  3. 机器人被禁用或删除")
        print("  4. 签名校验失败（如果配置了secret）")
    print("=" * 60)

if __name__ == '__main__':
    main()
