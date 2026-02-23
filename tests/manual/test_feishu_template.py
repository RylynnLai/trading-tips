#!/usr/bin/env python3
"""测试飞书通知模板"""

import sys
from pathlib import Path
sys.path.insert(0, '/Users/imtlll/Documents/trading-tips')

from src.notification.notifier import FeishuNotifier
from datetime import datetime

# 模拟配置
config = {
    'feishu': {
        'webhook_url': 'YOUR_WEBHOOK_URL',  # 需要配置实际的webhook
        'secret': ''
    }
}

# 模拟推荐数据
recommendations = [
    {
        'symbol': '300724',
        'stock_name': '捷佳伟创',
        'score': 85,
        'current_price': 122.70,
        'strategy': '加速行情-持有',
        'trend_type': '加速上涨',
        'ma_alignment': 'bull',
        'priority': '⭐',
        'entry_signal': '不建议追高',
        'hold_signal': '已有持仓继续持有',
        'exit_signal': '等待均线死叉或顶部构造',
        'stop_loss': 110.0,
        'stop_loss_pct': -10.3,
        'targets': [130.0, 140.0, 150.0],
        'risk_reward': 2.5,
        'reasons': [
            '加速上涨中',
            '尚未出现顶部构造',
            '乖离率22.2%，未到极端'
        ],
        'profit_prediction': {
            'targets': [
                {
                    'level': 1,
                    'price': 130.0,
                    'gain_pct': 6.0,
                    'probability': 0.80,
                    'description': '保守目标'
                },
                {
                    'level': 2,
                    'price': 140.0,
                    'gain_pct': 14.1,
                    'probability': 0.60,
                    'description': '适中目标'
                }
            ],
            'holding_period': {
                'min_days': 5,
                'target_days': 15,
                'max_days': 30,
                'description': '中短期持仓'
            }
        }
    },
    {
        'symbol': '688200',
        'stock_name': '华峰测控',
        'score': 78,
        'current_price': 95.50,
        'strategy': '稳定趋势回调',
        'trend_type': '稳定上涨',
        'ma_alignment': 'bull',
        'priority': '⭐⭐',
        'entry_signal': '回踩MA20支撑',
        'hold_signal': '趋势持续',
        'stop_loss': 88.0,
        'stop_loss_pct': -7.9,
        'targets': [100.0, 105.0],
        'risk_reward': 3.0,
        'reasons': [
            '稳定上涨趋势',
            '回调至关键支撑',
            '成交量温和放大'
        ]
    }
]

# 模拟数据信息
data_info = {
    'total_stocks': 833,
    'date_range': '2020-01-02 至 2026-02-23',
    'avg_data_points': 1358
}

print("="*80)
print("测试飞书通知模板")
print("="*80)
print()

# 创建通知器
notifier = FeishuNotifier(config)

# 测试发送（如果配置了webhook，将实际发送）
if config['feishu']['webhook_url'] != 'YOUR_WEBHOOK_URL':
    print("发送飞书通知...")
    success = notifier.send_report_card(
        strategy_name='趋势跟随策略',
        recommendations=recommendations,
        portfolio_stats=None,
        data_info=data_info
    )
    
    if success:
        print("✅ 通知发送成功")
    else:
        print("❌ 通知发送失败")
else:
    print("⚠️  未配置webhook_url，跳过实际发送")
    print()
    print("模拟数据预览：")
    print(f"- 推荐数量: {len(recommendations)}")
    print(f"- 分析股票: {data_info['total_stocks']}")
    print(f"- 数据范围: {data_info['date_range']}")
    print()
    print("前2个推荐：")
    for i, rec in enumerate(recommendations[:2], 1):
        print(f"\n{i}. {rec['stock_name']} ({rec['symbol']})")
        print(f"   评分: {rec['score']}, 策略: {rec['strategy']}")
        print(f"   价格: ¥{rec['current_price']:.2f}")
        if rec.get('profit_prediction'):
            targets = rec['profit_prediction'].get('targets', [])
            if targets:
                t1 = targets[0]
                print(f"   目标: ¥{t1['price']:.2f} (+{t1['gain_pct']:.1f}%)")

print()
print("="*80)
print("✅ 测试完成")
print("="*80)
