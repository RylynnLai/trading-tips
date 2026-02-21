"""
环境变量配置工具

从环境变量读取配置信息，支持青龙面板等环境
"""

import os
from typing import Dict, Any, List
from loguru import logger


def str_to_bool(value: str) -> bool:
    """
    将字符串转换为布尔值
    
    Args:
        value: 字符串值
        
    Returns:
        bool: 布尔值
    """
    return value.lower() in ('true', '1', 'yes', 'on', 'enabled')


def str_to_list(value: str, separator: str = ',') -> List[str]:
    """
    将字符串转换为列表
    
    Args:
        value: 字符串值
        separator: 分隔符
        
    Returns:
        List[str]: 字符串列表
    """
    if not value:
        return []
    return [item.strip() for item in value.split(separator) if item.strip()]


def load_config_from_env() -> Dict[str, Any]:
    """
    从环境变量加载配置
    
    Returns:
        Dict: 配置字典
    """
    logger.info("从环境变量加载配置...")
    
    config = {
        # 数据源配置
        'data_source': {
            'provider': os.getenv('DATA_SOURCE_PROVIDER', 'tushare'),
            'api_key': os.getenv('DATA_SOURCE_API_KEY', ''),
            'update_interval': int(os.getenv('DATA_UPDATE_INTERVAL', '60')),
            'cache': {
                'enabled': str_to_bool(os.getenv('DATA_CACHE_ENABLED', 'true')),
                'expire_time': int(os.getenv('DATA_CACHE_EXPIRE', '3600'))
            }
        },
        
        # 分析配置
        'analysis': {
            'security_types': str_to_list(os.getenv('SECURITY_TYPES', 'stock,fund,etf')),
            'indicators': [
                {
                    'name': 'MA',
                    'params': {
                        'periods': [5, 10, 20, 60]
                    }
                },
                {
                    'name': 'MACD',
                    'params': {
                        'fast': 12,
                        'slow': 26,
                        'signal': 9
                    }
                },
                {
                    'name': 'RSI',
                    'params': {
                        'period': 14
                    }
                },
                {
                    'name': 'KDJ',
                    'params': {
                        'n': 9,
                        'm1': 3,
                        'm2': 3
                    }
                }
            ],
            'filters': {
                'min_price': float(os.getenv('MIN_PRICE', '5.0')),
                'max_price': float(os.getenv('MAX_PRICE', '1000.0')),
                'min_volume': int(os.getenv('MIN_VOLUME', '1000000')),
                'min_market_cap': int(os.getenv('MIN_MARKET_CAP', '1000000000'))
            }
        },
        
        # 回测配置
        'backtest': {
            'start_date': os.getenv('BACKTEST_START_DATE', '2023-01-01'),
            'end_date': os.getenv('BACKTEST_END_DATE', '2024-12-31'),
            'initial_cash': float(os.getenv('BACKTEST_INITIAL_CASH', '100000.0')),
            'commission': float(os.getenv('BACKTEST_COMMISSION', '0.0003')),
            'stamp_duty': float(os.getenv('BACKTEST_STAMP_DUTY', '0.001')),
            'position_size': float(os.getenv('BACKTEST_POSITION_SIZE', '0.2'))
        },
        
        # 报告生成配置
        'report': {
            'format': str_to_list(os.getenv('REPORT_FORMAT', 'html,json')),
            'output_path': os.getenv('REPORT_OUTPUT_PATH', 'data/reports/'),
            'top_n': int(os.getenv('TOP_N_STOCKS', '10')),
            'include_charts': str_to_bool(os.getenv('REPORT_INCLUDE_CHARTS', 'true'))
        },
        
        # 通知推送配置
        'notification': {
            'enabled_channels': [],
            'email': {},
            'wechat': {},
            'dingtalk': {}
        },
        
        # 日志配置
        'logging': {
            'level': os.getenv('LOG_LEVEL', 'INFO'),
            'log_file': os.getenv('LOG_FILE', 'logs/trading_tips.log'),
            'max_size': os.getenv('LOG_MAX_SIZE', '10MB'),
            'backup_count': int(os.getenv('LOG_BACKUP_COUNT', '5'))
        }
    }
    
    # 配置邮件推送
    if str_to_bool(os.getenv('EMAIL_ENABLED', 'false')):
        config['notification']['enabled_channels'].append('email')
        config['notification']['email'] = {
            'smtp_server': os.getenv('EMAIL_SMTP_SERVER', ''),
            'smtp_port': int(os.getenv('EMAIL_SMTP_PORT', '587')),
            'use_tls': str_to_bool(os.getenv('EMAIL_USE_TLS', 'true')),
            'username': os.getenv('EMAIL_USERNAME', ''),
            'password': os.getenv('EMAIL_PASSWORD', ''),
            'from_addr': os.getenv('EMAIL_FROM', ''),
            'to_addrs': str_to_list(os.getenv('EMAIL_TO', ''))
        }
    
    # 配置微信推送
    if str_to_bool(os.getenv('WECHAT_ENABLED', 'false')):
        config['notification']['enabled_channels'].append('wechat')
        config['notification']['wechat'] = {
            'webhook_url': os.getenv('WECHAT_WEBHOOK_URL', '')
        }
    
    # 配置钉钉推送
    if str_to_bool(os.getenv('DINGTALK_ENABLED', 'false')):
        config['notification']['enabled_channels'].append('dingtalk')
        config['notification']['dingtalk'] = {
            'webhook_url': os.getenv('DINGTALK_WEBHOOK_URL', ''),
            'secret': os.getenv('DINGTALK_SECRET', '')
        }
    
    # 配置推送时间
    config['notification']['schedule'] = {
        'time': os.getenv('NOTIFICATION_TIME', '09:00'),
        'frequency': os.getenv('NOTIFICATION_FREQUENCY', 'daily')
    }
    
    logger.info(f"配置加载完成，数据源: {config['data_source']['provider']}")
    logger.info(f"启用的推送渠道: {config['notification']['enabled_channels']}")
    
    return config


