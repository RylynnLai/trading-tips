# 数据源模块说明

## 概述

数据源模块提供了统一的接口来获取各种证券数据，支持多个数据源，包括 AkShare 和 YFinance。

## 支持的数据源

### 1. AkShare

**特点**：
- ✅ 免费、开源
- ✅ 无需 API key
- ✅ 主要支持A股、港股市场
- ✅ 数据全面，包括股票、基金、指数等
- ⚠️ 数据更新可能有延迟

**使用场景**：
- A股市场数据获取
- 基金净值查询
- 港股行情

**示例代码**：
```python
from src.data_source import DataFetcher

config = {
    'provider': 'akshare',
    'cache': {'enabled': True}
}

fetcher = DataFetcher(config)

# 获取A股股票列表
stock_list = fetcher.fetch_stock_list('A')

# 获取股票历史数据
data = fetcher.fetch_stock_data('000001', '2024-01-01', '2024-12-31')

# 获取实时行情
realtime = fetcher.fetch_realtime_data(['000001', '600036'])
```

### 2. YFinance

**特点**：
- ✅ 免费、开源
- ✅ 无需 API key
- ✅ 支持全球市场（美股、港股、A股等）
- ✅ 数据质量高、更新及时
- ✅ 支持实时数据和历史数据
- ⚠️ 部分地区访问可能需要代理

**使用场景**：
- 美股市场数据
- 全球股票对比分析
- 获取详细的基本面信息

**示例代码**：
```python
from src.data_source import DataFetcher

config = {
    'provider': 'yfinance',
    'cache': {'enabled': True}
}

fetcher = DataFetcher(config)

# 获取美股数据
data = fetcher.fetch_stock_data('AAPL', '2024-01-01', '2024-12-31')

# 获取A股数据（需要添加市场后缀）
data = fetcher.fetch_stock_data('000001.SZ', '2024-01-01', '2024-12-31')

# 获取港股数据
data = fetcher.fetch_stock_data('0700.HK', '2024-01-01', '2024-12-31')
```

### 3. Twelve Data

**特点**：
- ✅ 支持全球市场（股票、外汇、加密货币、ETF等）
- ✅ 数据质量高、更新及时
- ✅ 提供实时和历史数据
- ✅ 支持分钟级数据
- ⚠️ 需要 API key（免费版有限制：每天800次请求，每分钟8次）
- ⚠️ 高级功能需要付费

**使用场景**：
- 全球股票数据获取
- 外汇和加密货币数据
- 多市场数据对比
- 高频数据分析

**示例代码**：
```python
from src.data_source import DataFetcher

config = {
    'provider': 'twelvedata',
    'api_key': 'your_twelvedata_api_key',
    'cache': {'enabled': True}
}

fetcher = DataFetcher(config)

# 获取美股数据
data = fetcher.fetch_stock_data('AAPL', '2024-01-01', '2024-12-31')

# 获取外汇数据
forex_data = fetcher.fetch_stock_data('EUR/USD', '2024-01-01', '2024-12-31')

# 获取加密货币数据
crypto_data = fetcher.fetch_stock_data('BTC/USD', '2024-01-01', '2024-12-31')

# 获取实时行情
realtime = fetcher.fetch_realtime_data(['AAPL', 'MSFT', 'GOOGL'])
```

