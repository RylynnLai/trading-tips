# 证券交易推荐系统

一个自动化的证券交易分析和推荐系统，基于**价量时空交易系统**理论，通过趋势分析、回测验证，推送值得关注的证券信息。

## ✨ 核心特性

- 🎯 **趋势跟随策略**：基于均线密集突破、稳定趋势回调的完整交易系统
- 📊 **技术指标体系**：MA、EMA、抵扣价、乖离率、ATR、均线密集度等
- 🔍 **信号检测系统**：2B结构、突破信号、回调信号、顶底构造识别
- 📈 **智能评分系统**：0-100分综合评分，自动筛选高质量机会
- � **盈利预测功能**：目标价位、离场时机、盈亏比、成功率（**新增** ⭐）
- 🚪 **离场信号判断**：明确的出场条件，避免盲目持仓（**新增** ⭐）
- 💾 **本地数据支持**：800+A股历史数据，无需频繁调用API
- 📝 **多格式报告**：JSON + Markdown + HTML，易读易分享
- 📊 **详细推荐说明**：包含理由、操作建议、风险提示（**增强**）
- 📨 **多渠道推送**：飞书、钉钉、邮件等（可选）
- 🤖 **定时任务**：支持青龙面板订阅，自动执行

## 🚀 快速开始

### 1. 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd trading-tips

# 创建虚拟环境
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 2. 下载数据

```bash
# 下载800只A股数据（排除ST股票）
python download_stock_data.py --num 800 -y

# 验证数据
python download_stock_data.py --verify-only
```

### 3. 运行分析

```bash
# 基础运行（使用本地数据）
python run.py --local

# 指定参数运行
python run.py --local --max-stocks 50 --min-score 70

# 启用通知推送
python run.py --local --notify

# 查看帮助
python run.py --help
```

### 4. 查看结果

```bash
# 查看Markdown格式报告（易读版）
cat data/reports/trend_following_*.md | tail -1

# 或在VS Code中打开查看
code data/reports/trend_following_*.md

# 查看JSON格式（机器可读）
cat data/reports/trend_following_*.json | python -m json.tool

# 快速查看推荐摘要
python run.py --local 2>&1 | grep "推荐"
```

### 5. 调整参数获得更多推荐

```bash
# 如果推荐数量太少，可以降低评分阈值
python run.py --local --min-score 50

# 或扩大分析范围
python run.py --local --max-stocks 200 --min-score 55

# 查看详细说明
cat docs/RECOMMENDATION_GUIDE.md
```

## 📚 项目结构

```
trading-tips/
├── README.md                      # 项目说明文档
├── requirements.txt               # Python依赖包
├── run.py                        # 快速启动脚本
├── ql_task.py                    # 青龙面板任务脚本
├── ql.json                       # 青龙面板配置
├── download_stock_data.py        # 数据下载工具
├── config/
│   └── config.yaml              # 主配置文件
├── src/                         # 核心代码
│   ├── main.py                  # 主程序入口
│   ├── data_source/             # 数据源模块
│   │   ├── base_provider.py    # 数据提供者基类
│   │   ├── akshare_provider.py # AKShare数据提供者
│   │   └── data_fetcher.py     # 数据获取器
│   ├── analysis/                # 分析模块 ⭐核心
│   │   ├── indicators.py       # 技术指标计算
│   │   ├── trend_analyzer.py   # 趋势分析器
│   │   ├── signal_detector.py  # 信号检测器
│   │   ├── trend_strategy.py   # 趋势跟随策略
│   │   ├── profit_predictor.py # 盈利预测器
│   │   ├── base_strategy.py    # 策略基类
│   │   └── analyzer.py         # 分析器集成（可选）
│   ├── backtest/               # 回测模块
│   │   └── backtester.py       # 回测引擎
│   ├── report/                 # 报告生成模块
│   │   └── report_generator.py # 报告生成器
│   ├── notification/           # 通知推送模块
│   │   └── notifier.py         # 飞书/钉钉通知器
│   └── utils/                  # 工具模块
│       └── env_config.py       # 环境配置
├── scripts/                    # 辅助脚本
│   └── backtest_strategy.py    # 独立回测脚本
├── tests/                      # 测试代码
│   └── manual/                 # 手动测试脚本
├── data/
│   ├── reports/                # 分析报告输出
│   └── task_results/           # 任务结果
├── docs/                       # 文档目录
│   ├── MAIN_USAGE.md          # 主程序使用指南
│   ├── TREND_ANALYSIS_GUIDE.md # 趋势分析详细文档
│   ├── PROFIT_PREDICTION_GUIDE.md # 盈利预测指南
│   ├── RECOMMENDATION_GUIDE.md # 推荐说明指南
│   ├── DATA_SOURCE.md         # 数据源说明
│   ├── QINGLONG.md            # 青龙面板部署指南
│   ├── FEISHU_NOTIFICATION_SETUP.md # 飞书通知设置
│   └── archive/               # 历史文档归档
└── logs/                       # 日志文件目录
```

