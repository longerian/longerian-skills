# Option Yield Calculator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a skill that calculates annualized premium yield for sold options (puts and calls) based on Duan Yongping's method, with support for US and HK markets.

**Architecture:** Agent parses option info from screenshots or text, searches for real-time risk-free rates, then a pure Python script calculates the annualized return. Formula: `(premium / (strike - premium)) × (12 / months) + risk_free_rate`.

**Tech Stack:** Python 3.x (standard library only), agent vision for screenshot parsing, web search for risk-free rates

**Spec:** `docs/superpowers/specs/2026-05-01-option-yield-design.md`

---

## File Structure

```
skills/option-yield/
├── SKILL.md                          # Skill definition + interaction flow
├── option_yield_calculator.py        # Calculation core (pre-installed to ~/.longerian/scripts/)
└── tests/
    └── test_option_yield_calculator.py
```

Runtime (after installation):
```
~/.longerian/
├── scripts/option_yield_calculator.py
└── data/option-yield/
    ├── option_input.json             # (generated per calculation)
    └── option_result.json            # (generated per calculation)
```

---

### Task 1: Create directory structure

**Files:**
- Create: `skills/option-yield/` directory
- Create: `skills/option-yield/tests/` directory

- [ ] **Step 1: Create directories**

```bash
mkdir -p skills/option-yield/tests
mkdir -p ~/.longerian/scripts
mkdir -p ~/.longerian/data/option-yield
```

- [ ] **Step 2: Verify structure**

```bash
ls -la skills/option-yield/
ls -la ~/.longerian/data/option-yield/
```

Expected: Empty directories created successfully.

- [ ] **Step 3: Commit**

```bash
git add skills/option-yield/
git commit -m "feat(option-yield): create directory structure for option yield calculator skill"
```

---

### Task 2: Write calculator tests (TDD)

**Files:**
- Create: `skills/option-yield/tests/test_option_yield_calculator.py`

- [ ] **Step 1: Write tests for calculate_annualized_return**

```python
"""Tests for option yield calculator."""
import json
import os
import sys
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from option_yield_calculator import calculate_annualized_return, validate_input, main


def test_basic_put_calculation():
    """Test basic sell put calculation (Duan Yongping AAPL example)."""
    result = calculate_annualized_return(
        strike=195.00,
        premium=14.45,
        months=7,
        risk_free_rate=0.043,
        quantity=999,
        shares_per_contract=100,
    )
    assert abs(result['capital_per_share'] - 180.55) < 0.01
    assert abs(result['premium_annualized_return'] - 0.137) < 0.01
    assert abs(result['total_annualized_return'] - 0.180) < 0.01
    assert result['shares_total'] == 99900
    assert abs(result['total_premium_income'] - 1443555.00) < 1.0


def test_basic_call_calculation():
    """Test basic sell call calculation."""
    result = calculate_annualized_return(
        strike=200.00,
        premium=5.00,
        months=3,
        risk_free_rate=0.04,
        quantity=10,
        shares_per_contract=100,
    )
    assert abs(result['capital_per_share'] - 195.00) < 0.01
    # (5 / 195) * (12/3) = 0.1026
    assert abs(result['premium_annualized_return'] - 0.1026) < 0.01
    # 0.1026 + 0.04 = 0.1426
    assert abs(result['total_annualized_return'] - 0.1426) < 0.01
    assert result['shares_total'] == 1000


def test_hk_market_with_custom_shares():
    """Test HK market with non-standard shares per contract."""
    result = calculate_annualized_return(
        strike=300.00,
        premium=10.00,
        months=6,
        risk_free_rate=0.035,
        quantity=5,
        shares_per_contract=500,
    )
    assert result['shares_total'] == 2500
    assert abs(result['capital_per_share'] - 290.00) < 0.01
    # (10 / 290) * (12/6) = 0.0690
    assert abs(result['premium_annualized_return'] - 0.0690) < 0.01


def test_small_premium():
    """Test with very small premium."""
    result = calculate_annualized_return(
        strike=100.00,
        premium=0.50,
        months=1,
        risk_free_rate=0.04,
        quantity=1,
        shares_per_contract=100,
    )
    assert abs(result['capital_per_share'] - 99.50) < 0.01
    # (0.5 / 99.5) * 12 = 0.0603
    assert abs(result['premium_annualized_return'] - 0.0603) < 0.01


def test_validate_input_valid():
    """Test input validation with valid data."""
    errors = validate_input(
        strike=195.00,
        premium=14.45,
        months=7,
        risk_free_rate=0.043,
    )
    assert errors == []


def test_validate_input_premium_exceeds_strike():
    """Test that premium >= strike is rejected."""
    errors = validate_input(
        strike=100.00,
        premium=150.00,
        months=7,
        risk_free_rate=0.043,
    )
    assert len(errors) > 0
    assert any('权利金' in e for e in errors)


def test_validate_input_expired():
    """Test that expired options are rejected."""
    errors = validate_input(
        strike=100.00,
        premium=5.00,
        months=0,
        risk_free_rate=0.043,
    )
    assert len(errors) > 0
    assert any('过期' in e for e in errors)


def test_validate_input_negative_months():
    """Test that negative months are rejected."""
    errors = validate_input(
        strike=100.00,
        premium=5.00,
        months=-1,
        risk_free_rate=0.043,
    )
    assert len(errors) > 0


def test_main_with_json_files():
    """Test main() reads input JSON and writes output JSON."""
    with tempfile.TemporaryDirectory() as tmpdir:
        input_path = os.path.join(tmpdir, 'input.json')
        output_path = os.path.join(tmpdir, 'output.json')

        input_data = {
            "underlying": "AAPL",
            "market": "us",
            "option_type": "put",
            "strike": 195.00,
            "premium": 14.45,
            "months": 7,
            "quantity": 999,
            "shares_per_contract": 100,
            "risk_free_rate": 0.043,
        }
        with open(input_path, 'w') as f:
            json.dump(input_data, f)

        # Patch sys.argv
        old_argv = sys.argv
        sys.argv = ['option_yield_calculator.py', input_path, output_path]
        try:
            main()
        finally:
            sys.argv = old_argv

        with open(output_path, 'r') as f:
            result = json.load(f)

        assert result['underlying'] == 'AAPL'
        assert result['market'] == 'us'
        assert abs(result['capital_per_share'] - 180.55) < 0.01
        assert abs(result['total_annualized_return'] - 0.180) < 0.01
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd skills/option-yield && python3 -m pytest tests/test_option_yield_calculator.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'option_yield_calculator'`

