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

### 核心配置

| 环境变量 | 说明 | 默认值 | 必需 |
|---------|------|--------|------|
| `TASK_MODE` | 任务模式（full/quick/test） | `full` | 否 |
| `USE_LOCAL_DATA` | 是否使用本地数据 | `true` | 否 |
| `MAX_STOCKS` | 最大分析股票数量 | `100` | 否 |
| `MIN_SCORE` | 最低推荐分数（0-100） | `60` | 否 |
| `ENABLE_NOTIFICATION` | 是否启用通知推送 | `true` | 否 |
| `ENABLE_BACKTEST` | 是否启用回测验证 | `false` | 否 |
| `DEBUG_MODE` | 是否启用调试模式 | `false` | 否 |

**任务模式说明：**
- `full`: 完整模式 - 完整分析 + 回测验证 + 通知推送（推荐生产环境使用）
- `quick`: 快速模式 - 仅分析和推送，跳过回测（适合快速查看）
- `test`: 测试模式 - 仅分析少量股票，用于测试配置

### 必需配置

对于使用在线API的情况：

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

### 高级任务配置

支持在命令中直接传递参数，无需配置环境变量：

```bash
# 完整模式：分析100只股票，分数≥70，启用通知
python3 /ql/scripts/trading-tips/ql_task.py --mode full --max-stocks 100 --min-score 70 --notify

# 快速模式：分析50只股票，分数≥60
python3 /ql/scripts/trading-tips/ql_task.py --mode quick --max-stocks 50 --min-score 60

# 测试模式：仅分析10只股票，不发送通知
python3 /ql/scripts/trading-tips/ql_task.py --mode test --max-stocks 10 --no-notify

# 使用本地数据，启用回测
python3 /ql/scripts/trading-tips/ql_task.py --local --backtest --max-stocks 30

# 调试模式：输出详细日志
python3 /ql/scripts/trading-tips/ql_task.py --debug --mode test
```

**命令行参数说明：**

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--mode` | 任务模式（full/quick/test） | full |
| `--local` | 使用本地数据 | true |
| `--max-stocks` | 最大分析股票数量 | 100 |
| `--min-score` | 最低推荐分数 | 60 |
| `--notify` | 启用通知推送 | 启用 |
| `--no-notify` | 禁用通知推送 | - |
| `--backtest` | 启用回测验证 | 禁用 |
| `--no-backtest` | 禁用回测验证 | - |
| `--debug` | 启用调试模式 | 禁用 |

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

### 日志位置

1. **青龙面板日志**：在「定时任务」页面找到对应任务，点击「日志」按钮
2. **应用日志文件**：`/ql/scripts/trading-tips/logs/ql_task_YYYY-MM-DD.log`
3. **任务结果文件**：`/ql/scripts/trading-tips/data/task_results/ql_task_*.json`
4. **分析报告**：`/ql/scripts/trading-tips/data/reports/trend_following_*.json`

### 查看日志命令

```bash
# 查看今天的日志
cat /ql/scripts/trading-tips/logs/ql_task_$(date +%Y-%m-%d).log

# 实时查看日志
tail -f /ql/scripts/trading-tips/logs/ql_task_$(date +%Y-%m-%d).log

# 查看最新的任务结果
cat /ql/scripts/trading-tips/data/task_results/ql_task_*.json | tail -1 | python3 -m json.tool

