# 主程序使用指南

## 快速开始

### 1. 基本使用

```bash
# 使用本地数据运行（推荐）
python run.py --local

# 指定配置文件
python run.py --config config/config.yaml

# 使用在线API获取数据
python run.py
```

### 2. 常用参数

```bash
# 分析30只股票，最低推荐分数60
python run.py --local --max-stocks 30 --min-score 60

# 启用通知推送
python run.py --local --notify

# 启用回测
python run.py --local --backtest

# 组合使用
python run.py --local --max-stocks 50 --min-score 70 --notify
```

### 3. 参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--config` | 配置文件路径 | `config/config.yaml` |
| `--local` | 使用本地数据 | false（使用API） |
| `--max-stocks` | 最大分析股票数量 | 配置文件中的值 |
| `--min-score` | 最低推荐分数（0-100） | 配置文件中的值 |
| `--notify` | 启用通知推送 | false |
| `--backtest` | 启用回测 | false |

## 完整工作流程

### 步骤1：下载数据

```bash
# 下载800只A股数据（排除ST）
python download_stock_data.py --num 800 -y

# 验证数据
python download_stock_data.py --verify-only
```

### 步骤2：配置系统

编辑 `config/config.yaml`：

```yaml
# 数据源配置
data_source:
  use_local_data: true  # 使用本地数据
  local_data_dir: "~/.qlib/qlib_data/cn_data"

# 分析配置
analysis:
  max_stocks: 100      # 最大分析数量
  min_score: 60        # 最低推荐分数
  max_recommendations: 20  # 最多推荐数量
  
  trend_strategy:
    ma_periods: [20, 60, 120]  # 均线周期
    min_data_points: 60        # 最少数据点

# 报告配置
report:
  format: ["markdown", "json"]  # 报告格式
  output_path: "data/reports/"  # 输出路径

# 通知配置
notification:
  enabled: false  # 是否启用
  enabled_channels:
    - feishu
```

### 步骤3：运行分析

```bash
# 基础运行
python run.py --local

# 高质量推荐（更严格过滤）
python run.py --local --max-stocks 100 --min-score 70

# 快速扫描（分析更多，要求较低）
python run.py --local --max-stocks 200 --min-score 50
```

### 步骤4：查看报告

报告会自动生成在 `data/reports/` 目录：

```bash
# 查看最新的JSON报告
cat data/reports/trend_following_*.json | python -m json.tool

# 查看推荐总结
python run.py --local 2>&1 | grep "推荐"
```

## 程序执行流程

```
1. 数据获取
   ├─ 本地数据：从 ~/.qlib/qlib_data/cn_data/ 加载CSV
   └─ 在线数据：通过AKShare API获取

2. 趋势分析
   ├─ 计算技术指标（MA、EMA、ATR等）
   ├─ 趋势分类（5种趋势类型）
   ├─ 信号检测（突破、回调、2B结构）
   └─ 生成推荐（评分0-100）

3. 结果过滤
   ├─ 最低分数过滤
   ├─ 按得分排序
   └─ 限制推荐数量

4. 回测验证（可选）
   └─ 历史数据回测

5. 生成报告
   ├─ JSON格式（详细数据）
   └─ Markdown格式（可读性强）

6. 推送通知（可选）
   ├─ 飞书
   ├─ 钉钉
   └─ 邮件
```

## 输出示例

### 控制台输出

```
2026-02-23 19:22:14 | INFO  | 步骤1: 获取证券数据
2026-02-23 19:22:14 | INFO  | 从本地目录加载数据: ~/.qlib/qlib_data/cn_data
2026-02-23 19:22:14 | INFO  | 成功获取 30 只股票的数据
2026-02-23 19:22:14 | INFO  | 步骤2: 执行数据分析
2026-02-23 19:22:14 | INFO  | 分析完成，生成 6 个推荐
2026-02-23 19:22:14 | INFO  | 步骤4: 生成分析报告
2026-02-23 19:22:14 | INFO  | 报告生成完成: data/reports/trend_following_20260223_192214.json
2026-02-23 19:22:14 | INFO  | ✅ 程序执行成功
```

### JSON报告示例

```json
{
  "report_name": "trend_following_20260223_192214",
  "strategy_name": "trend_following",
  "generated_at": "2026-02-23T19:22:14",
  "recommendations": [
    {
      "symbol": "300724",
      "strategy": "加速行情-持有",
      "score": 50,
      "current_price": 122.7,
      "trend_type": "加速上涨",
      "ma_alignment": "bull",
      "entry_signal": "不建议追高",
      "hold_signal": "已有持仓继续持有",
      "reasons": [
        "加速上涨中",
        "尚未出现顶部构造",
        "乖离率22.2%，未到极端"
      ]
    }
  ]
}
```

## 常见问题

### Q1: 无推荐结果？

检查最低分数设置是否太高：
```bash
# 降低最低分数
python run.py --local --min-score 40
```

### Q2: 分析速度慢？

减少分析股票数量：
```bash
# 只分析50只
python run.py --local --max-stocks 50
```

### Q3: 想要更多推荐？

调整配置文件中的 `max_recommendations`，或降低 `min_score`。

### Q4: 如何启用通知？

1. 配置飞书Webhook（见 `docs/feishu_notification_guide.md`）
2. 运行时添加 `--notify` 参数

```bash
python run.py --local --notify
```

## 定时任务

### Linux/macOS (cron)

```bash
# 编辑crontab
crontab -e

# 每天15:30运行
30 15 * * * cd /path/to/trading-tips && source .venv/bin/activate && python run.py --local --notify
```

### 青龙面板

1. 上传 `ql_task.py` 和 `ql.json`
2. 在青龙面板添加定时任务
3. 配置环境变量（飞书Webhook等）

详见：`docs/QINGLONG.md`

## 高级用法

### 自定义策略

修改 `src/analysis/trend_strategy.py` 中的评分逻辑：

```python
def _recommend_breakout(self, symbol, df, trend_info, signals):
    score = 70  # 基础分数
    
    # 自定义评分逻辑
    if trend_info['ma_alignment'] == 'bull':
        score += 10
    if some_custom_condition:
        score += 20
    
    return score
```

### 批量测试

创建测试脚本：

```python
from src.main import TradingTipsApp

# 测试不同参数组合
configs = [
    {'max_stocks': 50, 'min_score': 60},
    {'max_stocks': 100, 'min_score': 70},
    {'max_stocks': 200, 'min_score': 50},
]

for cfg in configs:
    app = TradingTipsApp()
    app.config['analysis'].update(cfg)
    app.run()
```

## 下一步

- [ ] 配置飞书通知推送
- [ ] 添加更多技术指标
- [ ] 实现回测功能
- [ ] 添加可视化图表
- [ ] 集成到青龙面板

完整文档：
- 趋势分析指南：`docs/TREND_ANALYSIS_GUIDE.md`
- 数据源说明：`docs/DATA_SOURCE.md`
- 飞书通知配置：`docs/feishu_notification_guide.md`
