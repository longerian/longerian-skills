# DII Estimator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a skill that estimates the Dietary Inflammatory Index (DII) from food photos using vision AI + Python calculation.

**Architecture:** Claude identifies food from photos and estimates weights, looks up nutrients from a JSON database, then a pure Python script calculates DII using the Shivappa et al. 2014 algorithm (45 parameters). Mobile-first design for OpenClaw.

**Tech Stack:** Python 3.11+ (standard library only), JSON data files, Claude vision for food recognition

**Spec:** `docs/superpowers/specs/2026-04-30-dii-estimator-design.md`

---

## File Structure

```
skills/dii-estimator/
├── SKILL.md                    # Skill definition + interaction flow
├── dii_calculator.py           # DII calculation core (pre-installed to ~/.longerian/scripts/)
├── food_nutrition_db.json      # Food → nutrient mapping (~215 foods)
├── dii_params.json             # 45 DII parameter constants
└── tests/
    └── test_dii_calculator.py  # Unit tests for DII calculation
```

Runtime (after installation):
```
~/.longerian/
├── scripts/dii_calculator.py
└── data/dii/
    ├── dii_params.json
    ├── food_nutrition_db.json
    ├── dii_input.json          # (generated per analysis)
    ├── dii_result.json         # (generated per analysis)
    └── report.md               # (generated per analysis)
```

---

### Task 1: Create directory structure

**Files:**
- Create: `skills/dii-estimator/` directory
- Create: `skills/dii-estimator/tests/` directory

- [ ] **Step 1: Create directories**

```bash
mkdir -p skills/dii-estimator/tests
mkdir -p ~/.longerian/scripts
mkdir -p ~/.longerian/data/dii
```

- [ ] **Step 2: Verify structure**

```bash
ls -la skills/dii-estimator/
ls -la ~/.longerian/data/dii/
```

Expected: Empty directories created successfully.

- [ ] **Step 3: Commit**

```bash
git add skills/dii-estimator/
git commit -m "feat(dii): create directory structure for DII estimator skill"
```

---

### Task 2: Create dii_params.json

**Files:**
- Create: `skills/dii-estimator/dii_params.json`

- [ ] **Step 1: Write dii_params.json with all 45 DII parameters**

The data is extracted from `jamesjiadazhan/dietaryindex` R package source (`R/DII.R` and `R/DII_NHANES_FPED.R`), cross-verified between both implementations.