## 💡 功能模块详解

### 1. 数据源模块 (data_source)
- ✅ AKShare - A股实时数据（已实现）
- ✅ 本地CSV缓存 - 800+股票历史数据（已实现）
- ⏳ yfinance - 港股/美股数据（计划中）
- ⏳ twelvedata - 全球市场数据（计划中）

### 2. 趋势分析系统 ⭐核心功能

基于**价量时空交易系统**理论的完整实现：

**四大核心模块：**
1. **indicators.py** - 技术指标计算
   - MA/EMA均线系统
   - 抵扣价（预测均线方向的核心）
   - 乖离率、ATR波动率
   - 均线密集度、排列、斜率

2. **trend_analyzer.py** - 趋势分析
   - 5种趋势类型分类
   - 趋势阶段识别
   - 均线拐头预测
   - 均线密集区识别

3. **signal_detector.py** - 交易信号检测
   - 2B结构（趋势反转）
   - 突破信号（密集区突破）
   - 回调信号（趋势回撤）
   - 顶底构造识别

4. **trend_strategy.py** - 完整交易策略
   - 三大策略：突破、回调、持有
   - 智能评分系统（0-100分）
   - 批量股票筛选
   - 入场/止损/目标价位

**三大交易策略：**
- 🥇 **密集成交区突破**（最推荐）- 横盘突破，空间最大
- 🥈 **稳定趋势回调**（最稳健）- 趋势回调，风险最小  
- 🥉 **加速行情持有**（高风险）- 只持有不追高

### 3. 回测模块 (backtest)
- ⏳ 策略回测引擎（开发中）
- ⏳ 绩效指标计算（开发中）

### 4. 报告生成模块 (report)
- ✅ JSON格式报告（已实现）
- ✅ Markdown格式报告（已实现）
- ⏳ HTML可视化报告（计划中）

### 5. 通知推送模块 (notification)
- ✅ 飞书机器人（已实现）
- ⏳ 钉钉机器人（计划中）
- ⏳ 邮件通知（计划中）

## 📖 使用文档

### 必读文档

1. **[主程序使用指南](docs/MAIN_USAGE.md)** - 运行参数、工作流程、常见问题
2. **[趋势分析指南](docs/TREND_ANALYSIS_GUIDE.md)** - 策略详解、API文档、使用示例
3. **[推荐数量与评分说明](docs/RECOMMENDATION_GUIDE.md)** - 为什么推荐少？如何调整？
4. **[盈利预测与离场时机](docs/PROFIT_PREDICTION_GUIDE.md)** - 目标价位、离场信号、风险评估（**新增** ⭐）
5. **[数据源说明](docs/DATA_SOURCE.md)** - 数据获取、格式、配置

### 选读文档

6. **[报告生成改进说明](docs/REPORT_ENHANCEMENT.md)** - Markdown报告使用指南
7. **[飞书通知配置](docs/feishu_notification_guide.md)** - 推送配置教程
8. **[青龙面板集成](docs/QINGLONG.md)** - 定时任务配置
9. **[青龙面板增强功能](docs/QINGLONG_ENHANCEMENT.md)** - 最新功能说明

## 🎯 典型使用场景

### 场景1：每日选股推荐

```bash
# 分析100只股票，筛选得分≥70的机会
python run.py --local --max-stocks 100 --min-score 70

# 查看推荐
cat data/reports/trend_following_*.json | python -m json.tool
```

### 场景2：快速扫描机会

```bash
# 分析200只股票，筛选得分≥50的所有机会
python run.py --local --max-stocks 200 --min-score 50
```

### 场景3：高质量精选

```bash
# 分析50只股票，只筛选得分≥80的优质机会
python run.py --local --max-stocks 50 --min-score 80
```

