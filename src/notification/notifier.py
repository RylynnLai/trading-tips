"""
通知推送器

支持多种推送渠道：邮件、微信、钉钉、飞书等
"""

from typing import Dict, List, Optional
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
import requests
import hashlib
import time
import base64
import hmac
import json
from loguru import logger


class Notifier:
    """
    通知推送器基类
    """
    
    def __init__(self, config: Dict):
        """
        初始化通知推送器
        
        Args:
            config: 配置字典
        """
        self.config = config
        self.enabled_channels = config.get('enabled_channels', [])
        logger.info(f"初始化通知推送器，启用渠道: {self.enabled_channels}")
    
    def send(self, message: str, title: str = "证券推荐") -> bool:
        """
        发送通知
        
        Args:
            message: 消息内容
            title: 消息标题
            
        Returns:
            bool: 是否发送成功
        """
        # TODO: 实现通知发送
        pass


class EmailNotifier(Notifier):
    """
    邮件通知器
    """
    
    def __init__(self, config: Dict):
        """
        初始化邮件通知器
        
        Args:
            config: 邮件配置字典
        """
        super().__init__(config)
        email_config = config.get('email', {})
        self.smtp_server = email_config.get('smtp_server')
        self.smtp_port = email_config.get('smtp_port', 587)
        self.use_tls = email_config.get('use_tls', True)
        self.username = email_config.get('username')
        self.password = email_config.get('password')
        self.from_addr = email_config.get('from_addr')
        self.to_addrs = email_config.get('to_addrs', [])
        
        logger.info(f"初始化邮件通知器，SMTP服务器: {self.smtp_server}")
    
    def send(self, message: str, title: str = "证券推荐", 
             html_content: str = None, 
             attachments: List[str] = None) -> bool:
        """
        发送邮件
        
        Args:
            message: 邮件正文（纯文本）
            title: 邮件主题
            html_content: HTML格式的邮件内容
            attachments: 附件文件路径列表
            
        Returns:
            bool: 是否发送成功
        """
        # TODO: 实现邮件发送逻辑
        logger.info(f"发送邮件: {title}")
        
        try:
            # 创建邮件对象
            msg = MIMEMultipart('alternative')
            msg['Subject'] = title
            msg['From'] = self.from_addr
            msg['To'] = ', '.join(self.to_addrs)
            
            # 添加纯文本内容
            # TODO: 实现邮件内容添加
            
            # 添加HTML内容
            # TODO: 实现HTML内容添加
            
            # 添加附件
            # TODO: 实现附件添加
            
            # 发送邮件
            # TODO: 实现SMTP发送
            
            logger.info("邮件发送成功")
            return True
            
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False
    
    def _connect_smtp(self) -> smtplib.SMTP:
        """
        连接SMTP服务器
        
        Returns:
            SMTP: SMTP连接对象
        """
        # TODO: 实现SMTP连接
        pass


class WeChatNotifier(Notifier):
    """
    微信通知器（通过Server酱等服务）
    """
    
    def __init__(self, config: Dict):
        """
        初始化微信通知器
        
        Args:
            config: 微信配置字典
        """
        super().__init__(config)
        wechat_config = config.get('wechat', {})
        self.webhook_url = wechat_config.get('webhook_url')
        
        logger.info("初始化微信通知器")
    
    def send(self, message: str, title: str = "证券推荐") -> bool:
        """
        发送微信通知
        
        Args:
            message: 消息内容（支持Markdown）
            title: 消息标题
            
        Returns:
            bool: 是否发送成功
        """
        # TODO: 实现微信推送
        logger.info(f"发送微信通知: {title}")
        
        try:
            # 构造请求数据
            data = {
                'text': title,
                'desp': message
            }
            
            # TODO: 发送HTTP请求
            
            logger.info("微信通知发送成功")
            return True
            
        except Exception as e:
            logger.error(f"微信通知发送失败: {e}")
            return False


