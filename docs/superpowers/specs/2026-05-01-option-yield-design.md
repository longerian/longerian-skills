# Option Yield Calculator Skill 设计文档

## 概述

创建一个期权权利金年化收益计算 skill，通过截图或文字输入期权信息，自动计算权利金年化收益率。基于段永平的计算方法：净投入资金 = 行权价 - 权利金，年化收益 = 权利金/净投入 × 12/月数 + 无风险利率。

## 目标

- 用户发送期权截图或文字 → 自动识别期权参数 → 计算年化收益率
- 支持 Sell Put 和 Sell Call 两种期权类型
- 支持美股和港股两个市场，使用对应的无风险利率
- 实时搜索最新无风险利率，并验证数据时效性
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
| `market` | 市场 | us / hk |
| `option_type` | 期权类型 | put / call |
| `quantity` | 合约数量（张） | 999 |
| `shares_per_contract` | 每张合约股数 | 100 |
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

## 市场与无风险利率

### 市场支持

| 市场 | 代码 | 无风险利率来源 | 每张合约默认股数 | 说明 |
|------|------|--------------|----------------|------|
| 美股 | `us` | 美国国债收益率（10年期） | 100股 | 默认市场，固定100股/张 |
| 港股 | `hk` | 香港银行间同业拆借利率（HIBOR） | 100股（可覆盖） | 港股期权，股数不统一 |

### 无风险利率获取与验证流程

```
1. 根据市场选择利率来源
   - 美股 → 搜索 "US 10-year Treasury yield"
   - 港股 → 搜索 "HK HIBOR rate"
    ↓
2. 搜索获取最新利率数据
    ↓
3. 验证数据时效性
   - 检查数据日期是否在最近7天内
   - 如果超过7天，警告用户数据可能过时
    ↓
4. 如果搜索失败或数据过时
   - 要求用户手动输入当前利率
    ↓
5. 使用验证后的利率进行计算
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
| 市场 | 根据标的代码自动判断（如港股代码以数字开头），否则询问用户 |
| 无风险利率 | 根据市场搜索对应利率，验证时效性，失败则要求用户输入 |
| 每张合约股数 | 美股默认100股；港股默认100股，但提示用户确认（港股可能为500股等） |
| 数量 | 默认1张 |

## 输出格式

```
📊 期权权利金年化收益计算
━━━━━━━━━━━━━━━━━━━━━━━
标的: AAPL
市场: 美股
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
无风险利率: 4.3%（US 10Y Treasury, 2026-05-01）
总年化收益率: 18.0%
```

## Python 脚本接口

### 输入 (option_input.json)

```json
{
  "underlying": "AAPL",
  "market": "us",
  "option_type": "put",
  "strike": 195.00,
  "premium": 14.45,
  "months": 7,
  "quantity": 999,
  "shares_per_contract": 100,
  "risk_free_rate": 0.043
}
```

### 输出 (option_result.json)

```json
{
  "underlying": "AAPL",
  "market": "us",
  "option_type": "put",
  "strike": 195.00,
  "premium": 14.45,
  "months": 7,
  "quantity": 999,
  "shares_per_contract": 100,
  "risk_free_rate": 0.043,
  "risk_free_rate_source": "US 10Y Treasury",
  "risk_free_rate_date": "2026-05-01",
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
| 无风险利率数据超过7天 | 警告数据可能过时，建议用户确认 |
| 截图无法识别 | 要求用户提供文字信息 |
| 市场无法自动判断 | 询问用户是美股还是港股 |

## 前置条件

- Python 3.x（无额外依赖，仅用标准库）
- Web 搜索能力（用于获取实时无风险利率）