```json
{
  "ALCOHOL": {"inflammatory_score": -0.278, "global_mean": 13.98, "sd": 3.72},
  "VITB12": {"inflammatory_score": 0.106, "global_mean": 5.15, "sd": 2.7},
  "VITB6": {"inflammatory_score": -0.365, "global_mean": 1.47, "sd": 0.74},
  "BCAROTENE": {"inflammatory_score": -0.584, "global_mean": 3718, "sd": 1720},
  "CAFFEINE": {"inflammatory_score": -0.11, "global_mean": 8.05, "sd": 6.67},
  "CARB": {"inflammatory_score": 0.097, "global_mean": 272.2, "sd": 40},
  "CHOLES": {"inflammatory_score": 0.11, "global_mean": 279.4, "sd": 51.2},
  "KCAL": {"inflammatory_score": 0.18, "global_mean": 2056, "sd": 338},
  "EUGENOL": {"inflammatory_score": -0.14, "global_mean": 0.01, "sd": 0.08},
  "TOTALFAT": {"inflammatory_score": 0.298, "global_mean": 71.4, "sd": 19.4},
  "FIBER": {"inflammatory_score": -0.663, "global_mean": 18.8, "sd": 4.9},
  "FOLICACID": {"inflammatory_score": -0.19, "global_mean": 273, "sd": 70.7},
  "GARLIC": {"inflammatory_score": -0.412, "global_mean": 4.35, "sd": 2.9},
  "GINGER": {"inflammatory_score": -0.453, "global_mean": 59, "sd": 63.2},
  "IRON": {"inflammatory_score": 0.032, "global_mean": 13.35, "sd": 3.71},
  "MG": {"inflammatory_score": -0.484, "global_mean": 310.1, "sd": 139.4},
  "MUFA": {"inflammatory_score": -0.009, "global_mean": 27, "sd": 6.1},
  "NIACIN": {"inflammatory_score": -0.246, "global_mean": 25.9, "sd": 11.77},
  "N3FAT": {"inflammatory_score": -0.436, "global_mean": 1.06, "sd": 1.06},
  "N6FAT": {"inflammatory_score": -0.159, "global_mean": 10.8, "sd": 7.5},
  "ONION": {"inflammatory_score": -0.301, "global_mean": 35.9, "sd": 18.4},
  "PROTEIN": {"inflammatory_score": 0.021, "global_mean": 79.4, "sd": 13.9},
  "PUFA": {"inflammatory_score": -0.337, "global_mean": 13.88, "sd": 3.76},
  "RIBOFLAVIN": {"inflammatory_score": -0.068, "global_mean": 1.7, "sd": 0.79},
  "SAFFRON": {"inflammatory_score": -0.14, "global_mean": 0.37, "sd": 1.78},
  "SATFAT": {"inflammatory_score": 0.373, "global_mean": 28.6, "sd": 8},
  "SE": {"inflammatory_score": -0.191, "global_mean": 67, "sd": 25.1},
  "THIAMIN": {"inflammatory_score": -0.098, "global_mean": 1.7, "sd": 0.66},
  "TRANSFAT": {"inflammatory_score": 0.229, "global_mean": 3.15, "sd": 3.75},
  "TURMERIC": {"inflammatory_score": -0.785, "global_mean": 533.6, "sd": 754.3},
  "VITA": {"inflammatory_score": -0.401, "global_mean": 983.9, "sd": 518.6},
  "VITC": {"inflammatory_score": -0.424, "global_mean": 118.2, "sd": 43.46},
  "VITD": {"inflammatory_score": -0.446, "global_mean": 6.26, "sd": 2.21},
  "VITE": {"inflammatory_score": -0.419, "global_mean": 8.73, "sd": 1.49},
  "ZN": {"inflammatory_score": -0.313, "global_mean": 9.84, "sd": 2.19},
  "TEA": {"inflammatory_score": -0.536, "global_mean": 1.69, "sd": 1.53},
  "FLA3OL": {"inflammatory_score": -0.415, "global_mean": 95.8, "sd": 85.9},
  "FLAVONES": {"inflammatory_score": -0.616, "global_mean": 1.55, "sd": 0.07},
  "FLAVONOLS": {"inflammatory_score": -0.467, "global_mean": 17.7, "sd": 6.79},
  "FLAVONONES": {"inflammatory_score": -0.25, "global_mean": 11.7, "sd": 3.82},
  "ANTHOC": {"inflammatory_score": -0.131, "global_mean": 18.05, "sd": 21.14},
  "ISOFLAVONES": {"inflammatory_score": -0.593, "global_mean": 1.2, "sd": 0.2},
  "PEPPER": {"inflammatory_score": -0.131, "global_mean": 10, "sd": 7.07},
  "THYME_OREGANO": {"inflammatory_score": -0.102, "global_mean": 0.33, "sd": 0.99},
  "ROSEMARY": {"inflammatory_score": -0.013, "global_mean": 1, "sd": 15}
}
```

- [ ] **Step 2: Validate JSON is parseable**

```bash
python3 -c "import json; d = json.load(open('skills/dii-estimator/dii_params.json')); print(f'{len(d)} parameters loaded')"
```

Expected: `45 parameters loaded`

- [ ] **Step 3: Commit**

```bash
git add skills/dii-estimator/dii_params.json
git commit -m "feat(dii): add 45 DII parameter constants from Shivappa et al. 2014"
```

---

### Task 3: Write DII calculator tests (TDD)

**Files:**
- Create: `skills/dii-estimator/tests/test_dii_calculator.py`

- [ ] **Step 1: Write test for norm_cdf**

```python
"""Tests for DII calculator."""
import math
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dii_calculator import norm_cdf, calculate_dii, interpret_dii


def test_norm_cdf_at_zero():
    """norm_cdf(0) should return 0.5."""
    assert abs(norm_cdf(0) - 0.5) < 1e-10


def test_norm_cdf_positive():
    """norm_cdf(1.96) should be approximately 0.975."""
    assert abs(norm_cdf(1.96) - 0.975) < 0.001


def test_norm_cdf_negative():
    """norm_cdf(-1.96) should be approximately 0.025."""
    assert abs(norm_cdf(-1.96) - 0.025) < 0.001


def test_norm_cdf_large_positive():
    """norm_cdf(10) should be approximately 1.0."""
    assert abs(norm_cdf(10) - 1.0) < 1e-10


def test_norm_cdf_large_negative():
    """norm_cdf(-10) should be approximately 0.0."""
    assert abs(norm_cdf(-10) - 0.0) < 1e-10
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd skills/dii-estimator && python3 -m pytest tests/test_dii_calculator.py::test_norm_cdf_at_zero -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'dii_calculator'`