- [ ] **Step 3: Commit test file**

```bash
git add skills/option-yield/tests/test_option_yield_calculator.py
git commit -m "test(option-yield): add calculator unit tests (TDD red phase)"
```

---

### Task 3: Implement option_yield_calculator.py

**Files:**
- Create: `skills/option-yield/option_yield_calculator.py`

- [ ] **Step 1: Implement the calculator**

```python
#!/usr/bin/env python3
"""Option Premium Annualized Return Calculator.

Calculates the annualized return on selling options (puts/calls)
based on Duan Yongping's method:
- Capital = Strike - Premium (net investment)
- Premium return = (Premium / Capital) × (12 / Months)
- Total return = Premium return + Risk-free rate

No external dependencies - uses only Python standard library.

Usage:
    python3 option_yield_calculator.py [input_json_path] [output_json_path]

Defaults:
    input:  ~/.longerian/data/option-yield/option_input.json
    output: ~/.longerian/data/option-yield/option_result.json
"""

import json
import os
import sys


def validate_input(strike, premium, months, risk_free_rate):
    """Validate input parameters. Returns list of error messages."""
    errors = []
    if premium >= strike:
        errors.append(f"权利金 ({premium}) 必须小于行权价 ({strike})")
    if months <= 0:
        errors.append(f"到期月数 ({months}) 必须大于 0（期权已过期）")
    if risk_free_rate < 0:
        errors.append(f"无风险利率 ({risk_free_rate}) 不能为负数")
    return errors


def calculate_annualized_return(strike, premium, months, risk_free_rate,
                                 quantity=1, shares_per_contract=100):
    """Calculate annualized return for a sold option.

    Args:
        strike: Strike price
        premium: Premium received per share
        months: Months to expiration
        risk_free_rate: Annual risk-free rate (e.g., 0.043 for 4.3%)
        quantity: Number of contracts
        shares_per_contract: Shares per contract (US: 100, HK: varies)

    Returns:
        dict with calculation results
    """
    capital_per_share = strike - premium
    shares_total = quantity * shares_per_contract
    total_premium_income = premium * shares_total

    premium_annualized_return = (premium / capital_per_share) * (12 / months)
    total_annualized_return = premium_annualized_return + risk_free_rate

    return {
        "capital_per_share": round(capital_per_share, 2),
        "shares_total": shares_total,
        "total_premium_income": round(total_premium_income, 2),
        "premium_annualized_return": round(premium_annualized_return, 4),
        "total_annualized_return": round(total_annualized_return, 4),
    }


def main():
    """CLI entry point."""
    base_dir = os.path.expanduser('~/.longerian/data/option-yield')
    input_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base_dir, 'option_input.json')
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(base_dir, 'option_result.json')

    # Load input
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    strike = data['strike']
    premium = data['premium']
    months = data['months']
    risk_free_rate = data['risk_free_rate']
    quantity = data.get('quantity', 1)
    shares_per_contract = data.get('shares_per_contract', 100)

    # Validate
    errors = validate_input(strike, premium, months, risk_free_rate)
    if errors:
        print("Error: " + "; ".join(errors), file=sys.stderr)
        sys.exit(1)

    # Calculate
    result = calculate_annualized_return(
        strike=strike,
        premium=premium,
        months=months,
        risk_free_rate=risk_free_rate,
        quantity=quantity,
        shares_per_contract=shares_per_contract,
    )

    # Merge input fields into output
    output = {
        "underlying": data.get("underlying", ""),
        "market": data.get("market", ""),
        "option_type": data.get("option_type", ""),
        "strike": strike,
        "premium": premium,
        "months": months,
        "quantity": quantity,
        "shares_per_contract": shares_per_contract,
        "risk_free_rate": risk_free_rate,
        "risk_free_rate_source": data.get("risk_free_rate_source", ""),
        "risk_free_rate_date": data.get("risk_free_rate_date", ""),
        **result,
    }

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Run all tests**

```bash
cd skills/option-yield && python3 -m pytest tests/test_option_yield_calculator.py -v
```

Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add skills/option-yield/option_yield_calculator.py
git commit -m "feat(option-yield): implement option yield calculator"
```

