---
name: option-yield
description: Use when user wants to calculate the annualized return on selling options (puts or calls). Triggers on "计算期权收益", "期权年化", "权利金收益", "option yield", "premium return", or when option trading screenshots are shared with yield analysis intent.
version: 1.0.0
---

# 期权权利金年化收益计算器

通过截图或文字输入期权信息，计算权利金年化收益率。基于段永平的计算方法。

## 前置条件

- Python 3.x（无额外依赖，仅用标准库）
- `~/.longerian/scripts/option_yield_calculator.py`（安装时自动复制）
- Web 搜索能力（用于获取实时无风险利率）

## 目录约定

所有文件使用 `~/.longerian/`（持久化、跨 agent）：

```
~/.longerian/
├── scripts/option_yield_calculator.py   # 计算脚本
└── data/option-yield/
    ├── option_input.json                # 输入（临时）
    └── option_result.json               # 输出（临时）
```

## 核心公式

```
净资金占用 = 行权价 - 权利金
权利金年化收益 = (权利金 / 净资金占用) × (12 / 到期月数)
总年化收益 = 权利金年化收益 + 无风险利率
```

## 流程

### Step 1: 接收输入

用户可能提供：
- **截图**：期权交易界面截图
- **文字**：自由格式或结构化的期权信息

### Step 2: 解析期权参数

从输入中提取以下参数：

| 参数 | 说明 | 默认值 |
|------|------|--------|
| underlying | 标的代码（如 AAPL、700） | 必填 |
| market | 市场（us / hk） | 根据标的自动判断 |
| option_type | 期权类型（put / call） | put |
| strike | 行权价 | 必填 |
| premium | 权利金（每股） | 必填 |
| months | 剩余到期月数 | 必填 |
| quantity | 合约数量（张） | 1 |
| shares_per_contract | 每张合约股数 | 美股100，港股需查询 |

**市场自动判断规则：**
- 标的代码以数字开头（如 700、9988）→ 港股
- 标的代码以字母开头（如 AAPL、TSLA）→ 美股

**港股每张合约股数查询：**
1. 搜索 "{标的代码} HKEX option shares per contract"
2. 搜索成功 → 使用查询到的股数
3. 搜索失败 → 询问用户

如有缺失参数，向用户确认。

### Step 3: 搜索无风险利率

根据市场搜索对应的无风险利率：

| 市场 | 搜索关键词 | 利率来源 |
|------|-----------|---------|
| 美股 | "US 10-year Treasury yield" | 美国10年期国债收益率 |
| 港股 | "HK HIBOR rate" | 香港银行间同业拆借利率 |

**验证数据时效性：**
- 检查数据日期是否在最近 7 天内
- 超过 7 天 → 警告用户数据可能过时
- 搜索失败 → 要求用户手动输入当前利率

### Step 4: 运行计算

写入输入文件：
```bash
# 写入 ~/.longerian/data/option-yield/option_input.json
```

运行计算：
```bash
python3 ~/.longerian/scripts/option_yield_calculator.py
```

读取结果：
```bash
# 读取 ~/.longerian/data/option-yield/option_result.json
```

### Step 5: 输出结果

**终端输出格式：**

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

## 错误处理

| 场景 | 处理 |
|------|------|
| 权利金 >= 行权价 | 报错：参数不合理 |
| 到期月数 <= 0 | 报错：已过期 |
| 无风险利率搜索失败 | 要求用户手动输入 |
| 无风险利率数据超过 7 天 | 警告数据可能过时 |
| 截图无法识别 | 要求用户提供文字信息 |
| 市场无法自动判断 | 询问用户是美股还是港股 |
| 港股股数查询失败 | 询问用户每张合约对应多少股 |