- [ ] **Step 3: Write test for calculate_dii with all parameters at global mean**

```python
def test_calculate_dii_at_global_mean():
    """When all nutrient values equal global mean, DII should be 0."""
    params = {
        "ALCOHOL": {"inflammatory_score": -0.278, "global_mean": 13.98, "sd": 3.72},
        "VITB12": {"inflammatory_score": 0.106, "global_mean": 5.15, "sd": 2.7},
    }
    nutrients = {
        "ALCOHOL": 13.98,
        "VITB12": 5.15,
    }
    score, components = calculate_dii(nutrients, params)
    assert abs(score) < 1e-10


def test_calculate_dii_anti_inflammatory():
    """High fiber (anti-inflammatory) should produce negative DII."""
    params = {
        "FIBER": {"inflammatory_score": -0.663, "global_mean": 18.8, "sd": 4.9},
    }
    nutrients = {"FIBER": 30}  # Well above mean
    score, components = calculate_dii(nutrients, params)
    assert score < 0
    assert components["FIBER"]["direction"] == "anti"


def test_calculate_dii_pro_inflammatory():
    """High saturated fat (pro-inflammatory) should produce positive DII."""
    params = {
        "SATFAT": {"inflammatory_score": 0.373, "global_mean": 28.6, "sd": 8},
    }
    nutrients = {"SATFAT": 50}  # Well above mean
    score, components = calculate_dii(nutrients, params)
    assert score > 0
    assert components["SATFAT"]["direction"] == "pro"


def test_calculate_dii_skips_missing_params():
    """Missing nutrient keys should be skipped, not cause errors."""
    params = {
        "ALCOHOL": {"inflammatory_score": -0.278, "global_mean": 13.98, "sd": 3.72},
        "VITB12": {"inflammatory_score": 0.106, "global_mean": 5.15, "sd": 2.7},
    }
    nutrients = {"ALCOHOL": 10}  # VITB12 not provided
    score, components = calculate_dii(nutrients, params)
    assert "ALCOHOL" in components
    assert "VITB12" not in components
```

- [ ] **Step 4: Write test for interpret_dii**

```python
def test_interpret_dii_strong_anti():
    """DII < -1 should be strong anti-inflammatory."""
    level, label = interpret_dii(-2.0)
    assert level == "strong_anti"
    assert "强抗炎" in label


def test_interpret_dii_mild_anti():
    """-1 <= DII < 0 should be mild anti-inflammatory."""
    level, label = interpret_dii(-0.5)
    assert level == "mild_anti"
    assert "轻度抗炎" in label


def test_interpret_dii_mild_pro():
    """0 <= DII < 1 should be mild pro-inflammatory."""
    level, label = interpret_dii(0.5)
    assert level == "mild_pro"
    assert "轻度促炎" in label


def test_interpret_dii_strong_pro():
    """DII >= 1 should be strong pro-inflammatory."""
    level, label = interpret_dii(2.0)
    assert level == "strong_pro"
    assert "强促炎" in label


def test_interpret_dii_zero():
    """DII = 0 should be mild pro-inflammatory (boundary)."""
    level, label = interpret_dii(0.0)
    assert level == "mild_pro"
```

- [ ] **Step 5: Write test for direction classification**

```python
def test_direction_neutral():
    """A score of exactly 0 should be classified as neutral."""
    params = {
        "ALCOHOL": {"inflammatory_score": -0.278, "global_mean": 13.98, "sd": 3.72},
    }
    nutrients = {"ALCOHOL": 13.98}  # Exactly at mean → percentile=0 → score=0
    score, components = calculate_dii(nutrients, params)
    assert components["ALCOHOL"]["direction"] == "neutral"
```

- [ ] **Step 6: Run tests to verify they fail**

```bash
cd skills/dii-estimator && python3 -m pytest tests/test_dii_calculator.py -v
```

Expected: All FAIL with `ModuleNotFoundError`

- [ ] **Step 7: Commit test file**

