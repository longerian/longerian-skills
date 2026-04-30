# DII Estimator Skill 设计文档

## 概述

创建一个食物炎症指数（DII）估算 skill，通过拍照识别食物成分和重量，计算膳食炎症指数。基于 R 语言包 `dietaryindex` 的 DII 算法，在 Python 中重新实现。

## 目标

- 用户发送食物照片 → 自动识别食物+估算重量 → 计算 DII 分数
- 输出手机友好的摘要 + 详细 Markdown 报告
- 兼容 OpenClaw（手机优先）和 Claude Code 环境

## 架构

### 文件结构

```
skills/dii-estimator/
├── SKILL.md                    # Skill 定义 + 使用说明
├── dii_calculator.py           # DII 计算核心脚本
├── food_nutrition_db.json      # 食物→营养素映射数据库（~215 种食物）
└── dii_params.json             # DII 45参数常量
```

### 运行时目录

```
~/.longerian/
├── scripts/dii_calculator.py   # 计算脚本（安装时复制）
├── data/dii/
│   ├── dii_input.json          # 输入（临时）
│   ├── dii_result.json         # 输出（临时）
│   └── report.md               # 详细报告
└── data/dii/food_nutrition_db.json  # 食物数据库
```

### 数据流

```
用户发送食物照片
    ↓
Claude 视觉识别 → 食物名称 + 估算重量
    ↓
从 food_nutrition_db.json 查询营养数据
    ↓
写入 /tmp/longerian_skill/dii_input.json
    ↓
运行 python3 ~/.longerian/scripts/dii_calculator.py
    ↓
读取 dii_result.json
    ↓
终端/对话输出摘要 + 生成 report.md
```

## DII 算法

### 45 个食物/营养参数

| # | 参数 | 单位 | 炎症效应分 | 全球均值 | 标准差 |
|---|------|------|-----------|---------|-------|
| 1 | ALCOHOL | g | -0.278 | 13.98 | 3.72 |
| 2 | VITB12 | μg | 0.106 | 5.15 | 2.7 |
| 3 | VITB6 | mg | -0.365 | 1.47 | 0.74 |
| 4 | BCAROTENE | μg | -0.584 | 3718 | 1720 |
| 5 | CAFFEINE | g | -0.11 | 8.05 | 6.67 |
| 6 | CARB | g | 0.097 | 272.2 | 40 |
| 7 | CHOLES | mg | 0.11 | 279.4 | 51.2 |
| 8 | KCAL | kcal | 0.18 | 2056 | 338 |
| 9 | EUGENOL | mg | -0.14 | 0.01 | 0.08 |
| 10 | TOTALFAT | g | 0.298 | 71.4 | 19.4 |
| 11 | FIBER | g | -0.663 | 18.8 | 4.9 |
| 12 | FOLICACID | μg | -0.19 | 273 | 70.7 |
| 13 | GARLIC | g | -0.412 | 4.35 | 2.9 |
| 14 | GINGER | g | -0.453 | 59 | 63.2 |
| 15 | IRON | mg | 0.032 | 13.35 | 3.71 |
| 16 | MG | mg | -0.484 | 310.1 | 139.4 |
| 17 | MUFA | g | -0.009 | 27 | 6.1 |
| 18 | NIACIN | mg | -0.246 | 25.9 | 11.77 |
| 19 | N3FAT | g | -0.436 | 1.06 | 1.06 |
| 20 | N6FAT | g | -0.159 | 10.8 | 7.5 |
| 21 | ONION | g | -0.301 | 35.9 | 18.4 |
| 22 | PROTEIN | g | 0.021 | 79.4 | 13.9 |
| 23 | PUFA | g | -0.337 | 13.88 | 3.76 |
| 24 | RIBOFLAVIN | mg | -0.068 | 1.7 | 0.79 |
| 25 | SAFFRON | g | -0.14 | 0.37 | 1.78 |
| 26 | SATFAT | g | 0.373 | 28.6 | 8 |
| 27 | SE | μg | -0.191 | 67 | 25.1 |
| 28 | THIAMIN | mg | -0.098 | 1.7 | 0.66 |
| 29 | TRANSFAT | g | 0.229 | 3.15 | 3.75 |
| 30 | TURMERIC | mg | -0.785 | 533.6 | 754.3 |
| 31 | VITA | RE | -0.401 | 983.9 | 518.6 |
| 32 | VITC | mg | -0.424 | 118.2 | 43.46 |
| 33 | VITD | μg | -0.446 | 6.26 | 2.21 |
| 34 | VITE | mg | -0.419 | 8.73 | 1.49 |
| 35 | ZN | mg | -0.313 | 9.84 | 2.19 |
| 36 | TEA | g | -0.536 | 1.69 | 1.53 |
| 37 | FLA3OL | mg | -0.415 | 95.8 | 85.9 |
| 38 | FLAVONES | mg | -0.616 | 1.55 | 0.07 |
| 39 | FLAVONOLS | mg | -0.467 | 17.7 | 6.79 |
| 40 | FLAVONONES | mg | -0.25 | 11.7 | 3.82 |
| 41 | ANTHOC | mg | -0.131 | 18.05 | 21.14 |
| 42 | ISOFLAVONES | mg | -0.593 | 1.2 | 0.2 |
| 43 | PEPPER | g | -0.131 | 10 | 7.07 |
| 44 | THYME_OREGANO | mg | -0.102 | 0.33 | 0.99 |
| 45 | ROSEMARY | mg | -0.013 | 1 | 15 |