---

### Task 4: Write SKILL.md

**Files:**
- Create: `skills/option-yield/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
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
```

- [ ] **Step 2: Verify SKILL.md follows existing pattern**

Compare with `skills/dii-estimator/SKILL.md` to ensure consistent structure.

- [ ] **Step 3: Commit**

```bash
git add skills/option-yield/SKILL.md
git commit -m "feat(option-yield): add SKILL.md with interaction flow definition"
```

---

### Task 5: Copy files to runtime directory and test

**Files:**
- Copy: `option_yield_calculator.py` → `~/.longerian/scripts/`

- [ ] **Step 1: Copy calculator script**

```bash
cp skills/option-yield/option_yield_calculator.py ~/.longerian/scripts/
```

- [ ] **Step 2: Verify file is in place**

```bash
ls -la ~/.longerian/scripts/option_yield_calculator.py
```

Expected: File exists.

- [ ] **Step 3: Test calculator with sample input (Duan Yongping AAPL example)**

```bash
cat > ~/.longerian/data/option-yield/option_input.json << 'EOF'
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
  "risk_free_rate_date": "2026-05-01"
}
EOF

python3 ~/.longerian/scripts/option_yield_calculator.py
```

Expected: JSON output with `total_annualized_return` ≈ 0.180

- [ ] **Step 4: No commit needed** (runtime files are not in git)

---

### Task 6: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add option-yield to the skills table**

Add row:
```markdown
| [option-yield](skills/option-yield/SKILL.md) | Calculate annualized premium yield for sold options (puts/calls) |
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add option-yield to skills list in README"
```

---

### Task 7: Integration test with real option data

- [ ] **Step 1: Test end-to-end with Duan Yongping's AAPL trade**

Simulate the full flow:
1. Parse option info (either from screenshot or text input)
2. Search for current US 10Y Treasury yield
3. Run option yield calculator
4. Verify output matches expected ~18% annualized return

- [ ] **Step 2: Test HK market flow**

Test with a sample HK option:
1. Parse HK option info (e.g., 700.HK)
2. Search for HIBOR rate
3. Query shares per contract for the underlying
4. Run calculator
5. Verify output is reasonable

- [ ] **Step 3: Commit any fixes**

If any issues are found during integration testing, fix and commit.

---

## Summary

| Task | Description | Est. Steps |
|------|-------------|-----------|
| 1 | Create directory structure | 3 |
| 2 | Write calculator tests (TDD) | 3 |
| 3 | Implement option_yield_calculator.py | 3 |
| 4 | Write SKILL.md | 3 |
| 5 | Copy files to runtime + test | 4 |
| 6 | Update README.md | 2 |
| 7 | Integration test | 3 |

Total: 7 tasks, 21 steps