```bash
git add skills/dii-estimator/tests/test_dii_calculator.py
git commit -m "test(dii): add DII calculator unit tests (TDD red phase)"
```

---

### Task 4: Implement dii_calculator.py

**Files:**
- Create: `skills/dii-estimator/dii_calculator.py`

- [ ] **Step 1: Implement norm_cdf and calculate_dii**

```python
#!/usr/bin/env python3
"""DII (Dietary Inflammatory Index) Calculator.

Pure Python implementation of the DII algorithm from Shivappa et al. 2014.
No external dependencies - uses only Python standard library.

Usage:
    python3 dii_calculator.py [input_json_path] [output_json_path]

Defaults:
    input:  ~/.longerian/data/dii/dii_input.json
    output: ~/.longerian/data/dii/dii_result.json
"""

import json
import math
import os
import sys


def norm_cdf(x):
    """Cumulative distribution function for standard normal distribution."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))


def calculate_dii(nutrients, dii_params):
    """Calculate DII score from nutrient values.

    Args:
        nutrients: dict of {param_name: value} for available nutrients
        dii_params: dict of {param_name: {inflammatory_score, global_mean, sd}}

    Returns:
        (total_score, component_scores) tuple
    """
    total = 0.0
    components = {}
    for param_name, value in nutrients.items():
        if param_name in dii_params and value is not None:
            p = dii_params[param_name]
            z = (value - p['global_mean']) / p['sd']
            percentile = norm_cdf(z) * 2 - 1
            score = percentile * p['inflammatory_score']
            components[param_name] = {
                'value': value,
                'score': round(score, 4),
                'direction': 'anti' if score < 0 else ('neutral' if score == 0 else 'pro')
            }
            total += score
    return round(total, 4), components


def interpret_dii(dii_score):
    """Interpret DII score into level and label.

    Returns:
        (level, label) tuple
    """
    if dii_score < -1:
        return "strong_anti", "强抗炎"
    elif dii_score < 0:
        return "mild_anti", "轻度抗炎"
    elif dii_score < 1:
        return "mild_pro", "轻度促炎"
    else:
        return "strong_pro", "强促炎"


def main():
    """CLI entry point."""
    base_dir = os.path.expanduser('~/.longerian/data/dii')
    input_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(base_dir, 'dii_input.json')
    output_path = sys.argv[2] if len(sys.argv) > 2 else os.path.join(base_dir, 'dii_result.json')
    params_path = os.path.join(base_dir, 'dii_params.json')

    # Load DII parameters
    with open(params_path, 'r', encoding='utf-8') as f:
        dii_params = json.load(f)

    # Load input
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    nutrients = data.get('nutrients', {})
    foods = data.get('foods', [])

    # Calculate DII
    score, components = calculate_dii(nutrients, dii_params)
    level, label = interpret_dii(score)

    # Build result
    result = {
        'dii_score': score,
        'interpretation': label,
        'level': level,
        'component_scores': components,
        'parameters_used': len(components),
        'total_parameters': len(dii_params),
        'foods': foods,
    }

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
```

- [ ] **Step 2: Run all tests**

```bash
cd skills/dii-estimator && python3 -m pytest tests/test_dii_calculator.py -v
```

Expected: All tests PASS

- [ ] **Step 3: Commit**

```bash
git add skills/dii-estimator/dii_calculator.py
git commit -m "feat(dii): implement DII calculator with norm_cdf, calculate_dii, interpret_dii"
```

---

### Task 5: Create food nutrition database

**Files:**
- Create: `skills/dii-estimator/food_nutrition_db.json`

- [ ] **Step 1: Create food_nutrition_db.json with ~215 foods**

The database maps food names to per_100g nutrient values for all 45 DII parameters. All 45 keys must be present per food (use 0 for inapplicable nutrients).

Data sources: 中国食物成分表（标准版）, USDA FoodData Central.

Start with a representative subset (~30 foods) to validate the structure, then expand to full ~215.

Initial foods to include (covering all 12 categories):

