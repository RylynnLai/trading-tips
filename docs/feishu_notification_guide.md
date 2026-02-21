# 飞书通知使用指南

## 功能介绍

飞书通知模块支持将证券推荐报告通过飞书机器人推送到飞书群聊，支持多种消息类型：

- ✅ 纯文本消息
- ✅ 富文本消息
- ✅ 交互式卡片消息（推荐）
- ✅ 自定义卡片消息
- ✅ 推荐报告卡片（专为股票推荐设计）

## 配置步骤

### 1. 在飞书群聊中添加自定义机器人

1. 打开飞书PC或移动端
2. 进入目标群聊
3. 点击群聊设置 → 群机器人 → 添加机器人
4. 选择"自定义机器人"
5. 配置机器人名称、描述和头像
6. （可选）启用"签名校验"以提高安全性
7. 复制生成的 Webhook 地址

### 2. 配置系统

编辑 `config/config.yaml` 文件：

```yaml
notification:
  # 启用飞书推送
  enabled_channels:
    - feishu
  
  # 飞书配置
  feishu:
    # 必填：Webhook地址
    webhook_url: "https://open.feishu.cn/open-apis/bot/v2/hook/YOUR_TOKEN_HERE"
    # 可选：如果启用了签名校验，填写密钥
    secret: ""
```

**获取Webhook地址：**
- 在添加机器人后，飞书会提供一个类似这样的URL：
  ```
  https://open.feishu.cn/open-apis/bot/v2/hook/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  ```
- 将完整URL复制到配置文件中的 `webhook_url` 字段

**（可选）配置签名校验：**
- 如果在添加机器人时启用了"签名校验"，将获得一个密钥
- 将密钥填入 `secret` 字段
- 如果未启用签名校验，`secret` 留空即可

## 使用示例

### 基础文本消息

```python
from src.notification.notifier import FeishuNotifier
import yaml

# 加载配置
with open('config/config.yaml', 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

# 初始化通知器
notifier = FeishuNotifier(config['notification'])

# 发送文本消息
notifier.send(
    message="这是一条测试消息",
    title="测试通知",
    msg_type="text"
)
```

### 富文本消息（支持Markdown）

```python
message = """
**今日市场概况**

📈 上证指数：+1.2%
📊 深证成指：+0.8%
💼 创业板指：+1.5%

市场整体表现良好！
"""

notifier.send(
    message=message,
    title="市场日报",
    msg_type="post"
)
```

### 交互式卡片消息（推荐）

```python
message = """
**系统运行状态**

✅ 数据源连接正常
✅ 策略计算完成
✅ 报告生成成功

所有模块运行正常！
"""

notifier.send(
    message=message,
    title="🎉 系统状态",
    msg_type="interactive"
)
```

### 推荐报告卡片（最常用）

```python
# 准备推荐数据
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
            '波动率较低，符合低波动策略',
            '近期动量强劲',
            '综合得分最高'
        ]
    },
    # ... 更多推荐
]

# 组合统计
portfolio_stats = {
    'portfolio_count': 5,
    'avg_volatility': 14.12,
    'avg_momentum': 5.84,
    'expected_annual_return': '15-20%'
}

# 发送推荐报告卡片
notifier.send_report_card(
    strategy_name="低波动轮动策略",
    recommendations=recommendations,
    portfolio_stats=portfolio_stats
)
```

### 使用通知管理器（多渠道推送）

```python
from src.notification.notifier import NotificationManager

# 初始化管理器（会自动加载所有启用的渠道）
manager = NotificationManager(config['notification'])

# 一次发送到所有渠道
results = manager.send_all(
    message="这是一条多渠道推送消息",
    title="通知标题"
)

# 查看结果
for channel, success in results.items():
    print(f"{channel}: {'成功' if success else '失败'}")
```

## 消息格式说明

### 推荐报告卡片格式

推荐报告卡片会包含以下内容：