def validate_config(config: Dict[str, Any]) -> bool:
    """
    验证配置是否有效
    
    Args:
        config: 配置字典
        
    Returns:
        bool: 配置是否有效
    """
    # 检查必需的配置项
    required_fields = [
        ('data_source', 'api_key'),
    ]
    
    for fields in required_fields:
        current = config
        for field in fields:
            if field not in current or not current[field]:
                logger.warning(f"缺少必需的配置项: {'.'.join(fields)}")
                return False
            current = current[field]
    
    logger.info("配置验证通过")
    return True


def print_config_example():
    """
    打印环境变量配置示例
    """
    example = """
# 青龙面板环境变量配置示例

# 数据源配置
export DATA_SOURCE_PROVIDER="tushare"
export DATA_SOURCE_API_KEY="your_tushare_token_here"

# 推荐数量
export TOP_N_STOCKS="10"

# 邮件推送配置
export EMAIL_ENABLED="true"
export EMAIL_SMTP_SERVER="smtp.gmail.com"
export EMAIL_SMTP_PORT="587"
export EMAIL_USERNAME="your_email@gmail.com"
export EMAIL_PASSWORD="your_password"
export EMAIL_FROM="your_email@gmail.com"
export EMAIL_TO="recipient1@example.com,recipient2@example.com"

# 微信推送配置（Server酱）
export WECHAT_ENABLED="true"
export WECHAT_WEBHOOK_URL="https://sc.ftqq.com/your_key.send"

# 钉钉推送配置
export DINGTALK_ENABLED="true"
export DINGTALK_WEBHOOK_URL="https://oapi.dingtalk.com/robot/send?access_token=your_token"
export DINGTALK_SECRET="your_secret"

# 日志配置
export LOG_LEVEL="INFO"
    """
    print(example)