**主食/面点:** 米饭, 面条, 馒头, 包子, 饺子, 炒饭, 油条, 红薯, 玉米, 土豆
**荤菜/肉类:** 红烧肉, 宫保鸡丁, 清蒸鱼, 炸鸡, 卤牛肉, 虾仁, 烤鸭, 白切鸡, 牛排, 培根
**蔬菜:** 番茄炒蛋, 蒜蓉西兰花, 清炒菠菜, 凉拌黄瓜, 地三鲜, 炒豆芽, 芹菜, 生菜, 茄子, 花菜
**汤/粥:** 紫菜蛋花汤, 番茄蛋汤, 皮蛋瘦肉粥, 小米粥
**水果:** 苹果, 香蕉, 橙子, 葡萄, 西瓜, 芒果, 猕猴桃, 蓝莓, 桃子, 梨
**饮品:** 绿茶, 红茶, 咖啡, 豆浆, 牛奶, 酸奶, 啤酒, 红酒
**西式/快餐:** 沙拉, 薯条, 蛋糕, 面包, 披萨, 汉堡, 冰淇淋, 巧克力
**零食/坚果:** 花生, 核桃, 杏仁, 瓜子, 薯片, 海苔
**调味料/油脂:** 酱油, 花生油, 橄榄油, 黄油, 蜂蜜
**豆制品:** 豆腐, 豆浆, 豆干, 毛豆
**蛋奶:** 鸡蛋, 奶酪, 酸奶
**海鲜:** 三文鱼, 虾, 海带

Each entry format:
```json
{
  "米饭": {
    "per_100g": {
      "KCAL": 116, "PROTEIN": 2.6, "TOTALFAT": 0.3, "SATFAT": 0.1,
      "TRANSFAT": 0, "MUFA": 0.1, "PUFA": 0.1, "N3FAT": 0.01,
      "N6FAT": 0.08, "CARB": 25.9, "FIBER": 0.3, "CHOLES": 0,
      "VITA": 0, "VITC": 0, "VITD": 0, "VITE": 0.04,
      "VITB6": 0.02, "VITB12": 0, "THIAMIN": 0.02, "RIBOFLAVIN": 0.01,
      "NIACIN": 0.4, "FOLICACID": 3, "IRON": 0.2, "MG": 7,
      "SE": 2.2, "ZN": 0.4, "BCAROTENE": 0, "CAFFEINE": 0,
      "ALCOHOL": 0, "GARLIC": 0, "GINGER": 0, "ONION": 0,
      "TURMERIC": 0, "EUGENOL": 0, "SAFFRON": 0, "PEPPER": 0,
      "THYME_OREGANO": 0, "ROSEMARY": 0, "TEA": 0, "FLA3OL": 0,
      "FLAVONES": 0, "FLAVONOLS": 0, "FLAVONONES": 0, "ANTHOC": 0,
      "ISOFLAVONES": 0
    }
  }
}
```

- [ ] **Step 2: Validate JSON structure**

```bash
python3 -c "
import json
db = json.load(open('skills/dii-estimator/food_nutrition_db.json'))
print(f'{len(db)} foods loaded')
for name, data in list(db.items())[:3]:
    keys = set(data['per_100g'].keys())
    print(f'  {name}: {len(keys)} nutrients')
"
```

Expected: Food count displayed, each food has 45 nutrient keys.

- [ ] **Step 3: Commit**

```bash
git add skills/dii-estimator/food_nutrition_db.json
git commit -m "feat(dii): add food nutrition database (~100 foods initial)"
```

Note: This is an initial batch. Expand to ~215 foods in a follow-up commit.

---

### Task 6: Expand food nutrition database to ~215 foods

**Files:**
- Modify: `skills/dii-estimator/food_nutrition_db.json`

- [ ] **Step 1: Add remaining foods across all 12 categories**

Expand the database from ~100 to ~215 foods. Use the same per_100g format with all 45 keys.

- [ ] **Step 2: Validate final count**

```bash
python3 -c "
import json
db = json.load(open('skills/dii-estimator/food_nutrition_db.json'))
print(f'{len(db)} foods loaded')
# Verify all foods have 45 keys
for name, data in db.items():
    assert len(data['per_100g']) == 45, f'{name} has {len(data[\"per_100g\"])} keys'
print('All foods have 45 nutrient keys')
"
```

Expected: `~215 foods loaded` and `All foods have 45 nutrient keys`

- [ ] **Step 3: Commit**

```bash
git add skills/dii-estimator/food_nutrition_db.json
git commit -m "feat(dii): expand food nutrition database to ~215 foods"
```

---

### Task 7: Write SKILL.md

**Files:**
- Create: `skills/dii-estimator/SKILL.md`

- [ ] **Step 1: Write SKILL.md**

