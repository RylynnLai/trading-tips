# 青龙面板使用指南

本文档介绍如何在青龙面板中添加和使用证券交易推荐系统订阅。

## 目录

- [什么是青龙面板](#什么是青龙面板)
- [添加订阅](#添加订阅)
- [配置环境变量](#配置环境变量)
- [设置定时任务](#设置定时任务)
- [查看运行日志](#查看运行日志)
- [常见问题](#常见问题)

## 什么是青龙面板

青龙面板是一个定时任务管理平台，支持Python、JavaScript、Shell等多种脚本语言。通过青龙面板，您可以轻松管理定时任务，实现自动化运行。

## 添加订阅

### 方法一：通过订阅链接添加

1. 登录青龙面板
2. 进入「订阅管理」页面
3. 点击「新建订阅」
4. 填写以下信息：
   - **名称**：证券交易推荐系统
   - **类型**：公开仓库
   - **链接**：`https://github.com/RylynnLai/trading-tips.git`
   - **分支**：`main`
   - **定时规则**：`0 9 * * *`（每天早上9点执行）
   - **拉取文件**：`ql_task.py`

5. 点击「确定」保存

### 方法二：手动拉取

```bash
# 进入青龙面板的scripts目录
cd /ql/scripts

# 克隆项目
git clone https://github.com/RylynnLai/trading-tips.git

# 安装依赖
cd trading-tips
pip3 install -r requirements.txt
```

## 配置环境变量

在青龙面板中配置环境变量：

### 必需配置

| 环境变量 | 说明 | 示例值 |
|---------|------|--------|
| `DATA_SOURCE_API_KEY` | 数据源API密钥 | `your_tushare_token` |

### 可选配置

#### 数据源配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `DATA_SOURCE_PROVIDER` | 数据源提供商（akshare/yfinance/twelvedata） | `tushare` |
| `DATA_SOURCE_API_KEY` | 数据源API密钥（twelvedata需要） | - |
| `TOP_N_STOCKS` | 推荐股票数量 | `10` |

**数据源说明：**
- `akshare`: 免费，无需API key，支持A股、港股、基金
- `yfinance`: 免费，无需API key，支持全球市场
- `twelvedata`: 需要API key（免费版800次/天），支持全球股票、外汇、加密货币

#### 邮件推送配置

| 环境变量 | 说明 | 示例值 |
|---------|------|--------|
| `EMAIL_ENABLED` | 是否启用邮件 | `true` |
| `EMAIL_SMTP_SERVER` | SMTP服务器 | `smtp.gmail.com` |
| `EMAIL_SMTP_PORT` | SMTP端口 | `587` |
| `EMAIL_USERNAME` | 邮箱账号 | `your@email.com` |
| `EMAIL_PASSWORD` | 邮箱密码 | `your_password` |
| `EMAIL_FROM` | 发件人地址 | `your@email.com` |
| `EMAIL_TO` | 收件人地址（逗号分隔） | `user1@email.com,user2@email.com` |

#### 微信推送配置

| 环境变量 | 说明 | 示例值 |
|---------|------|--------|
| `WECHAT_ENABLED` | 是否启用微信推送 | `true` |
| `WECHAT_WEBHOOK_URL` | 微信webhook URL | `https://sc.ftqq.com/your_key.send` |

#### 钉钉推送配置

| 环境变量 | 说明 | 示例值 |
|---------|------|--------|
| `DINGTALK_ENABLED` | 是否启用钉钉推送 | `true` |
| `DINGTALK_WEBHOOK_URL` | 钉钉webhook URL | `https://oapi.dingtalk.com/robot/send?access_token=xxx` |
| `DINGTALK_SECRET` | 钉钉加签密钥 | `SECxxxxxxxxxxxx` |

#### 其他配置

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `LOG_LEVEL` | 日志级别 | `INFO` |
| `BACKTEST_DAYS` | 回测天数 | `365` |

### 配置步骤

1. 在青龙面板中，进入「环境变量」页面
2. 点击「新建变量」
3. 按照上述表格填写变量名和值
4. 点击「确定」保存

## 设置定时任务

### 创建定时任务

1. 进入「定时任务」页面
2. 点击「新建任务」
3. 填写以下信息：
   - **任务名称**：证券推荐
   - **命令**：`task trading-tips/ql_task.py` 或 `python3 /ql/scripts/trading-tips/ql_task.py`
   - **定时规则**：`0 9 * * *`（每天早上9点）
4. 点击「确定」保存

### 定时规则说明

定时规则使用 Cron 表达式：

```
* * * * *
│ │ │ │ │
│ │ │ │ └─── 星期几 (0-7, 0和7都表示周日)
│ │ │ └───── 月份 (1-12)
│ │ └─────── 日期 (1-31)
│ └───────── 小时 (0-23)
└─────────── 分钟 (0-59)
```

**常用示例**：

- `0 9 * * *` - 每天早上9点执行
- `0 9 * * 1-5` - 工作日早上9点执行
- `0 9,15 * * *` - 每天早上9点和下午3点执行
- `0 */6 * * *` - 每6小时执行一次

## 查看运行日志

1. 在「定时任务」页面找到对应任务
2. 点击「日志」按钮查看运行日志
3. 也可以在服务器上查看日志文件：`/ql/scripts/trading-tips/logs/trading_tips.log`

## 常见问题

### 1. 如何获取数据源API密钥？

**Tushare**：
1. 访问 [Tushare官网](https://tushare.pro/)
2. 注册账号并登录
3. 在个人中心获取API Token
4. 将Token配置到环境变量 `DATA_SOURCE_API_KEY`

### 2. 任务执行失败怎么办？

1. 检查环境变量是否配置正确
2. 查看日志文件确认错误信息
3. 确认依赖包是否正确安装：`pip3 list | grep -E "pandas|numpy|requests"`
4. 手动执行测试：`python3 /ql/scripts/trading-tips/ql_task.py`

### 3. 如何测试推送是否正常？

可以先配置一个推送渠道（如Server酱微信推送），然后手动运行任务测试：

```bash
cd /ql/scripts/trading-tips
python3 ql_task.py
```

查看是否收到推送消息。

### 4. 如何更新订阅？

在青龙面板的「订阅管理」页面，点击对应订阅的「运行」按钮，即可拉取最新代码。

### 5. 依赖安装失败怎么办？

尝试手动安装：

```bash
cd /ql/scripts/trading-tips
pip3 install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 6. 如何修改推荐数量？

在环境变量中设置 `TOP_N_STOCKS`，例如推荐15只股票：

```
TOP_N_STOCKS=15
```

## 高级配置

### 自定义回测参数

```bash
# 回测起始日期
export BACKTEST_START_DATE="2023-01-01"

# 回测结束日期  
export BACKTEST_END_DATE="2024-12-31"

# 初始资金
export BACKTEST_INITIAL_CASH="100000"

# 手续费率
export BACKTEST_COMMISSION="0.0003"

# 印花税率
export BACKTEST_STAMP_DUTY="0.001"
```

### 自定义筛选条件

```bash
# 最低价格
export MIN_PRICE="5.0"

# 最高价格
export MAX_PRICE="1000.0"

# 最小成交量
export MIN_VOLUME="1000000"

# 最小市值
export MIN_MARKET_CAP="1000000000"
```

## 技术支持

如有问题，欢迎提交Issue：https://github.com/RylynnLai/trading-tips/issues
