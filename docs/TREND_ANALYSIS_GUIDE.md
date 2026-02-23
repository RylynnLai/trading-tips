# 趋势分析模块使用指南

基于**价量时空交易系统**的完整趋势分析实现。

## 📋 模块概览

### 核心模块

| 模块 | 文件 | 功能 |
|------|------|------|
| **技术指标计算** | `indicators.py` | MA、EMA、抵扣价、乖离率、ATR、均线密集度等 |
| **趋势分析器** | `trend_analyzer.py` | 趋势分类、趋势阶段识别、均线拐头预判、目标位测算 |
| **信号检测器** | `signal_detector.py` | 2B结构、突破信号、回撤信号、顶底构造 |
| **趋势策略** | `trend_strategy.py` | 完整的趋势跟随策略，整合所有分析模块 |

### 整合模块

- `analyzer.py` - 已更新，集成了所有新模块
- `example_trend_analysis.py` - 完整示例代码

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

需要额外安装：
```bash
pip install scipy  # 用于信号检测中的波峰波谷识别
```

### 2. 基础使用

#### 单个股票分析

```python
from src.data_source.data_fetcher import DataFetcher
from src.analysis.analyzer import TechnicalAnalyzer

# 1. 获取数据
data_config = {'provider': 'akshare'}
fetcher = DataFetcher(data_config)
data = fetcher.get_stock_data('000001', '20230101', '20240223')

# 2. 创建分析器
analyzer_config = {
    'ma_periods': [20, 60, 120],
    'trend_analyzer': {
        'dense_threshold': 0.05,
        'accelerate_threshold': 0.8
    }
}
analyzer = TechnicalAnalyzer(analyzer_config)

# 3. 执行分析
result = analyzer.comprehensive_analysis(data, '000001')

# 4. 查看结果
print(f"趋势类型: {result['trend_analysis']['trend_type']}")
print(f"活跃信号: {result['signals']['active_signals']}")
```

#### 批量股票筛选

```python
from src.analysis.trend_strategy import TrendFollowingStrategy

# 1. 创建策略
strategy_config = {
    'ma_periods': [20, 60, 120],
    'min_score': 60,
    'max_recommendations': 20
}
strategy = TrendFollowingStrategy(strategy_config)

# 2. 准备数据（字典格式）
symbols_data = {
    '000001': df1,
    '600036': df2,
    # ...
}

# 3. 批量分析
recommendations = strategy.batch_analyze(symbols_data)

# 4. 查看推荐
for rec in recommendations:
    print(strategy.format_recommendation(rec))
```

## 📚 核心概念

### 1. 抵扣价原理（核心中的核心）

**什么是抵扣价？**

```python
# MA5的计算
MA5(明天) = (明天收盘 + 今天 + 昨天 + 前天 + 大前天) / 5
MA5(今天) = (今天收盘 + 昨天 + 前天 + 大前天 + 大大前天) / 5

# 如果要 MA5(明天) > MA5(今天)
# 只需要：明天收盘 > 大大前天收盘（抵扣价）
```

**如何使用？**

```python
from src.analysis.trend_analyzer import TrendAnalyzer

analyzer = TrendAnalyzer()
result = analyzer.check_ma_turning(data, period=20)

if result['can_turn_up']:
    print(f"当前价 {result['current_price']} > 抵扣价 {result['discount_price']}")
    print("MA20 即将向上拐头！")
```

### 2. 趋势分类（时钟方向法）

系统自动将趋势分为5类：

| 趋势类型 | 年化收益率 | 特征 | 操作策略 |
|---------|-----------|------|---------|
| **密集成交区** | - | 横盘6个月+，均线密集<5% | ⭐⭐⭐ 突破后买入 |
| **稳定上涨** | 15% ~ 80% | 多头排列，斜率稳定 | ⭐⭐⭐ 回撤买入 |
| **加速上涨** | > 80% | 多头排列，斜率加速 | ⭐ 持有不追高 |
| **稳定下跌** | -80% ~ -15% | 空头排列 | ❌ 不参与 |
| **加速下跌** | < -80% | 空头排列，加速 | ❌ 不参与 |

```python
from src.analysis.trend_analyzer import TrendAnalyzer

analyzer = TrendAnalyzer()
trend_type = analyzer.classify_trend(data)

print(f"趋势类型: {trend_type}")
# 输出示例：密集成交区 / 稳定上涨 / 加速上涨
```

### 3. 三大交易信号

#### 信号1：密集成交区突破

```python
from src.analysis.signal_detector import SignalDetector

detector = SignalDetector()
signal = detector.detect_breakout_signal(data)

if signal['has_signal']:
    print(f"突破信号强度: {signal['strength']}")
    print(f"均线密集度: {signal['ma_density']:.2f}%")
```