```markdown
---
name: dii-estimator
description: Use when user wants to estimate the Dietary Inflammatory Index (DII) from a food photo. Triggers on "分析食物炎症指数", "DII 分析", "食物抗炎评分", or when a food photo is shared with inflammation analysis intent.
version: 1.0.0
---

# 食物炎症指数（DII）估算

通过食物照片识别食物成分和重量，计算膳食炎症指数（DII）。

## 前置条件

- Python 3.11+
- `~/.longerian/scripts/dii_calculator.py`（安装时自动复制）
- `~/.longerian/data/dii/dii_params.json`（安装时自动复制）
- `~/.longerian/data/dii/food_nutrition_db.json`（安装时自动复制）

## 目录约定

所有文件使用 `~/.longerian/`（持久化、跨 agent）：

```
~/.longerian/
├── scripts/dii_calculator.py   # 计算脚本
└── data/dii/
    ├── dii_params.json         # DII 45参数常量
    ├── food_nutrition_db.json  # 食物营养数据库
    ├── dii_input.json          # 输入（临时）
    ├── dii_result.json         # 输出（临时）
    └── report.md               # 详细报告
```

## 流程

### Step 1: 接收食物照片

用户在对话中发送食物照片。照片可能来自：
- 手机拍照（OpenClaw 场景）
- 文件路径（Claude Code 场景）

### Step 2: 视觉识别食物

用视觉能力识别照片中的每种食物，估算重量（g）。

输出格式：
```
识别到的食物：
1. 番茄炒蛋 - 约200g（高置信度）
2. 米饭 - 约150g（高置信度）
3. 清炒西兰花 - 约100g（中置信度）
```

置信度定义：
- **高**：食物清晰可辨，常见菜品，重量可合理估算
- **中**：食物大致可辨，但具体做法或配料不确定
- **低**：照片模糊、食物遮挡严重、或为不常见菜品

如果照片不清晰或非食物，提示用户重新拍照。

### Step 3: 查询营养数据

从 `~/.longerian/data/dii/food_nutrition_db.json` 查找每种食物的 per_100g 营养数据。

按重量换算：
```
实际营养素 = per_100g值 × (重量g / 100)
```

如果食物不在数据库中，根据食物类型估算营养素，标注"估算"。

汇总所有食物的营养素（加权求和），生成 `dii_input.json`。

### Step 4: 运行 DII 计算

写入输入文件：
```bash
# 写入 ~/.longerian/data/dii/dii_input.json
```

运行计算：
```bash
python3 ~/.longerian/scripts/dii_calculator.py
```

读取结果：
```bash
# 读取 ~/.longerian/data/dii/dii_result.json
```

### Step 5: 输出结果

**手机端摘要格式：**
```
📸 识别到 3 种食物：
• 番茄炒蛋 200g
• 米饭 150g
• 清炒西兰花 100g

🟢 DII 得分：-2.35
🟢 抗炎饮食

主要抗炎因素：
• 膳食纤维 -0.42
• 维生素 C -0.18

主要促炎因素：
• 总脂肪 +0.15
• 胆固醇 +0.03
```

**DII 解读：**
| 范围 | 等级 |
|------|------|
| DII < -1 | 🟢 强抗炎 |
| -1 ≤ DII < 0 | 🟡 轻度抗炎 |
| 0 ≤ DII < 1 | 🟠 轻度促炎 |
| DII ≥ 1 | 🔴 强促炎 |

**Markdown 报告**（保存到 `~/.longerian/data/dii/report.md`）：
1. 食物识别结果（每种食物含置信度）
2. 营养成分明细表（45 项参数）
3. DII 总分及各成分得分
4. 炎症解读 + 饮食建议
5. 与全球均值的对比

## 错误处理

| 场景 | 处理 |
|------|------|
| 照片不清晰/非食物 | 提示用户重新拍照 |
| 食物不在数据库 | 根据类型估算，标注"估算" |
| 无法判断重量 | 给出参考范围 |
| 营养素缺失 | 跳过，标注"已使用 X/45 个参数" |
| 参数少于 10 个 | 警告精度较低 |
| Python 未安装 | 提示安装 Python 3.11+ |
| 脚本执行失败 | 输出原始错误 |
```

- [ ] **Step 2: Verify SKILL.md follows existing pattern**

Compare with `skills/podcast-transcribe-whisper/SKILL.md` and `skills/podcast-transcribe-mimo/SKILL.md` to ensure consistent structure.