class DingTalkNotifier(Notifier):
    """
    钉钉通知器
    """
    
    def __init__(self, config: Dict):
        """
        初始化钉钉通知器
        
        Args:
            config: 钉钉配置字典
        """
        super().__init__(config)
        dingtalk_config = config.get('dingtalk', {})
        self.webhook_url = dingtalk_config.get('webhook_url')
        self.secret = dingtalk_config.get('secret')
        
        logger.info("初始化钉钉通知器")
    
    def send(self, message: str, title: str = "证券推荐") -> bool:
        """
        发送钉钉通知
        
        Args:
            message: 消息内容（支持Markdown）
            title: 消息标题
            
        Returns:
            bool: 是否发送成功
        """
        # TODO: 实现钉钉推送
        logger.info(f"发送钉钉通知: {title}")
        
        try:
            # 计算签名
            timestamp = str(round(time.time() * 1000))
            sign = self._generate_sign(timestamp)
            
            # 构造请求URL
            webhook_url = f"{self.webhook_url}&timestamp={timestamp}&sign={sign}"
            
            # 构造请求数据
            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": title,
                    "text": message
                }
            }
            
            # TODO: 发送HTTP请求
            
            logger.info("钉钉通知发送成功")
            return True
            
        except Exception as e:
            logger.error(f"钉钉通知发送失败: {e}")
            return False
    
    def _generate_sign(self, timestamp: str) -> str:
        """
        生成钉钉机器人签名
        
        Args:
            timestamp: 时间戳
            
        Returns:
            str: 签名字符串
        """
        # TODO: 实现签名生成
        if not self.secret:
            return ""
        
        secret_enc = self.secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{self.secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, 
                            digestmod=hashlib.sha256).digest()
        sign = base64.b64encode(hmac_code).decode('utf-8')
        
        return sign