**特征：**
- ✅ 均线密集度 < 5%
- ✅ 刚刚形成多头排列
- ✅ 价格突破MA20
- ✅ 成交量放大

#### 信号2：稳定趋势回撤

```python
signal = detector.detect_pullback_signal(data)

if signal['has_signal']:
    print(f"回撤到: {signal['pullback_to']}")
    print(f"是否首次回撤: {signal['is_first_pullback']}")
```

**特征：**
- ✅ 完美多头排列
- ✅ 回撤到MA20/60/120
- ✅ 抵扣价安全（均线不会拐头）
- ✅ 第一次回撤（质量最好）

#### 信号3：2B结构（反转）

```python
signal = detector.detect_2b_structure(data)

if signal['has_2b']:
    if signal['bullish_2b']['found']:
        print("看涨2B结构：跌破前低后迅速拉回")
    if signal['bearish_2b']['found']:
        print("看跌2B结构：突破前高后迅速回落")
```

**特征：**
- 价格跌破（突破）前低（高）点
- 迅速回到前低（高）点上方（下方）
- ⚠️ 只是短期反弹/回调，不代表大趋势反转

## 🎯 策略使用

### 策略1：密集成交区突破策略

**适用场景：** 横盘6个月以上，即将突破

```python
from src.analysis.trend_strategy import TrendFollowingStrategy

strategy = TrendFollowingStrategy(config)
recommendations = strategy.batch_analyze(symbols_data)

# 筛选突破策略推荐
breakout_recs = [r for r in recommendations if r['strategy'] == '密集成交区突破']
```

**评分标准：**
- 均线密集 (30分)
- 多头排列 (25分 + 刚形成10分)
- 价格突破MA20 (15分)
- 成交量放大 (10分)
- 盈亏比>3 (20分)

**最低评分：** 60分

### 策略2：稳定趋势回撤策略

**适用场景：** 稳定上升趋势，回踩关键均线

```python
pullback_recs = [r for r in recommendations if r['strategy'] == '稳定趋势回撤']
```

**评分标准：**
- 多头排列 (20分)
- 回撤到MA120 (50分) / MA60 (40分) / MA20 (30分)
- 第一次回撤 (15分)
- 抵扣价安全 (10分)
- 双底构造 (15分)

**最低评分：** 60分

### 策略3：加速行情持有策略

**适用场景：** 已有持仓，加速上涨中

```python
hold_recs = [r for r in recommendations if '加速行情' in r['strategy']]
```

**特点：**
- 不建议追高
- 已有持仓继续持有
- 关注顶部构造和均线死叉
- 乖离率 > 50% 警惕

## 📊 完整示例

### 示例1：分析平安银行

```python
from src.data_source.data_fetcher import DataFetcher
from src.analysis.analyzer import TechnicalAnalyzer
from datetime import datetime, timedelta

# 1. 获取数据
fetcher = DataFetcher({'provider': 'akshare'})
data = fetcher.get_stock_data(
    '000001',
    (datetime.now() - timedelta(days=500)).strftime('%Y%m%d'),
    datetime.now().strftime('%Y%m%d')
)

# 2. 分析
analyzer = TechnicalAnalyzer({'ma_periods': [20, 60, 120]})
result = analyzer.comprehensive_analysis(data, '000001')

# 3. 查看结果
print(f"当前价格: {result['latest_price']:.2f}")
print(f"趋势类型: {result['trend_analysis']['trend_type']}")
print(f"均线排列: {result['trend_analysis']['ma_alignment']}")
print(f"活跃信号: {result['signals']['active_signals']}")

# 4. 目标位和止损
for target in result['trend_analysis'].get('targets', []):
    print(f"目标{target['level']}: {target['price']:.2f} (+{target['gain_pct']:.1f}%)")

stop_loss = result['trend_analysis']['stop_loss']
print(f"止损: {stop_loss['stop_loss']:.2f} (-{stop_loss['stop_loss_pct']:.1f}%)")
```

### 示例2：批量筛选沪深300

```python
from src.analysis.trend_strategy import TrendFollowingStrategy
import akshare as ak

# 1. 获取沪深300成分股
hs300 = ak.index_stock_cons_csindex(symbol="000300")
symbols = hs300['成分券代码'].tolist()

# 2. 批量获取数据
fetcher = DataFetcher({'provider': 'akshare'})
symbols_data = {}

for symbol in symbols[:50]:  # 限制50个
    data = fetcher.get_stock_data(symbol, '20230101', '20240223')
    if data is not None and len(data) >= 252:
        symbols_data[symbol] = data

# 3. 执行策略
strategy = TrendFollowingStrategy({
    'min_score': 70,  # 更严格的标准
    'max_recommendations': 10
})

recommendations = strategy.batch_analyze(symbols_data)

# 4. 打印推荐
for rec in recommendations:
    print(strategy.format_recommendation(rec))
```