**卡片头部：**
- 📊 蓝色背景
- 策略名称

**统计信息区（如果提供）：**
- 推荐数量
- 平均波动率
- 平均动量
- 预期年化收益

**推荐列表（最多显示前5个）：**
- 🥇🥈🥉 排名徽章
- 股票名称和代码
- 💰 当前价格
- ⭐ 综合得分
- 📊 波动率
- 📈 动量（绿色表示正，红色表示负）
- 💼 建议仓位
- 推荐理由（最多3条）

**底部备注：**
- ⚠️ 投资风险提示
- 生成时间

## 测试

运行测试脚本验证配置：

```bash
python test_feishu_notification.py
```

测试内容：
1. ✅ 文本消息发送
2. ✅ 富文本消息发送
3. ✅ 交互式卡片消息发送
4. ✅ 推荐报告卡片发送
5. ✅ 通知管理器多渠道发送

## 常见问题

### Q1: 收到"access token invalid"错误

**原因：** Webhook URL配置错误或已过期

**解决方法：**
1. 检查 `config/config.yaml` 中的 `webhook_url` 是否正确
2. 确认URL完整，包含 `https://open.feishu.cn/open-apis/bot/v2/hook/` 前缀
3. 在飞书群聊中重新创建机器人并获取新的Webhook地址

### Q2: 消息发送成功但群里看不到

**原因：** 可能是群聊权限问题或机器人被移除

**解决方法：**
1. 确认机器人仍在群聊中
2. 检查群聊设置中的机器人权限
3. 尝试重新添加机器人

### Q3: 签名校验失败

**原因：** `secret` 配置错误或时间不同步

**解决方法：**
1. 检查 `secret` 是否与飞书后台显示的一致
2. 确认系统时间准确（签名包含时间戳）
3. 如果不需要签名校验，可以在飞书机器人设置中关闭

### Q4: 卡片格式显示异常

**原因：** 数据格式不符合预期

**解决方法：**
1. 确保 `recommendations` 列表中每个元素包含必要字段
2. 检查数值类型（score、volatility、momentum等应为数字）
3. 参考测试脚本中的数据格式

## 高级功能

### 自定义卡片元素

```python
# 自定义卡片内容
elements = [
    {
        "tag": "div",
        "text": {
            "tag": "lark_md",
            "content": "**自定义标题**\n这是自定义内容"
        }
    },
    {
        "tag": "hr"  # 分割线
    },
    {
        "tag": "div",
        "fields": [
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": "**字段1**\n值1"
                }
            },
            {
                "is_short": True,
                "text": {
                    "tag": "lark_md",
                    "content": "**字段2**\n值2"
                }
            }
        ]
    }
]

# 发送自定义卡片
notifier.send_card(
    title="自定义卡片标题",
    content_elements=elements,
    header_color="blue"  # 可选：blue/green/red/orange等
)
```

### 支持的卡片颜色

- `blue` - 蓝色（默认）
- `wathet` - 浅蓝色
- `turquoise` - 青绿色
- `green` - 绿色
- `yellow` - 黄色
- `orange` - 橙色
- `red` - 红色
- `carmine` - 紫红色
- `violet` - 紫罗兰色
- `purple` - 紫色
- `indigo` - 靛蓝色
- `grey` - 灰色

## 最佳实践

1. **使用卡片消息**：推荐使用交互式卡片消息，视觉效果更好
2. **合理控制推送频率**：避免频繁推送打扰用户
3. **启用签名校验**：提高安全性，防止恶意请求
4. **错误处理**：发送失败时记录日志，便于排查问题
5. **测试先行**：使用测试脚本验证配置后再正式使用

## API参考

完整API文档请参考 `src/notification/notifier.py` 中的 `FeishuNotifier` 类。

主要方法：
- `send()` - 发送基础消息
- `send_card()` - 发送自定义卡片
- `send_report_card()` - 发送推荐报告卡片