**来源**：Shivappa et al. 2014，通过 `jamesjiadazhan/dietaryindex` R 包源码交叉验证（`DII.R` 和 `DII_NHANES_FPED.R` 两份独立实现数值一致）。

### 计算公式

```python
import math

def norm_cdf(x):
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))

def calculate_dii(nutrients, dii_params):
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
                'direction': 'anti' if score < 0 else 'pro'
            }
            total += score
    return round(total, 4), components
```

### DII 解读

| 范围 | 等级 | 含义 |
|------|------|------|
| DII < -1 | 🟢 强抗炎 | 饮食具有显著抗炎作用 |
| -1 ≤ DII < 0 | 🟡 轻度抗炎 | 饮食略偏抗炎 |
| 0 ≤ DII < 1 | 🟠 轻度促炎 | 饮食略偏促炎 |
| DII ≥ 1 | 🔴 强促炎 | 饮食具有显著促炎作用 |

## 食物营养数据库

### 结构

```json
{
  "番茄炒蛋": {
    "per_100g": {
      "KCAL": 130,
      "PROTEIN": 8.5,
      "TOTALFAT": 8.2,
      "SATFAT": 1.8,
      "TRANSFAT": 0.05,
      "MUFA": 3.2,
      "PUFA": 2.1,
      "N3FAT": 0.08,
      "N6FAT": 1.5,
      "CARB": 4.5,
      "FIBER": 0.8,
      "CHOLES": 220,
      "VITA": 85,
      "VITC": 12,
      "VITD": 0.5,
      "VITE": 1.2,
      "VITB6": 0.12,
      "VITB12": 0.8,
      "THIAMIN": 0.06,
      "RIBOFLAVIN": 0.15,
      "NIACIN": 0.8,
      "FOLICACID": 35,
      "IRON": 1.5,
      "MG": 18,
      "SE": 8,
      "ZN": 1.0,
      "BCAROTENE": 250,
      "CAFFEINE": 0,
      "ALCOHOL": 0,
      "GARLIC": 0,
      "GINGER": 0,
      "ONION": 15,
      "TURMERIC": 0,
      "EUGENOL": 0,
      "SAFFRON": 0,
      "PEPPER": 0,
      "THYME_OREGANO": 0,
      "ROSEMARY": 0,
      "TEA": 0,
      "FLA3OL": 0,
      "FLAVONES": 0,
      "FLAVONOLS": 1.5,
      "FLAVONONES": 0,
      "ANTHOC": 0,
      "ISOFLAVONES": 0
    }
  }
}
```

### 覆盖范围（~215 种食物）

| 分类 | 数量 | 示例 |
|------|------|------|
| 主食/面点 | ~25 | 米饭、面条、馒头、花卷、包子、饺子、馄饨、炒饭、炒面、油条、烧饼、煎饼、年糕、粉丝、红薯、玉米、土豆、南瓜、山药、芋头、披萨、意面、吐司、汉堡、三明治 |
| 荤菜/肉类 | ~30 | 红烧肉、糖醋排骨、宫保鸡丁、鱼香肉丝、回锅肉、水煮鱼、清蒸鱼、红烧鱼、炸鸡、烤鸡、卤牛肉、红烧牛肉、羊肉串、虾仁、螃蟹、猪蹄、肉丸、腊肉、香肠、烤鸭、白切鸡、盐水鸭、牛排、培根、火腿 |
| 蔬菜 | ~30 | 清炒时蔬、番茄炒蛋、蒜蓉西兰花、干煸四季豆、地三鲜、酸辣白菜、炒菠菜、炒豆芽、炒蘑菇、凉拌黄瓜、凉拌木耳、土豆丝、茄子、辣椒、韭菜、芹菜、生菜、紫甘蓝、花菜、丝瓜、苦瓜、冬瓜、西葫芦、秋葵、芦笋 |
| 汤/粥 | ~15 | 紫菜蛋花汤、番茄蛋汤、酸辣汤、玉米排骨汤、冬瓜汤、皮蛋瘦肉粥、小米粥、白粥、八宝粥、海鲜粥 |
| 水果 | ~20 | 苹果、香蕉、橙子、葡萄、草莓、西瓜、芒果、菠萝、猕猴桃、桃子、梨、柚子、蓝莓、樱桃、龙眼、荔枝、山竹、火龙果、哈密瓜、石榴 |
| 饮品 | ~12 | 绿茶、红茶、咖啡、豆浆、牛奶、酸奶、橙汁、可乐、椰汁、奶茶、啤酒、红酒 |
| 西式/快餐 | ~15 | 沙拉、薯条、炸鸡块、蛋糕、饼干、冰淇淋、巧克力、麦片、面包、甜甜圈、华夫饼、派、热狗、墨西哥卷 |
| 零食/坚果 | ~15 | 花生、核桃、杏仁、腰果、瓜子、薯片、果干、蜜饯、月饼、粽子、汤圆、麻花、芝麻糊、海苔 |
| 调味料/油脂 | ~15 | 酱油、醋、盐、糖、味精、辣椒酱、番茄酱、芝麻油、花生油、橄榄油、黄油、蚝油、豆瓣酱、蜂蜜、果酱 |
| 豆制品 | ~10 | 豆腐、豆浆、豆干、腐竹、毛豆、黄豆、黑豆、红豆、绿豆、扁豆 |
| 蛋奶 | ~8 | 鸡蛋、鸭蛋、鹌鹑蛋、奶酪、芝士、炼乳、奶粉、奶油 |
| 海鲜 | ~10 | 三文鱼、金枪鱼、虾、蟹、蛤蜊、鱿鱼、带鱼、鲈鱼、鳕鱼、海带 |