- [ ] **Step 3: Commit**

```bash
git add skills/dii-estimator/SKILL.md
git commit -m "feat(dii): add SKILL.md with interaction flow definition"
```

---

### Task 8: Copy files to runtime directory

**Files:**
- Copy: `dii_calculator.py` → `~/.longerian/scripts/`
- Copy: `dii_params.json` → `~/.longerian/data/dii/`
- Copy: `food_nutrition_db.json` → `~/.longerian/data/dii/`

- [ ] **Step 1: Copy files**

```bash
cp skills/dii-estimator/dii_calculator.py ~/.longerian/scripts/
cp skills/dii-estimator/dii_params.json ~/.longerian/data/dii/
cp skills/dii-estimator/food_nutrition_db.json ~/.longerian/data/dii/
```

- [ ] **Step 2: Verify files are in place**

```bash
ls -la ~/.longerian/scripts/dii_calculator.py
ls -la ~/.longerian/data/dii/dii_params.json
ls -la ~/.longerian/data/dii/food_nutrition_db.json
```

Expected: All three files exist.

- [ ] **Step 3: Test calculator with sample input**

Create a test input file and run the calculator:

```bash
cat > ~/.longerian/data/dii/dii_input.json << 'EOF'
{
  "foods": [
    {"name": "番茄炒蛋", "weight_g": 200},
    {"name": "米饭", "weight_g": 150}
  ],
  "nutrients": {
    "KCAL": 410,
    "PROTEIN": 18.2,
    "TOTALFAT": 16.7,
    "SATFAT": 3.7,
    "TRANSFAT": 0.1,
    "MUFA": 6.5,
    "PUFA": 4.3,
    "N3FAT": 0.17,
    "N6FAT": 3.08,
    "CARB": 43.35,
    "FIBER": 1.9,
    "CHOLES": 440,
    "VITA": 170,
    "VITC": 24,
    "VITD": 1.0,
    "VITE": 2.44,
    "VITB6": 0.27,
    "VITB12": 1.6,
    "THIAMIN": 0.14,
    "RIBOFLAVIN": 0.31,
    "NIACIN": 1.8,
    "FOLICACID": 73,
    "IRON": 3.4,
    "MG": 39.5,
    "SE": 17.2,
    "ZN": 2.2,
    "BCAROTENE": 500,
    "CAFFEINE": 0,
    "ALCOHOL": 0,
    "GARLIC": 0,
    "GINGER": 0,
    "ONION": 30,
    "TURMERIC": 0,
    "EUGENOL": 0,
    "SAFFRON": 0,
    "PEPPER": 0,
    "THYME_OREGANO": 0,
    "ROSEMARY": 0,
    "TEA": 0,
    "FLA3OL": 0,
    "FLAVONES": 0,
    "FLAVONOLS": 3.0,
    "FLAVONONES": 0,
    "ANTHOC": 0,
    "ISOFLAVONES": 0
  }
}
EOF

python3 ~/.longerian/scripts/dii_calculator.py
```

Expected: JSON output with DII score and component scores.

- [ ] **Step 4: No commit needed** (runtime files are not in git)

---

### Task 9: Update README.md

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Add dii-estimator to the skills table**

Add row:
```markdown
| [dii-estimator](skills/dii-estimator/SKILL.md) | Estimate Dietary Inflammatory Index (DII) from food photos |
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add dii-estimator to skills list in README"
```

---

### Task 10: Integration test with real food photo

- [ ] **Step 1: Test end-to-end with a real food photo**

Take or use an existing food photo and run the complete flow:
1. Identify foods from the photo
2. Look up nutrients from the database
3. Run DII calculator
4. Verify output is reasonable

- [ ] **Step 2: Commit any fixes**

If any issues are found during integration testing, fix and commit.

---

## Summary

| Task | Description | Est. Steps |
|------|-------------|-----------|
| 1 | Create directory structure | 3 |
| 2 | Create dii_params.json | 3 |
| 3 | Write DII calculator tests (TDD) | 7 |
| 4 | Implement dii_calculator.py | 3 |
| 5 | Create food nutrition DB (initial ~100) | 3 |
| 6 | Expand food nutrition DB (~215) | 3 |
| 7 | Write SKILL.md | 3 |
| 8 | Copy files to runtime + test | 4 |
| 9 | Update README.md | 2 |
| 10 | Integration test | 2 |

Total: 10 tasks, 33 steps