**获取 API Key**：
1. 访问 [https://twelvedata.com](https://twelvedata.com)
2. 注册账号
3. 在控制台获取 API key
4. 免费版限额：800次/天，8次/分钟

### 4. Tushare（待实现）

**特点**：
- 🔄 需要 API key（免费注册）
- 🔄 数据专业、准确
- 🔄 适合量化分析
- 🔄 免费版有调用频率限制

## 股票代码格式

### AkShare 格式
- A股上海：`600000`（6位数字）
- A股深圳：`000001`（6位数字）
- 港股：`00700`（5位数字）

### YFinance 格式
- 美股：`AAPL`（代码）
- A股上海：`600000.SS`（代码.SS后缀）
- A股深圳：`000001.SZ`（代码.SZ后缀）
- 港股：`0700.HK`（代码.HK后缀）
- 指数：`^GSPC`（^前缀）

### Twelve Data 格式
- 美股：`AAPL`（代码）
- 外汇：`EUR/USD`, `GBP/USD`（货币对用斜杠分隔）
- 加密货币：`BTC/USD`, `ETH/USD`（加密货币对用斜杠分隔）
- A股：`600000.SS`, `000001.SZ`（同 YFinance）
- 港股：`0700.HK`（同 YFinance）
- ETF：`SPY`, `QQQ`（代码）
- 指数：`NDX`, `DJI`（代码）

## 统一接口

### DataFetcher 类

主要方法：

#### 1. 获取股票列表
```python
fetch_stock_list(market='A') -> pd.DataFrame
```
- `market`: 市场类型 'A'(A股), 'HK'(港股), 'US'(美股)
- 返回：包含股票代码和名称的 DataFrame

#### 2. 获取股票历史数据
```python
fetch_stock_data(symbol, start_date, end_date) -> pd.DataFrame
```
- `symbol`: 股票代码
- `start_date`: 开始日期 (YYYY-MM-DD)
- `end_date`: 结束日期 (YYYY-MM-DD)
- 返回：包含 OHLCV 数据的 DataFrame

#### 3. 获取实时行情
```python
fetch_realtime_data(symbols) -> pd.DataFrame
```
- `symbols`: 股票代码列表
- 返回：实时行情 DataFrame

#### 4. 获取基本面数据
```python
fetch_fundamental_data(symbol) -> Dict
```
- `symbol`: 股票代码
- 返回：包含 PE、PB、市值等信息的字典

#### 5. 获取基金列表
```python
fetch_fund_list() -> pd.DataFrame
```
- 返回：基金列表 DataFrame

#### 6. 获取基金净值
```python
fetch_fund_data(symbol, start_date, end_date) -> pd.DataFrame
```
- 返回：基金净值历史数据

#### 7. 获取指数数据
```python
fetch_index_data(index_code, start_date, end_date) -> pd.DataFrame
```
- 返回：指数历史数据

### 缓存功能

DataFetcher 支持内存缓存，减少重复请求：

```python
# 启用缓存
config = {
    'provider': 'akshare',
    'cache': {
        'enabled': True,
        'expire_time': 3600  # 秒
    }
}

fetcher = DataFetcher(config)

# 清空缓存
fetcher.clear_cache()
```

### 切换数据源

在运行时可以动态切换数据源：

```python
fetcher = DataFetcher({'provider': 'akshare'})

# 切换到 YFinance
fetcher.switch_provider('yfinance')

# 获取当前数据源名称
current = fetcher.get_provider_name()
```

## 扩展新数据源

如果需要添加新的数据源（如 Tushare），只需：

1. 创建新的 Provider 类，继承 `BaseProvider`
2. 实现所有抽象方法
3. 在 `DataFetcher._init_provider()` 中添加初始化逻辑

示例：

```python
from .base_provider import BaseProvider

class TushareProvider(BaseProvider):
    def __init__(self, config):
        super().__init__(config)
        import tushare as ts
        ts.set_token(self.api_key)
        self.pro = ts.pro_api()
    
    def fetch_stock_list(self, market='A'):
        # 实现获取股票列表
        pass
    
    # ... 实现其他方法
```

## 数据格式说明

### 股票历史数据格式

| 列名 | 类型 | 说明 |
|------|------|------|
| date | datetime | 日期 |
| open | float | 开盘价 |
| high | float | 最高价 |
| low | float | 最低价 |
| close | float | 收盘价 |
| volume | int | 成交量 |
| amount | float | 成交额 |

### 实时行情数据格式

| 列名 | 类型 | 说明 |
|------|------|------|
| code | str | 股票代码 |
| name | str | 股票名称 |
| price | float | 当前价格 |
| change | float | 涨跌额 |
| change_pct | float | 涨跌幅(%) |
| volume | int | 成交量 |
| amount | float | 成交额 |
| open | float | 今开 |
| high | float | 最高 |
| low | float | 最低 |
| pre_close | float | 昨收 |
| pe_ratio | float | 市盈率 |
| pb_ratio | float | 市净率 |
| market_cap | float | 总市值 |

## 常见问题

### 1. 如何选择数据源？

- **分析A股**：推荐使用 AkShare
- **分析美股**：推荐使用 YFinance
- **全球市场对比**：使用 YFinance
- **需要基金数据**：使用 AkShare

### 2. 数据获取失败怎么办？

检查以下几点：
1. 网络连接是否正常
2. 股票代码格式是否正确
3. 日期范围是否合理
4. 查看日志获取详细错误信息

### 3. 如何提高数据获取速度？

1. 启用缓存功能
2. 批量获取而不是逐个请求
3. 使用合适的日期范围，避免获取过多数据

### 4. 数据不一致怎么办？

不同数据源可能有细微差异：
- 价格调整方式不同（复权方式）
- 更新时间不同
- 数据精度不同

建议针对具体场景选择合适的数据源。

## 测试

运行测试脚本：

```bash
python test_data_source.py
```

测试内容：
- AkShare 数据源功能
- YFinance 数据源功能
- 数据源切换
- 缓存功能

## 依赖安装

```bash
pip install akshare yfinance
```

或者安装项目所有依赖：

```bash
pip install -r requirements.txt
```