# 查看最新的分析报告
cat /ql/scripts/trading-tips/data/reports/trend_following_*.json | tail -1 | python3 -m json.tool
```

## 使用示例

### 场景一：每日股票推荐（生产环境）

**配置环境变量：**
```bash
TASK_MODE=full
USE_LOCAL_DATA=true
MAX_STOCKS=100
MIN_SCORE=70
ENABLE_NOTIFICATION=true
ENABLE_BACKTEST=false
```

**定时任务命令：**
```bash
python3 /ql/scripts/trading-tips/ql_task.py
```

**定时规则：** `0 9 * * 1-5`（工作日早上9点）

---

### 场景二：盘中快速检查

**直接运行命令：**
```bash
python3 /ql/scripts/trading-tips/ql_task.py --mode quick --max-stocks 50 --min-score 60
```

**定时规则：** `0 11,14 * * 1-5`（工作日上午11点和下午2点）

---

### 场景三：周末回测分析

**配置环境变量：**
```bash
TASK_MODE=full
ENABLE_BACKTEST=true
MAX_STOCKS=30
MIN_SCORE=65
```

**定时任务命令：**
```bash
python3 /ql/scripts/trading-tips/ql_task.py --backtest
```

**定时规则：** `0 10 * * 6`（每周六上午10点）

---

### 场景四：新手测试配置

**直接运行命令：**
```bash
# 测试模式：仅分析10只股票，不发送通知
python3 /ql/scripts/trading-tips/ql_task.py --mode test --no-notify --debug
```

手动执行一次，查看日志确认配置正确后，再设置为定时任务。

## 常见问题

### 1. 如何选择合适的任务模式？

- **full 模式**：适合生产环境，完整分析流程，结果最准确
- **quick 模式**：适合盘中快速查看，跳过耗时的回测
- **test 模式**：适合测试配置，仅分析少量股票

### 2. 本地数据和在线API有什么区别？

- **本地数据**（推荐）：
  - ✅ 速度快，不受API限制
  - ✅ 可离线运行
  - ❌ 需要预先下载数据
  - 适合：已有数据文件的情况

- **在线API**：
  - ✅ 实时数据
  - ✅ 无需预先准备
  - ❌ 受API调用限制
  - ❌ 需要网络连接
  - 适合：初次使用或需要实时数据

### 3. 如何获取数据源API密钥？

**AKShare**（推荐）：
- 免费，无需API密钥
- 支持A股、港股、基金等
- 设置：`DATA_SOURCE_PROVIDER=akshare`

**Tushare**：
1. 访问 [Tushare官网](https://tushare.pro/)
2. 注册账号并登录
3. 在个人中心获取API Token
4. 设置：`DATA_SOURCE_API_KEY=your_token`

**TwelveData**：
1. 访问 [TwelveData](https://twelvedata.com/)
2. 注册获取免费API密钥（800次/天）
3. 设置：`DATA_SOURCE_API_KEY=your_api_key`

### 4. 任务执行失败怎么办？

1. **查看日志**: 
   ```bash
   cat /ql/scripts/trading-tips/logs/ql_task_$(date +%Y-%m-%d).log
   ```

2. **检查环境变量**: 确认所有必需的环境变量已配置

3. **测试模式运行**:
   ```bash
   python3 /ql/scripts/trading-tips/ql_task.py --mode test --debug
   ```

4. **检查依赖**:
   ```bash
   pip3 list | grep -E "pandas|numpy|akshare"
   ```

5. **查看任务结果**:
   ```bash
   cat /ql/scripts/trading-tips/data/task_results/ql_task_*.json | tail -1 | python3 -m json.tool
   ```

### 5. 如何测试推送是否正常？

1. **配置一个推送渠道**（如钉钉或飞书）
2. **运行测试命令**:
   ```bash
   cd /ql/scripts/trading-tips
   python3 ql_task.py --mode test --notify
   ```
3. **查看是否收到推送消息**

### 6. 如何调整推荐条件？

通过环境变量调整：

```bash
# 提高推荐门槛
MIN_SCORE=75

# 增加推荐数量
TOP_N_STOCKS=20

# 扩大分析范围
MAX_STOCKS=200
```

或在命令行中直接指定：
```bash
python3 ql_task.py --max-stocks 200 --min-score 75
```

### 7. 任务结果在哪里查看？

1. **JSON格式报告**: `data/reports/trend_following_*.json`
2. **任务执行摘要**: `data/task_results/ql_task_*.json`
3. **日志文件**: `logs/ql_task_*.log`
4. **推送消息**: 检查配置的通知渠道（邮件、微信、钉钉等）

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
