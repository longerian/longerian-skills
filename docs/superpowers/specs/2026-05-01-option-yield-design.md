# Option Yield Calculator Skill 设计文档

## 概述

创建一个期权权利金年化收益计算 skill，通过截图或文字输入期权信息，自动计算权利金年化收益率。基于段永平的计算方法：净投入资金 = 行权价 - 权利金，年化收益 = 权利金/净投入 × 12/月数 + 无风险利率。

## 目标

- 用户发送期权截图或文字 → 自动识别期权参数 → 计算年化收益率
- 支持 Sell Put 和 Sell Call 两种期权类型
- 实时搜索最新无风险利率（美国国债收益率）
- 终端文本输出简洁结果

## 架构

### 文件结构

```
skills/option-yield/
├── SKILL.md                      # Skill 定义 + 交互流程
├── option_yield_calculator.py    # 核心计算脚本
└── tests/
    └── test_option_yield_calculator.py
```

### 运行时目录

```
~/.longerian/
├── scripts/option_yield_calculator.py   # 计算脚本（安装时复制）
├── data/option-yield/
│   ├── option_input.json                # 输入（临时，每次计算时生成）
│   └── option_result.json               # 输出（临时，每次计算时生成）
```

### 数据流

```
用户提供输入（截图或文字）
    ↓
Agent 解析期权参数：标的、类型、行权价、权利金、到期日、数量
    ↓
如有缺失参数，向用户确认
    ↓
搜索实时无风险利率（web搜索）
    ↓
写入 ~/.longerian/data/option-yield/option_input.json
    ↓
运行 python3 ~/.longerian/scripts/option_yield_calculator.py
    ↓
读取 ~/.longerian/data/option-yield/option_result.json
    ↓
终端输出结果
```

## 核心算法

### 计算公式

```python
# 净资金占用（每股）
capital = strike - premium

# 权利金年化收益率
premium_annualized = (premium / capital) * (12 / months)

# 总年化收益率 = 权利金收益 + 无风险利率
total_annualized = premium_annualized + risk_free_rate
```

### 参数说明

| 参数 | 含义 | 示例 |
|------|------|------|
| `strike` | 行权价 | $195.00 |
| `premium` | 权利金（每股） | $14.45 |
| `months` | 剩余到期月数 | 7 |
| `risk_free_rate` | 无风险利率（年化小数） | 0.043 |
| `option_type` | 期权类型 | put / call |
| `quantity` | 合约数量（张） | 999 |
| `underlying` | 标的代码 | AAPL |

### 计算示例（段永平AAPL交易）

```
标的: AAPL
类型: Sell Put
行权价: $195.00
权利金: $14.45
到期月数: 7
无风险利率: 4.3%

净资金占用 = 195 - 14.45 = $180.55
权利金年化收益 = 14.45 / 180.55 × 12/7 = 13.7%
总年化收益 = 13.7% + 4.3% = 18.0%
```

## 输入格式

### 截图输入

Agent 使用内置视觉能力从截图中识别以下信息：
- 标的代码（如 AAPL、TSLA）
- 期权类型（Put/Call）
- 行权价（Strike Price）
- 权利金（Premium）
- 到期日（Expiration Date）
- 卖出数量

### 文字输入

支持自由格式文字，例如：
```
卖了AAPL 195 put，权利金14.45，明年1月到期，999张
```

或结构化格式：
```
标的: AAPL
类型: Sell Put
行权价: 195
权利金: 14.45
到期日: 2026-01-16
数量: 999
```

### 参数缺失处理

| 缺失参数 | 处理方式 |
|---------|---------|
| 到期日 | 向用户确认剩余月份 |
| 期权类型 | 默认 Sell Put，向用户确认 |
| 无风险利率 | 实时搜索美国国债收益率，失败则要求用户输入 |
| 数量 | 默认1张 |

## 输出格式

```
📊 期权权利金年化收益计算
━━━━━━━━━━━━━━━━━━━━━━━
标的: AAPL
期权类型: Sell Put
行权价: $195.00
权利金: $14.45/股
到期日: 2026-01-16（剩余7个月）
数量: 999张（99,900股）

💰 收益分析
━━━━━━━━━━━━━━━━━━━━━━━
净资金占用: $180.55/股
总权利金收入: $1,443,555.00
权利金年化收益率: 13.7%
无风险利率: 4.3%（实时）
总年化收益率: 18.0%
```

## Python 脚本接口

### 输入 (option_input.json)

```json
{
  "underlying": "AAPL",
  "option_type": "put",
  "strike": 195.00,
  "premium": 14.45,
  "months": 7,
  "quantity": 999,
  "risk_free_rate": 0.043
}
```

### 输出 (option_result.json)

```json
{
  "underlying": "AAPL",
  "option_type": "put",
  "strike": 195.00,
  "premium": 14.45,
  "months": 7,
  "quantity": 999,
  "risk_free_rate": 0.043,
  "capital_per_share": 180.55,
  "total_premium_income": 1443555.00,
  "premium_annualized_return": 0.137,
  "total_annualized_return": 0.180,
  "shares_total": 99900
}
```

## 错误处理

| 场景 | 处理 |
|------|------|
| 权利金 >= 行权价 | 报错：参数不合理 |
| 到期月数 <= 0 | 报错：已过期 |
| 无风险利率搜索失败 | 要求用户手动输入 |
| 截图无法识别 | 要求用户提供文字信息 |

## 前置条件

- Python 3.x（无额外依赖，仅用标准库）
- Web 搜索能力（用于获取实时无风险利率）