### 场景4：定时推送（配合cron）

```bash
# crontab配置（每天15:30执行）
30 15 * * * cd /path/to/trading-tips && source .venv/bin/activate && python run.py --local --notify
```

## ⚙️ 配置说明

主配置文件：`config/config.yaml`

```yaml
# 数据源配置
data_source:
  use_local_data: true               # 使用本地数据
  local_data_dir: "~/.qlib/qlib_data/cn_data"

# 分析配置
analysis:
  max_stocks: 100                    # 最大分析数量
  min_score: 60                      # 最低推荐分数
  max_recommendations: 20            # 最多推荐数量
  
  trend_strategy:
    ma_periods: [20, 60, 120]       # 均线周期
    min_data_points: 60              # 最少数据点

# 报告配置
report:
  format: ["markdown", "json"]       # 报告格式
  output_path: "data/reports/"       # 输出路径

# 通知配置
notification:
  enabled: false                     # 是否启用
  enabled_channels: [feishu]         # 推送渠道
```

## 📊 输出示例

### 推荐结果

```json
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
```

## 🔧 开发指南

### 运行测试

```bash
# 测试本地数据
python test_local_data.py

# 测试数据源
python test_data_source.py

# 测试飞书通知
python test_feishu_notification.py
```

### 添加自定义策略

编辑 `src/analysis/trend_strategy.py`：

```python
def _recommend_custom(self, symbol, df, trend_info, signals):
    """自定义策略逻辑"""
    score = 60
    
    # 添加你的条件
    if your_condition:
        score += 20
    
    return {
        'symbol': symbol,
        'score': score,
        # ... 其他字段
    }
```

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

