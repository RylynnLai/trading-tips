# 证券交易推荐系统

一个自动化的证券交易分析和推荐系统，通过数据分析、回测验证，推送值得买入的证券信息。

## ✨ 特性

- 🤖 **自动化运行**：支持青龙面板订阅，定时自动执行
- 📊 **多维分析**：技术指标 + 基本面分析双重验证
- 📈 **回测验证**：历史数据回测，验证策略有效性
- 📨 **多渠道推送**：支持邮件、微信、钉钉等多种推送方式
- 🔧 **灵活配置**：支持配置文件或环境变量两种配置方式
- 📝 **详细报告**：生成HTML/JSON格式的分析报告

## 项目结构

```
trading-tips/
├── README.md                 # 项目说明文档
├── requirements.txt          # Python依赖包
├── config/                   # 配置文件目录
│   └── config.yaml          # 主配置文件
├── src/                     # 源代码目录
│   ├── main.py             # 主程序入口
│   ├── data_source/        # 数据源模块
│   ├── analysis/           # 数据分析模块
│   ├── backtest/           # 回测模块
│   ├── report/             # 分析结果生成模块
│   └── notification/       # 推送消息模块
├── tests/                   # 测试代码目录
├── data/                    # 数据存储目录
└── logs/                    # 日志文件目录
```

## 功能模块

### 1. 数据源模块 (data_source)
- 获取股票、基金等证券数据
- 支持多个数据源接口
- 数据缓存和更新机制

### 2. 数据分析模块 (analysis)
- 技术指标分析
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
```

#### 配置
编辑 `config/config.yaml` 文件，配置数据源、策略参数和推送方式。

#### 运行
```bash
python src/main.py
```

### 方式二：青龙面板（推荐）

支持在青龙面板中订阅运行，实现定时自动化执行。

#### 快速添加订阅

1. 登录青龙面板
2. 进入「订阅管理」，点击「新建订阅」
3. 填写以下信息：
   - **名称**：证券交易推荐系统
   - **链接**：`https://github.com/RylynnLai/trading-tips.git`
   - **分支**：`main`
   - **定时规则**：`0 9 * * *`（每天早上9点执行）
   - **拉取文件**：`ql_task.py`

#### 配置环境变量

在青龙面板的「环境变量」中添加：

```bash
# 必需配置
DATA_SOURCE_API_KEY=your_tushare_token

# 可选配置
TOP_N_STOCKS=10
EMAIL_ENABLED=true
EMAIL_SMTP_SERVER=smtp.gmail.com
EMAIL_USERNAME=your@email.com
EMAIL_PASSWORD=your_password
EMAIL_TO=recipient@email.com
```

📖 **详细文档**：[青龙面板使用指南](docs/QINGLONG.md)

## 开发计划

- [x] 项目框架搭建
- [ ] 数据源模块实现
- [ ] 数据分析模块实现
- [ ] 回测模块实现
- [ ] 结果生成模块实现
- [ ] 推送模块实现

## 注意事项

本系统仅供学习和研究使用，不构成投资建议。投资有风险，入市需谨慎。
