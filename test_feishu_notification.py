"""
测试飞书通知功能

验证飞书webhook通知的测试脚本
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.notification.notifier import FeishuNotifier, NotificationManager
import yaml
from datetime import datetime


def test_feishu_basic():
    """测试飞书基础通知"""
    print("=" * 70)
    print("测试飞书通知器")
    print("=" * 70)
    
    # 1. 加载配置
    print("\n1. 加载配置...")
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    notification_config = config['notification']
    print(f"✓ 配置加载成功")
    print(f"  启用渠道: {notification_config['enabled_channels']}")
    
    # 2. 初始化飞书通知器
    print("\n2. 初始化飞书通知器...")
    feishu_config = notification_config.get('feishu', {})
    
    if not feishu_config.get('webhook_url'):
        print("⚠️  警告: 未配置飞书webhook_url")
        print("   请在 config/config.yaml 中配置:")
        print("   notification:")
        print("     feishu:")
        print("       webhook_url: 'https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN'")
        print("\n   你可以在飞书群聊中添加自定义机器人获取webhook地址")
        return False
    
    notifier = FeishuNotifier(notification_config)
    print(f"✓ 飞书通知器初始化成功")
    print(f"  Webhook URL: {feishu_config['webhook_url'][:60]}...")
    
    # 3. 测试文本消息
    print("\n3. 测试文本消息...")
    try:
        success = notifier.send(
            message="这是一条测试消息，来自证券交易推荐系统 🚀",
            title="测试通知",
            msg_type="text"
        )
        
        if success:
            print("✓ 文本消息发送成功")
        else:
            print("✗ 文本消息发送失败")
            
    except Exception as e:
        print(f"✗ 文本消息发送失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 4. 测试富文本消息
    print("\n4. 测试富文本消息...")
    try:
        message = "**证券交易推荐系统测试**\n\n" \
                 "这是一条富文本测试消息\n\n" \
                 "- 支持Markdown格式\n" \
                 "- 支持emoji表情 📊\n" \
                 "- 支持多种样式"
        
        success = notifier.send(
            message=message,
            title="📊 富文本测试",
            msg_type="post"
        )
        
        if success:
            print("✓ 富文本消息发送成功")
        else:
            print("✗ 富文本消息发送失败")
            
    except Exception as e:
        print(f"✗ 富文本消息发送失败: {e}")
        import traceback
        traceback.print_exc()
    
    # 5. 测试交互式卡片消息
    print("\n5. 测试交互式卡片消息...")
    try:
        message = "**系统功能测试**\n\n" \
                 "✅ 数据源模块正常\n" \
                 "✅ 策略分析模块正常\n" \
                 "✅ 报告生成模块正常\n" \
                 "✅ 通知推送模块正常\n\n" \
                 "所有核心功能运行正常！"
        
        success = notifier.send(
            message=message,
            title="🎉 系统状态检查",
            msg_type="interactive"
        )
        
        if success:
            print("✓ 交互式卡片消息发送成功")
        else:
            print("✗ 交互式卡片消息发送失败")
            
    except Exception as e:
        print(f"✗ 交互式卡片消息发送失败: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 70)
    print("✅ 飞书基础通知测试完成!")
    print("=" * 70)
    
    return True


def test_feishu_report_card():
    """测试飞书推荐报告卡片"""
    print("\n" + "=" * 70)
    print("测试飞书推荐报告卡片")
    print("=" * 70)
    
    # 1. 加载配置
    print("\n1. 加载配置...")
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    notification_config = config['notification']
    
    # 2. 初始化飞书通知器
    print("\n2. 初始化飞书通知器...")
    notifier = FeishuNotifier(notification_config)
    print(f"✓ 飞书通知器初始化成功")
    
    # 3. 准备测试数据
    print("\n3. 准备推荐数据...")
    
    strategy_name = "技术分析策略"
    
    # 模拟推荐列表
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
            'momentum': -2.1,
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
        'avg_momentum': 5.84,
        'expected_annual_return': '15-20%',
        'avg_sharpe_ratio': 1.35,
        'avg_max_drawdown': -8.5
    }
    
    print(f"✓ 推荐数据准备完成")
    print(f"  策略: {strategy_name}")
    print(f"  推荐数量: {len(recommendations)}")
    
    # 4. 发送推荐报告卡片
    print("\n4. 发送推荐报告卡片...")
    try:
        success = notifier.send_report_card(
            strategy_name=strategy_name,
            recommendations=recommendations,
            portfolio_stats=portfolio_stats
        )
        
        if success:
            print("✓ 推荐报告卡片发送成功")
            print("\n请检查你的飞书群聊，应该能看到一个漂亮的推荐报告卡片 📊")
        else:
            print("✗ 推荐报告卡片发送失败")
            
    except Exception as e:
        print(f"✗ 推荐报告卡片发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ 飞书推荐报告卡片测试完成!")
    print("=" * 70)
    
    return True


def test_notification_manager():
    """测试通知管理器"""
    print("\n" + "=" * 70)
    print("测试通知管理器")
    print("=" * 70)
    
    # 1. 加载配置
    print("\n1. 加载配置...")
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    notification_config = config['notification']
    
    # 2. 初始化通知管理器
    print("\n2. 初始化通知管理器...")
    manager = NotificationManager(notification_config)
    print(f"✓ 通知管理器初始化成功")
    print(f"  启用渠道数: {len(manager.notifiers)}")
    
    # 3. 发送测试通知
    print("\n3. 通过所有渠道发送测试通知...")
    try:
        results = manager.send_all(
            message="**通知管理器测试**\n\n这是通过通知管理器发送的测试消息",
            title="📢 通知管理器测试"
        )
        
        print(f"✓ 通知发送完成")
        for channel, success in results.items():
            status = "✓" if success else "✗"
            print(f"  {status} {channel}: {'成功' if success else '失败'}")
        
    except Exception as e:
        print(f"✗ 通知发送失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 70)
    print("✅ 通知管理器测试完成!")
    print("=" * 70)
    
    return True


if __name__ == '__main__':
    success = True
    
    # 测试基础通知
    if not test_feishu_basic():
        success = False
    
    # 测试推荐报告卡片
    if not test_feishu_report_card():
        success = False
    
    # 测试通知管理器
    if not test_notification_manager():
        success = False
    
    print("\n" + "=" * 70)
    if success:
        print("🎉 所有测试通过!")
    else:
        print("⚠️  部分测试未通过，请检查配置")
    print("=" * 70)
    
    sys.exit(0 if success else 1)