- [AKShare](https://github.com/akfamily/akshare) - 提供A股数据
- 价量时空交易系统理论
- 所有贡献者

---

**免责声明**：本系统仅供学习交流使用，不构成任何投资建议。股市有风险，投资需谨慎。

**三大交易策略：**
1. **密集成交区突破策略**（⭐⭐⭐最推荐）- 横盘突破，空间大
2. **稳定趋势回撤策略**（⭐⭐⭐最稳健）- 趋势回调，风险小
3. **斜率加速策略**（⭐高风险高收益）- 只持有不追高

**核心理念：**
- 抵扣价原理 - 预演均线未来走势的核心方法
- 均线密集 - 捕捉大行情的关键信号
- 不预测，只预演 - 用数学方法推演趋势

📖 **详细文档**：[趋势分析模块使用指南](docs/TREND_ANALYSIS_GUIDE.md)

#### 2.2 传统技术分析
- 技术指标分析（MACD、RSI、KDJ等）
- 基本面分析
- 量化策略分析
- 生成买入信号

### 3. 回测模块 (backtest)
- 历史数据回测
- 策略性能评估
- 风险评估

### 4. 分析结果生成模块 (report)
- 生成分析报告
- 可视化图表
- 推荐列表生成

### 5. 推送消息模块 (notification)
- 邮件推送
- 微信推送
- 钉钉推送
- 其他通知方式

## 快速开始

### 方式一：本地运行

#### 安装依赖
```bash
pip install -r requirements.txt
pip install scipy  # 趋势分析模块需要
```

#### 配置
编辑 `config/config.yaml` 文件，配置数据源、策略参数和推送方式。

#### 运行

**1. 运行主程序**
```bash
python src/main.py
```

**2. 运行趋势分析示例**（新）
```bash
python example_trend_analysis.py
```

示例功能：
- 单个股票的完整趋势分析
- 批量股票筛选和推荐
- ETF趋势分析和筛选

**3. 使用趋势分析模块**

```python
from src.data_source.data_fetcher import DataFetcher
from src.analysis.analyzer import TechnicalAnalyzer

# 获取数据
fetcher = DataFetcher({'provider': 'akshare'})
data = fetcher.get_stock_data('000001', '20230101', '20240223')

# 分析
analyzer = TechnicalAnalyzer({'ma_periods': [20, 60, 120]})
result = analyzer.comprehensive_analysis(data, '000001')

# 查看结果
print(f"趋势类型: {result['trend_analysis']['trend_type']}")
print(f"活跃信号: {result['signals']['active_signals']}")
```

更多示例请查看 [趋势分析模块使用指南](docs/TREND_ANALYSIS_GUIDE.md)

### 方式二：青龙面板（推荐）

支持在青龙面板中订阅运行，实现定时自动化执行。新增多种运行模式和灵活的参数配置。

#### 快速添加订阅

1. 登录青龙面板
2. 进入「订阅管理」，点击「新建订阅」
3. 填写以下信息：
   - **名称**：证券交易推荐系统
   - **链接**：`https://github.com/RylynnLai/trading-tips.git`
   - **分支**：`main`
   - **定时规则**：`0 9 * * 1-5`（工作日早上9点执行）
   - **拉取文件**：`ql_task.py`

#### 配置环境变量

在青龙面板的「环境变量」中添加：

```bash
# 核心配置
TASK_MODE=full                    # 任务模式: full/quick/test
USE_LOCAL_DATA=true               # 使用本地数据（推荐）
MAX_STOCKS=100                    # 最大分析股票数量
MIN_SCORE=60                      # 最低推荐分数（0-100）
ENABLE_NOTIFICATION=true          # 启用通知推送
ENABLE_BACKTEST=false             # 是否启用回测

# 数据源配置（使用在线API时需要）
DATA_SOURCE_PROVIDER=akshare      # 数据源: akshare（免费推荐）/tushare/twelvedata
DATA_SOURCE_API_KEY=              # API密钥（akshare不需要）

# 推送配置（可选）
EMAIL_ENABLED=false
WECHAT_ENABLED=false
DINGTALK_ENABLED=false
```

#### 任务模式说明

- **full 模式**：完整分析 + 回测验证 + 通知推送（生产推荐）
- **quick 模式**：快速分析 + 通知推送（跳过回测，适合盘中）
- **test 模式**：测试配置（仅分析10只股票，适合调试）

#### 高级用法：命令行参数

在青龙面板的定时任务中，可以直接使用命令行参数：

```bash
# 完整模式：分析100只股票，分数≥70
python3 ql_task.py --mode full --max-stocks 100 --min-score 70

# 快速模式：分析50只股票
python3 ql_task.py --mode quick --max-stocks 50 --min-score 60

# 测试模式：仅分析10只股票，不发送通知
python3 ql_task.py --mode test --no-notify --debug
```

#### 查看任务结果

任务执行后会生成详细的摘要和报告：

1. **青龙面板日志**：查看任务执行日志
2. **任务摘要**：`data/task_results/ql_task_*.json` - 包含统计信息
3. **分析报告**：`data/reports/trend_following_*.json` - 详细推荐数据
4. **应用日志**：`logs/ql_task_*.log` - 完整执行日志

📖 **详细文档**：[青龙面板使用指南](docs/QINGLONG.md)

## 开发计划2 - 报告生成增强
- ✨ **新增Markdown格式报告**：易读、美观、包含详细操作建议
- 📊 **增强报告内容**：推荐理由、技术信号、操作建议一目了然
- 📚 **新增推荐数量说明**：解释为什么推荐少及如何调整
- 💡 **智能推荐提示**："加速上涨-持有"等明确的操作建议
- 🎨 **美化报告格式**：使用表格、Emoji、清晰分段

#### v1.

- [x] 项目框架搭建
- [x] **趋势分析模块实现**（新）
  - [x] 技术指标计算器
  - [x] 趋势分析器
  - [x] 信号检测器
  - [x] 趋势跟随策略
  - [x] 完整示例代码
- [ ] 数据源模块优化
- [ ] 传统技术分析实现
- [ ] 回测模块实现
- [ ] 结果生成模块实现
- [ ] 推送模块实现

## 最新更新

### 2026-02-23

#### v1.1 - 青龙面板增强
- ✨ **新增任务模式**：full/quick/test 三种运行模式
- ✨ **命令行参数支持**：支持通过参数灵活控制执行
- ✨ **任务结果统计**：自动生成执行摘要和统计信息
- ✨ **增强日志系统**：按日期轮转，支持调试模式
- 📊 **任务结果持久化**：保存 JSON 格式的执行结果
- 📚 **完善青龙文档**：新增使用示例和场景说明

#### v1.0 - 趋势分析系统
- ✨ 实现完整的趋势分析系统
- ✨ 基于价量时空的三大交易策略
- ✨ 添加抵扣价原理、均线密集、2B结构等核心功能
- ✨ 提供批量股票筛选和推荐功能
- 📚 添加详细的使用指南和示例代码

## 注意事项

本系统仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。