## 🔧 配置参数

### TechnicalAnalyzer 配置

```python
config = {
    'ma_periods': [20, 60, 120],  # 均线周期
    'trend_analyzer': {
        'dense_threshold': 0.05,      # 密集区阈值 (5%)
        'accelerate_threshold': 0.8,  # 加速阈值 (80%年化)
        'stable_min': 0.15,           # 稳定趋势最小值 (15%年化)
        'stable_max': 0.8             # 稳定趋势最大值 (80%年化)
    },
    'signal_detector': {
        # 信号检测器配置（可选）
    }
}
```

### TrendFollowingStrategy 配置

```python
config = {
    'ma_periods': [20, 60, 120],
    'min_data_points': 252,        # 至少1年数据
    'min_score': 60,               # 最低推荐分数
    'max_recommendations': 20,     # 最多推荐数量
    'trend_analyzer': { ... },     # 同上
    'signal_detector': { ... }
}
```

## 📖 API 文档

### TechnicalIndicators

```python
from src.analysis.indicators import TechnicalIndicators

calc = TechnicalIndicators()

# 计算MA
df = calc.calculate_ma(data, periods=[20, 60, 120])

# 计算EMA
df = calc.calculate_ema(data, periods=[20, 60, 120])

# 计算抵扣价
df = calc.calculate_discount_price(data, periods=[20, 60, 120])

# 计算乖离率
df = calc.calculate_bias(data, periods=[20, 60, 120])

# 一站式计算所有指标
df = calc.calculate_all_indicators(data, ma_periods=[20, 60, 120])
```

### TrendAnalyzer

```python
from src.analysis.trend_analyzer import TrendAnalyzer

analyzer = TrendAnalyzer(config)

# 趋势分类
trend_type = analyzer.classify_trend(data)

# 趋势阶段
trend_phase = analyzer.identify_trend_phase(data)

# 均线拐头检查
ma_turn = analyzer.check_ma_turning(data, period=20)

# 找密集区
zones = analyzer.find_dense_zones(data)

# 计算目标位
targets = analyzer.calculate_target_price(data, current_price)

# 计算止损
stop_loss = analyzer.calculate_stop_loss(data, entry_price)

# 综合分析
result = analyzer.analyze_trend(data, symbol='000001')
```

### SignalDetector

```python
from src.analysis.signal_detector import SignalDetector

detector = SignalDetector(config)

# 检测2B结构
signal_2b = detector.detect_2b_structure(data)

# 检测突破信号
signal_breakout = detector.detect_breakout_signal(data)

# 检测回撤信号
signal_pullback = detector.detect_pullback_signal(data)

# 检测顶底构造
signal_structure = detector.detect_top_bottom_structure(data)

# 检测所有信号
all_signals = detector.detect_all_signals(data)
```

### TrendFollowingStrategy

```python
from src.analysis.trend_strategy import TrendFollowingStrategy

strategy = TrendFollowingStrategy(config)

# 分析单个标的
analyzed_data = strategy.analyze(data)
recommendations = strategy.generate_recommendations(analyzed_data)

# 批量分析
symbols_data = {'000001': df1, '600036': df2, ...}
recommendations = strategy.batch_analyze(symbols_data)

# 格式化推荐
text = strategy.format_recommendation(recommendation)
```

## 🎓 理论基础

本模块基于以下核心理论：

1. **价量时空交易系统** - 只关注最真实的数据
2. **抵扣价原理** - 预演均线未来走势
3. **趋势的五个阶段** - 转折→开始→发展→极端→转折
4. **均线密集** - 捕捉大行情的关键信号
5. **索罗斯反身性理论** - 市场非理性，人性之极是最佳机会

详细理论请参考：
- [价量时空交易系统_完整教学.md](../securities-data-sources/价量时空交易系统_完整教学.md)
- [趋势交易标的推荐策略.md](../securities-data-sources/趋势交易标的推荐策略.md)

## ⚠️ 风险提示

1. **历史数据不代表未来** - 任何策略都有失败的风险
2. **仓位管理** - 单笔仓位不超过20-30%
3. **严格止损** - 均线死叉必须止损
4. **盈亏比优先** - 至少3:1，最好10:1以上
5. **不追高** - 加速行情中不追高

## 📞 技术支持

- 问题反馈：请提交 Issue
- 文档完善：欢迎 PR

---

**最后更新**: 2026-02-23  
**版本**: v1.0
