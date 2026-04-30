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