**数据来源**：中国食物成分表（标准版）、USDA FoodData Central

**扩展机制**：用户可直接编辑 `food_nutrition_db.json` 添加新食物

## 交互流程

### 触发词

"分析食物炎症指数"、"DII 分析"、"食物抗炎评分"、拍照后说"分析这个"

### 流程

1. **接收照片**：用户在对话中发送食物照片
2. **视觉识别**：Claude 读取照片，识别每种食物并估算重量（g）
3. **营养查询**：从 `food_nutrition_db.json` 查找每种食物的 per_100g 营养数据，按重量换算
4. **汇总营养素**：将所有食物的营养素按重量加权求和
5. **DII 计算**：写入 JSON → 运行 Python 脚本 → 读取结果
6. **输出摘要**：手机友好的简洁格式
7. **生成报告**：详细 Markdown 报告保存到 `~/.longerian/data/dii/report.md`

### 手机端输出格式

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

详细报告已保存
```

### Markdown 报告内容

1. 食物识别结果（含置信度）
2. 营养成分明细表（45 项参数）
3. DII 总分及各成分得分
4. 炎症解读（抗炎/中性/促炎 + 建议）
5. 与全球均值的对比

## Python 脚本设计

### 依赖

纯 Python 标准库：`json`、`math`、`sys`、`os`

### 输入

`/tmp/longerian_skill/dii_input.json`

```json
{
  "foods": [
    {"name": "番茄炒蛋", "weight_g": 200},
    {"name": "米饭", "weight_g": 150}
  ],
  "nutrients": {
    "ALCOHOL": 0,
    "KCAL": 580,
    "PROTEIN": 22.5,
    "TOTALFAT": 18.2
  }
}
```

### 输出

`/tmp/longerian_skill/dii_result.json`

```json
{
  "dii_score": -2.35,
  "interpretation": "抗炎饮食",
  "level": "anti_inflammatory",
  "component_scores": {
    "FIBER": {"value": 5.8, "score": -0.42, "direction": "anti"},
    "VITC": {"value": 38.5, "score": -0.18, "direction": "anti"},
    "SATFAT": {"value": 6.2, "score": 0.15, "direction": "pro"}
  },
  "parameters_used": 32,
  "total_parameters": 45,
  "foods": [
    {"name": "番茄炒蛋", "weight_g": 200},
    {"name": "米饭", "weight_g": 150}
  ]
}
```

## 错误处理

| 场景 | 处理方式 |
|------|---------|
| 照片不清晰/非食物 | 提示用户重新拍照 |
| 食物不在数据库中 | Claude 根据食物类型估算营养素，标注"估算" |
| 无法判断重量 | 给出参考范围（如"一碗米饭约 150-200g"） |
| 某些营养素数据缺失 | 跳过该参数，在结果中标注"已使用 X/45 个参数" |
| 参数使用少于 10 个 | 警告"DII 精度较低" |
| Python 未安装 | 提示安装 Python 3.11+ |
| 脚本执行失败 | 输出原始错误信息 |

## 测试策略

### DII 计算正确性

1. 用 R 包 `dietaryindex` 的 `DII()` 函数计算一个已知食物组合的 DII 值
2. 用 Python 脚本计算同一组数据
3. 对比结果是否一致（允许浮点精度误差 < 0.001）

### 测试用例

1. **全参数**（45 项都有值）→ 验证与 R 输出一致
2. **部分参数**（只有 10 项）→ 验证部分参数计算正确
3. **边界值**（所有值 = 全球均值）→ DII 应为 0
4. **极端值**（所有值 = 最大/最小）→ 验证不崩溃

### 端到端测试

拍一张真实食物照片 → 运行完整流程 → 验证输出合理

## 实现计划

1. 创建 `skills/dii-estimator/` 目录结构
2. 实现 `dii_params.json`（45 项 DII 常量）
3. 实现 `dii_calculator.py`（DII 计算核心）
4. 实现 `food_nutrition_db.json`（~215 种食物营养数据）
5. 编写 `SKILL.md`（交互流程定义）
6. 测试验证（与 R 包对比）