class FeishuNotifier(Notifier):
    """
    飞书通知器
    """
    
    def __init__(self, config: Dict):
        """
        初始化飞书通知器
        
        Args:
            config: 飞书配置字典
        """
        super().__init__(config)
        feishu_config = config.get('feishu', {})
        self.webhook_url = feishu_config.get('webhook_url')
        self.secret = feishu_config.get('secret', '')
        
        logger.info("初始化飞书通知器")
    
    def send(self, message: str, title: str = "证券推荐", 
             msg_type: str = "interactive") -> bool:
        """
        发送飞书通知
        
        Args:
            message: 消息内容
            title: 消息标题
            msg_type: 消息类型 (text/post/interactive)
            
        Returns:
            bool: 是否发送成功
        """
        logger.info(f"发送飞书通知: {title}")
        
        try:
            # 生成签名（如果配置了secret）
            timestamp = str(int(time.time()))
            sign = self._generate_sign(timestamp) if self.secret else None
            
            # 根据消息类型构造不同的请求数据
            if msg_type == "text":
                data = self._build_text_message(message, sign, timestamp)
            elif msg_type == "post":
                data = self._build_post_message(message, title, sign, timestamp)
            else:  # interactive (默认)
                data = self._build_interactive_message(message, title, sign, timestamp)
            
            # 发送HTTP请求
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                self.webhook_url,
                headers=headers,
                data=json.dumps(data),
                timeout=10
            )
            
            result = response.json()
            
            if result.get('code') == 0 or result.get('StatusCode') == 0:
                logger.info("飞书通知发送成功")
                return True
            else:
                logger.error(f"飞书通知发送失败: {result}")
                return False
            
        except Exception as e:
            logger.error(f"飞书通知发送失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def send_card(self, title: str, content_elements: List[Dict],
                  header_color: str = "blue") -> bool:
        """
        发送卡片消息
        
        Args:
            title: 卡片标题
            content_elements: 内容元素列表
            header_color: 标题背景色 (blue/wathet/turquoise/green/yellow/orange/red/carmine/violet/purple/indigo/grey)
            
        Returns:
            bool: 是否发送成功
        """
        logger.info(f"发送飞书卡片消息: {title}")
        
        try:
            # 生成签名
            timestamp = str(int(time.time()))
            sign = self._generate_sign(timestamp) if self.secret else None
            
            # 构造卡片消息
            data = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "tag": "plain_text",
                            "content": title
                        },
                        "template": header_color
                    },
                    "elements": content_elements
                }
            }
            
            # 添加签名
            if sign:
                data["timestamp"] = timestamp
                data["sign"] = sign
            
            # 发送HTTP请求
            headers = {'Content-Type': 'application/json'}
            response = requests.post(
                self.webhook_url,
                headers=headers,
                data=json.dumps(data),
                timeout=10
            )
            
            result = response.json()
            
            if result.get('code') == 0 or result.get('StatusCode') == 0:
                logger.info("飞书卡片消息发送成功")
                return True
            else:
                logger.error(f"飞书卡片消息发送失败: {result}")
                return False
            
        except Exception as e:
            logger.error(f"飞书卡片消息发送失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def send_report_card(self, strategy_name: str, 
                        recommendations: List[Dict],
                        portfolio_stats: Optional[Dict] = None) -> bool:
        """
        发送推荐报告卡片
        
        Args:
            strategy_name: 策略名称
            recommendations: 推荐列表
            portfolio_stats: 组合统计
            
        Returns:
            bool: 是否发送成功
        """
        elements = []
        
        # 添加统计信息
        if portfolio_stats:
            fields = []
            fields.append({
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**推荐数量**\n{portfolio_stats.get('portfolio_count', len(recommendations))}"
                }
            })
            fields.append({
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**平均波动率**\n{portfolio_stats.get('avg_volatility', 0):.2f}%"
                }
            })
            fields.append({
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": f"**平均动量**\n{portfolio_stats.get('avg_momentum', 0):.2f}%"
                }
            })
            
            if 'expected_annual_return' in portfolio_stats:
                fields.append({
                    "is_short": True,
                    "text": {
                        "tag": "lark_md",
                        "content": f"**预期年化收益**\n{portfolio_stats['expected_annual_return']}"
                    }
                })
            
            elements.append({
                "tag": "div",
                "fields": fields
            })
            
            # 添加分割线
            elements.append({
                "tag": "hr"
            })
        
        # 添加推荐列表
        for i, rec in enumerate(recommendations[:10], 1):  # 显示前10个
            # 推荐标题
            if i <= 3:
                rank_emoji = ["🥇", "🥈", "🥉"][i-1]
            else:
                rank_emoji = f"{i}️⃣"
            
            # 构建推荐内容
            symbol = rec.get('symbol', 'N/A')
            name = rec.get('name', symbol)
            score = rec.get('score', 0)
            current_price = rec.get('current_price', 0)
            action = rec.get('action', 'N/A')
            reason = rec.get('reason', 'N/A')
            
            content_lines = [
                f"{rank_emoji} **{name}** ({symbol})",
                f"📊 **推荐**: {action} | **得分**: {score:.1f}",
                f"💰 **当前价格**: ¥{current_price:.2f}",
            ]
            
            # 添加策略信息
            if rec.get('strategy'):
                content_lines.append(f"📈 **策略**: {rec['strategy']}")
            
            # 添加盈利预测信息（如果存在）
            profit_pred = rec.get('profit_prediction', {})
            if profit_pred:
                expected_return = profit_pred.get('expected_return_pct', 0)
                success_prob = profit_pred.get('success_probability_pct', 0)
                
                # 设置收益率颜色
                return_color = "green" if expected_return > 0 else "red"
                return_sign = "+" if expected_return > 0 else ""
                
                content_lines.append("")
                content_lines.append(f"💹 **盈利预测**:")
                content_lines.append(f"   预期收益: <font color='{return_color}'>{return_sign}{expected_return:.1f}%</font> | 成功率: {success_prob:.0f}%")
                
                # 目标价格
                targets = profit_pred.get('target_prices', {})
                if targets.get('conservative'):
                    content_lines.append(f"   保守目标: ¥{targets['conservative']:.2f}")
                if targets.get('moderate'):
                    content_lines.append(f"   适中目标: ¥{targets['moderate']:.2f}")
                if targets.get('aggressive'):
                    content_lines.append(f"   激进目标: ¥{targets['aggressive']:.2f}")
                
                # 止损价格
                if profit_pred.get('stop_loss'):
                    content_lines.append(f"   止损价: ¥{profit_pred['stop_loss']:.2f}")
            
            # 添加推荐理由
            if reason and reason != 'N/A':
                content_lines.append("")
                content_lines.append(f"📝 **理由**: {reason}")
            
            elements.append({
                "tag": "div",
                "text": {
                    "tag": "lark_md",
                    "content": "\n".join(content_lines)
                }
            })
            
            # 非最后一个添加分割线
            if i < min(len(recommendations), 10):
                elements.append({
                    "tag": "hr"
                })
        
        # 添加备注信息
        from datetime import datetime
        elements.append({
            "tag": "note",
            "elements": [
                {
                    "tag": "plain_text",
                    "content": f"⚠️ 投资有风险，入市需谨慎。本报告仅供参考，不构成投资建议。\n生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                }
            ]
        })
        
        # 发送卡片
        return self.send_card(
            title=f"📊 {strategy_name} - 推荐报告",
            content_elements=elements,
            header_color="blue"
        )
    
    def _build_text_message(self, message: str, sign: Optional[str], 
                           timestamp: str) -> Dict:
        """
        构建纯文本消息
        
        Args:
            message: 消息内容
            sign: 签名
            timestamp: 时间戳
            
        Returns:
            Dict: 消息数据
        """
        data = {
            "msg_type": "text",
            "content": {
                "text": message
            }
        }
        
        if sign:
            data["timestamp"] = timestamp
            data["sign"] = sign
        
        return data
    
    def _build_post_message(self, message: str, title: str,
                           sign: Optional[str], timestamp: str) -> Dict:
        """
        构建富文本消息
        
        Args:
            message: 消息内容
            title: 标题
            sign: 签名
            timestamp: 时间戳
            
        Returns:
            Dict: 消息数据
        """
        data = {
            "msg_type": "post",
            "content": {
                "post": {
                    "zh_cn": {
                        "title": title,
                        "content": [
                            [
                                {
                                    "tag": "text",
                                    "text": message
                                }
                            ]
                        ]
                    }
                }
            }
        }
        
        if sign:
            data["timestamp"] = timestamp
            data["sign"] = sign
        
        return data
    
    def _build_interactive_message(self, message: str, title: str,
                                   sign: Optional[str], timestamp: str) -> Dict:
        """
        构建交互式卡片消息
        
        Args:
            message: 消息内容
            title: 标题
            sign: 签名
            timestamp: 时间戳
            
        Returns:
            Dict: 消息数据
        """
        data = {
            "msg_type": "interactive",
            "card": {
                "header": {
                    "title": {
                        "tag": "plain_text",
                        "content": title
                    },
                    "template": "blue"
                },
                "elements": [
                    {
                        "tag": "div",
                        "text": {
                            "tag": "lark_md",
                            "content": message
                        }
                    }
                ]
            }
        }
        
        if sign:
            data["timestamp"] = timestamp
            data["sign"] = sign
        
        return data
    
    def _generate_sign(self, timestamp: str) -> str:
        """
        生成飞书机器人签名
        
        Args:
            timestamp: 时间戳
            
        Returns:
            str: 签名字符串
        """
        if not self.secret:
            return ""
        
        # 拼接timestamp和secret
        string_to_sign = f"{timestamp}\n{self.secret}"
        
        # 使用HmacSHA256算法计算签名
        hmac_code = hmac.new(
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256
        ).digest()
        
        # 对签名进行base64编码
        sign = base64.b64encode(hmac_code).decode('utf-8')
        
        return sign


class NotificationManager:
    """
    通知管理器
    
    管理多个通知渠道，统一发送通知
    """
    
    def __init__(self, config: Dict):
        """
        初始化通知管理器
        
        Args:
            config: 通知配置字典
        """
        self.config = config
        self.enabled_channels = config.get('enabled_channels', [])
        self.notifiers = []
        
        # 初始化各个通知器
        if 'email' in self.enabled_channels:
            self.notifiers.append(EmailNotifier(config))
        
        if 'wechat' in self.enabled_channels:
            self.notifiers.append(WeChatNotifier(config))
        
        if 'dingtalk' in self.enabled_channels:
            self.notifiers.append(DingTalkNotifier(config))
        
        if 'feishu' in self.enabled_channels:
            self.notifiers.append(FeishuNotifier(config))
        
        logger.info(f"通知管理器初始化完成，共{len(self.notifiers)}个通知渠道")
    
    def send_all(self, message: str, title: str = "证券推荐", **kwargs) -> Dict[str, bool]:
        """
        通过所有启用的渠道发送通知
        
        Args:
            message: 消息内容
            title: 消息标题
            **kwargs: 其他参数
            
        Returns:
            Dict: 各渠道发送结果 {channel: success}
        """
        results = {}
        
        for notifier in self.notifiers:
            channel_name = notifier.__class__.__name__
            try:
                success = notifier.send(message, title, **kwargs)
                results[channel_name] = success
            except Exception as e:
                logger.error(f"{channel_name} 发送失败: {e}")
                results[channel_name] = False
        
        logger.info(f"通知发送完成，成功: {sum(results.values())}/{len(results)}")
        return results
    
    def format_message(self, recommendations: List[Dict]) -> str:
        """
        格式化推荐消息
        
        Args:
            recommendations: 推荐列表
            
        Returns:
            str: 格式化后的消息
        """
        # TODO: 实现消息格式化
        logger.debug("格式化推荐消息")
        
        message = "# 今日股票推荐\n\n"
        # TODO: 添加推荐内容
        
        return message
