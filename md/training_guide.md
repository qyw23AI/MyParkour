# MyBotV3 Parkour Training Guide — ROBOCON 障碍赛五项地形

## 🎯 训练目标（五项障碍赛任务）

| 序号 | 任务                                  | 障碍物类型   | 目标参数                                                                    | 几何原理                                                         |
| ---- | ------------------------------------- | ------------ | --------------------------------------------------------------------------- | ---------------------------------------------------------------- |
| 1    | 翻越**30cm** 高木板/围栏 (Wall) | `hurdle`   | `height=0.3m, depth=0.03~0.05m`                                           | 薄片升高（仅 x=1..depth_px+1），模拟 3-5cm 厚木板                |
| 2    | 稳定上**10cm** 楼梯             | `stairsup` | `height=0.08~0.15m, n_stairs=3`                                           | 迭代阶梯升高，3 级台阶逐级递增                                   |
| 3    | 走**木桥A** (多梁桥)         | `bridge_a` | `beam=40cm, gap=15cm, height=20cm, rotate_90°` | 程序化梁 (跨轨方向) |
| 4    | 走**木桥B** (多梁桥)         | `bridge_b` | `beam=20cm, gap=10cm, height=25cm, rotate_90°` | 程序化梁 (跨轨方向) |
| 5    | 爬**I型台阶**                   | `t_stairs` | `step_height=0.10m, n_steps=4, stair_width=2.0m`                         | 程序化 I-stairs (rotate_90 可选) |

> **重要**: 所有3种地形（bridge_a, bridge_b, t_stairs）均使用**程序化生成**（procedural），不再依赖 STL 文件。支持 `rotate_90` 参数控制方向。Heightfield 无法表示悬空梁结构，因此使用 Triangle Mesh。

**方案：高程点 + TPPO蒸馏训练** — 比深度相机快 **5~10倍**

---

## 📐 地形参数详解（从配置文件提取）

### 两份配置的职责

| 配置              | 文件                                 | 用途                       | num_envs | n_obstacles_per_track |
| ----------------- | ------------------------------------ | -------------------------- | -------- | --------------------- |
| **Teacher** | `mybot_v3_field_config.py`         | 教师策略训练（特权观测）   | 4096     | 4                     |
| **Distill** | `mybot_v3_field_distill_config.py` | 学生策略蒸馏（高程点观测） | 4096     | 5                     |

> 两份配置的障碍物参数**独立设置**。教师用较简单的范围探索，蒸馏用目标难度范围。

---

### 障碍物 1: `hurdle` — 翻越 30cm 木板/围栏

| 参数       | Teacher 配置     | Distill 配置     | 说明                                            |
| ---------- | ---------------- | ---------------- | ----------------------------------------------- |
| `height` | `(0.15, 0.3)`  | `(0.25, 0.35)` | 障碍物高度 (m)，difficulty 从 min→max 线性插值 |
| `depth`  | `(0.03, 0.05)` | `(0.03, 0.05)` | 木板厚度 (m)，3-5cm 薄木板                      |

**几何实现** (`barrier_track.py:569-573`)：

```python
track_heightfield[1:depth_px+1, wall_thickness_px:-wall_thickness_px] += height_value
```

仅升高 x=[1, depth_px+1] 的薄片区域 → 薄木板，而非全高台。

**关键区别 `jump` vs `hurdle`**：

```
jump (全高台):                    hurdle (薄木板):
+-----+                          +-----+
|     |  ← 机器人站上去            |███|  ← 机器人跨过去
|     |  整个 block 升高           |███|  仅 3-5cm 薄片
|     |                          |███|
+-----+                          +-----+
  [1:, ...] += height               [1:depth_px+1, ...] += height
```

---

### 障碍物 2: `stairsup` — 稳定上 10cm 楼梯

| 参数         | Teacher 配置     | Distill 配置     | 说明                  |
| ------------ | ---------------- | ---------------- | --------------------- |
| `height`   | `(0.06, 0.1)`  | `(0.08, 0.15)` | 每级台阶高度 (m)      |
| `depth`    | `(0.15, 0.25)` | `(0.1, 0.3)`   | 每级台阶深度/长度 (m) |
| `n_stairs` | `3`            | `3`            | 固定 3 级台阶         |

**几何实现** (`barrier_track.py:884-893`)：

```python
for i in range(int(n_steps)):
    track_heightfield[
        step_length_px*i+1 : step_length_px*(i+1)+1, ...
    ] += height_px * (i+1)
```

第 1 级 +1×height，第 2 级 +2×height，第 3 级 +3×height → 逐级升高。

总高度：3 级 × (8~15cm) = **24~45cm** 总爬升。

---

### 障碍物 3: `bridge_a` — 木桥A（多梁桥，程序化生成）

**实现**: 程序化梁 (procedural)，梁沿 X 轴（轨方向），自动填满 track_width。

| 参数              | Teacher 配置     | Distill 配置 | 说明                     |
| ----------------- | ---------------- | ------------ | ------------------------ |
| `n_beams`       | `5`            | `5`        | 标识（实际数量自动计算） |
| `beam_width`    | `(0.30, 0.50)` | `0.40`     | 每根梁宽度 (m)，标称 40cm |
| `gap_width`     | `(0.10, 0.20)` | `0.15`     | 梁间间隙 (m)，标称 15cm   |
| `bridge_height` | `(0.10, 0.30)` | `0.20`     | 梁高于地面 (m)           |
| `bridge_length` | `(1.5, 2.5)`   | `2.2`      | 梁沿前进方向长度 (m)     |

**三角网格构建** (`bridge_mesh.py:create_bridge_mesh()` with `rotate_90=False`):

```
纯梁 mesh（无地面/侧壁/平台）:
  └── N 根独立梁 (桥高度, 居中对齐, 填满 track_width)
      梁数 N = (track_width + gap_width) / (beam_width + gap_width)
```

**横截面示意图（俯视）**:

```
┌──────────────────────────────────────┐  ← track_width (2.4~3.0m)
│                                      │
│  ████  _  ████  _  ████  _  ████     │  ← 4 梁 3 隙
│  ████  _  ████  _  ████  _  ████     │     梁宽 40cm, 隙宽 15cm
│  ████  _  ████  _  ████  _  ████     │     梁长 2.2m, 高 20cm
│                                      │
└──────────────────────────────────────┘
```

**关键设计**:
- 梁间间隙是**真实的空区域**（无 mesh），机器人踩入会坠落
- Heightfield 仍生成（用于高程点观测），beam 区域升高到 bridge_height
- 物理碰撞由 Triangle Mesh 处理，精确模拟悬空梁

---

### 障碍物 4: `bridge_b` — 木桥B（多梁桥，程序化生成，rotate_90）

**实现**: 程序化梁 (procedural)，梁沿 Y 轴（跨轨方向，`rotate_90=True`），自动填满 track_block_length。长边与列 (col) 方向平行。

| 参数              | Teacher 配置     | Distill 配置 | 说明                                        |
| ----------------- | ---------------- | ------------ | ------------------------------------------- |
| `n_beams`       | `3`            | `3`        | 标识（实际数量自动计算）                    |
| `beam_width`    | `(0.15, 0.25)` | `0.20`     | 每根梁宽度沿 X (m)，标称 20cm               |
| `gap_width`     | `(0.05, 0.15)` | `0.10`     | 梁间间隙沿 X (m)，标称 10cm                 |
| `bridge_height` | `(0.10, 0.30)` | `0.25`     | 梁高于地面 (m)，25cm 比 Bridge A 更高       |
| `rotate_90`     | `True`         | `True`     | 梁沿 Y 轴（跨轨），长边平行于列             |

**三角网格构建** (`bridge_mesh.py:create_bridge_mesh()` with `rotate_90=True`):

```
纯梁 mesh（无地面/侧壁/平台）:
  └── N 根独立梁 (桥高度, 居中对齐, 填满 track_block_length)
      每根梁: Y 方向跨度 = track_width (整宽), X 方向宽度 = beam_width
      梁数 N = (track_block_length + gap_width) / (beam_width + gap_width)
```

**横截面示意图（俯视, 梁沿 Y）**:

```
┌──────────────────────────────────────┐  ← track_width (2.4~3.0m)
│  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃    │  ← 8 梁 7 隙
│  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃    │     梁宽 20cm (X), 隙宽 10cm
│  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃    │     梁长 = track_width (跨轨)
│  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃  ┃┃    │     高 25cm
└──────────────────────────────────────┘
  ← X (轨方向): 填满 track_block_length →
```

**Bridge A vs Bridge B 对比**:

| 特性       | Bridge A            | Bridge B                 |
| ---------- | ------------------- | ------------------------ |
| 梁方向     | 沿 X (轨方向)       | 沿 Y (跨轨方向)          |
| 梁宽       | 40cm                | 20cm (沿 X)              |
| 间隙       | 15cm                | 10cm (沿 X)              |
| 高度       | 20cm                | 25cm                     |
| 长度       | 2.2m (沿 X)         | = track_width (跨整轨)   |
| 填充方向   | Y 方向填满          | X 方向填满               |
| 难度特征   | 间隙更大            | 梁更窄更高，轨方向间隙多 |

**三种 Mesh 构建方式** (`bridge_mesh_source` 参数):

`bridge_a` 和 `bridge_b` 均支持三种三角网格构建方式，通过 `bridge_mesh_source` 参数选择。**当前默认使用 `"procedural"`**。

| `bridge_mesh_source`         | 方式     | 说明                                                                         |
| ------------------------------ | -------- | ---------------------------------------------------------------------------- |
| `"procedural"` **(当前默认)** | 独立梁盒 | 每根梁是独立 box，梁间真实空隙，自动填满                                   |
| `"platform"`                 | 整块平台 | 单块连接平台+空隙（效率更高）                                               |
| `"stl"`                      | STL 文件 | 从 STL 加载桥面几何（需要 STL 文件存在）                                   |

> **注意**: 配置文件位于 `mybot_v3_field_config.py` 和 `mybot_v3_field_distill_config.py`，修改 `beam_width`/`gap_width`/`bridge_height` 即可调整难度。

---

### 障碍物 5: `t_stairs` — T字台阶

**STL 实现**: 使用 `t_shaped_step.stl` 作为 3D 物理几何（`t_stairs_mesh_source="stl"`），等比缩放后与程序化地面/侧壁组合。Heightfield 仍按原逻辑生成供高程点观测。

| 参数               | Teacher 配置     | Distill 配置 | 说明                   |
| ------------------ | ---------------- | ------------ | ---------------------- |
| `step_height`    | `(0.05, 0.15)` | `0.10`     | 每级台阶高度 (m)       |
| `step_depth`     | `(0.15, 0.25)` | `0.20`     | 每级台阶深度 (m)       |
| `n_steps`        | `4`            | `4`        | 台阶数 (4级→40cm总高) |
| `stair_width`    | `(0.6, 1.0)`   | `0.80`     | 台阶宽度 (m, 居中)     |
| `platform_width` | `0.8`          | `0.80`     | 顶部平台尺寸 (m)       |

**几何实现** (`barrier_track.py:get_t_stairs_track()`):

```python
for i in range(n_steps):
    track_heightfield[
        step_depth_px*i+1 : step_depth_px*(i+1)+1,
        track_mid - half_width : track_mid + half_width,
    ] += step_height_px * (i+1)
```

只在中央 y-range 逐级升高，两侧保持 0 → T形结构。

**横截面示意图（俯视 + 侧视）**:

```
侧视 (X=前进方向):
  0.1     0.2     0.3     0.4     ← 逐级升高
  ██      ██      ██      ██
  ██  ██  ██  ██  ██  ██  ██████  ← 4级台阶 + 平台

俯视:
┌──────────────────────────────────────┐
│            ┌──────┐                  │  ← 平台 0.8×0.8m
│       ╔════╝      ╚════╗             │  ← T形台阶(中央0.8m宽)
│       ║                ║             │
└──────────────────────────────────────┘
```

---

### 轨道公共参数

| 参数                         | Teacher 配置    | Distill 配置    | 说明                            |
| ---------------------------- | --------------- | --------------- | ------------------------------- |
| `track_width`              | `2.4`         | `3.0`         | 轨道总宽度 (m)                  |
| `track_block_length`       | `2.4`         | `1.8`         | 每个障碍块长度 (m)              |
| `wall_thickness`           | `(0.04, 0.2)` | `(0.2, 1.0)`  | 轨道侧壁厚度 (m)                |
| `wall_height`              | `0.3`         | `(-0.5, 0.5)` | 轨道侧壁高度 (m)，负值=低于地面 |
| `n_obstacles_per_track`    | `4`           | `5`           | 每条轨道障碍物数量              |
| `randomize_obstacle_order` | `True`        | `True`        | 随机排列障碍物顺序              |
| `add_perlin_noise`         | `True`        | `True`        | 启用 Perlin 噪声                |
| `curriculum_perlin`        | `False`       | `False`       | Perlin 噪声不随 difficulty 变化 |

### Perlin 噪声

| 配置    | zScale          | frequency |
| ------- | --------------- | --------- |
| Teacher | `[0.0, 0.03]` | `10`    |
| Distill | `[0.0, 0.02]` | `10`    |

噪声幅度已从原来的 `[0.08, 0.15]`（8-15cm）降低到 `[0.0, 0.03]`（0-3cm），确保不会淹没断层 gap。

---

## 🔍 地形满足度评估

### Task 1: 高墙/Wall (hurdle) ✅ 满足

| 检查项          | 状态 | 说明                                            |
| --------------- | ---- | ----------------------------------------------- |
| 障碍物类型      | ✅   | `hurdle`（薄木板），非 `jump`（高台）       |
| 木板厚度        | ✅   | `depth=(0.03, 0.05)` → 3-5cm，符合薄木板要求 |
| 高度（Distill） | ✅   | `height=(0.25, 0.35)` → 覆盖 30cm 目标       |
| 高度（Teacher） | ✅   | `height=(0.2, 0.35)` → 已修正，聚焦 30cm     |

---

### Task 2: 10cm 楼梯 (stairsup) ✅ 满足

| 检查项              | 状态 | 说明                                      |
| ------------------- | ---- | ----------------------------------------- |
| 台阶高度（Distill） | ✅   | `height=(0.08, 0.15)` → 覆盖 10cm      |
| 台阶高度（Teacher） | ✅   | `height=(0.08, 0.15)` → 已对齐 Distill |
| 台阶数量            | ✅   | `n_stairs=3`                            |

---

### Task 3: 木桥A (bridge_a) ✅ 程序化梁

| 检查项           | 状态 | 说明                                                                          |
| ---------------- | ---- | ----------------------------------------------------------------------------- |
| 3D 物理几何      | ✅   | 程序化梁 (N 根独立 box)，梁沿 X 轴，填满 track_width                        |
| 真实间隙         | ✅   | 梁间真实空隙 → 机器人踩空会坠落                                              |
| Distill 参数     | ✅   | beam=40cm, gap=15cm, 高20cm, 长2.2m                                          |
| Teacher 随机化   | ✅   | `beam_width=(0.30,0.50)`, `gap_width=(0.10,0.20)`, `height=(0.10,0.30)` |
| Heightfield 观测 | ✅   | 梁区域升高到 bridge_height 供高程点采样                                       |

---

### Task 4: 木桥B (bridge_b) ✅ 程序化梁 (rotate_90)

| 检查项           | 状态 | 说明                                                                          |
| ---------------- | ---- | ----------------------------------------------------------------------------- |
| 3D 物理几何      | ✅   | 程序化梁 (N 根独立 box)，梁沿 Y 轴（跨轨），填满 track_block_length          |
| 真实间隙         | ✅   | 梁间真实空隙 → 机器人踩空会坠落                                              |
| Distill 参数     | ✅   | beam=20cm (沿 X), gap=10cm (沿 X), 高25cm                                    |
| Teacher 随机化   | ✅   | `beam_width=(0.15,0.25)`, `gap_width=(0.05,0.15)`, `height=(0.10,0.30)` |
| Heightfield 观测 | ✅   | 梁区域升高到 bridge_height 供高程点采样                                       |

---

### Task 5: T字台阶 (t_stairs) ✅ STL 实现

| 检查项           | 状态 | 说明                                                   |
| ---------------- | ---- | ------------------------------------------------------ |
| 3D 物理几何      | ✅   | STL 模型 (`t_shaped_step.stl`) + 程序化地面/侧壁     |
| Heightfield 观测 | ✅   | 中央 4 级台阶 + 顶部平台（高度场仍按原逻辑生成）       |
| Distill 参数     | ✅   | 10cm×4级=40cm 总高, 80cm 宽                           |
| Teacher 随机化   | ✅   | `step_height=(0.05,0.15)`, `stair_width=(0.6,1.0)` |

---

## ⚠ 发现的潜在问题

### 问题 1: Teacher 缺少障碍物特定终止阈值

**位置**: `mybot_v3_field_config.py:112-118`

```python
roll_kwargs = dict(threshold=1.4)
pitch_kwargs = dict(threshold=1.6)
check_obstacle_conditioned_threshold = True
```

教师配置没有障碍物特定的终止阈值（如 `hurdle_threshold`、`tilt_threshold` 等），所有障碍物统一使用默认 1.4 rad (80°) 的 roll 阈值。对比 Distill 配置：

```python
roll_kwargs = dict(
    threshold=0.8,
    stairsup_threshold=0.8,
    hurdle_threshold=0.8,
    bridge_a_threshold=0.8,
    bridge_b_threshold=0.8,
    t_stairs_threshold=0.8,
    ...
)
```

**影响**：教师训练时，窄桥上机器人可以倾斜 80° 才终止，过于宽松。但这可能是有意为之（让教师有更大探索空间）。

---

### 问题 2: Distill 配置 `wall_height` 范围包含负值

**位置**: `mybot_v3_field_distill_config.py:49`

```python
wall_height=(-0.5, 0.5),
```

轨道侧壁高度随机范围 -0.5m ~ 0.5m。当采样到负值时，轨道侧壁低于地面（不可见）。这是 BarrierTrack 的标准做法（低难度时侧壁低/负，高难度时侧壁高），但可能让地形看起来"没有边界"。

> **注意**：这不影响 tilt 窄桥的桥墙（桥墙使用 `tilt.wall_height=0.5` 独立参数）。

---

### 问题 3: `n_obstacles_per_track` 影响障碍物覆盖率

| 配置    | n_obstacles | 5 种类型全出现的概率               |
| ------- | ----------- | ---------------------------------- |
| Teacher | 4           | ~33%（随机抽取 4 次覆盖 5 种类型） |
| Distill | 5           | ~38%（随机抽取 5 次覆盖 5 种类型） |

教师训练时某些 track 可能缺少某种障碍物类型，影响对特定技能的探索。

---

### 问题 4: Distill `wall_thickness=(0.2, 1.0)` 上限过高

1.0m 的侧壁厚度会显著压缩可用轨道宽度（3.0m - 2×1.0m = 1.0m 可用空间）。在 tilt 窄桥上，如果 wall_thickness 采样到大值，tilt 墙和侧壁墙可能重叠。建议上限降到 0.5m。

---

## 📋 配置文件清单（更新后）

| 文件                                 | 状态  | 说明                                                                            |
| ------------------------------------ | ----- | ------------------------------------------------------------------------------- |
| `mybot_v3_config.py`               | ✅ OK | 基础配置，关节 PD 增益、默认姿态                                                |
| `mybot_v3_field_config.py`         | ✅ OK | Teacher 训练配置，5 种障碍物，procedural 模式                                     |
| `mybot_v3_field_distill_config.py` | ✅ OK | Distill 配置，5 种障碍物，procedural 模式                                     |
| `legged_robot_field.py`            | ✅ OK | reward 函数兼容 hurdle+jump                                                     |
| `play.py`                          | ✅ OK | options 列表已更新为 `["hurdle","stairsup","bridge_a","bridge_b","t_stairs"]` |
| `terrain_viewer.py`                | ✅ OK | 纯地形可视化脚本，不加载机器人                                                  |
| `__init__.py`                      | ✅ OK | 任务注册正确                                                                    |

---

## 🔄 完整训练流程

### 第一步：训练教师策略

```bash
cd /home/qyw/MyParkour

python legged_gym/legged_gym/scripts/train.py \
    --task=mybot_v3_field \
    --headless
```

**输出位置**：

```
logs/field_mybot_v3/
  └─ <timestamp>_JLC_obstacles/
      ├─ config.json
      └─ model_*.pt
```

训练到 `model_4500.pt` 或 `model_5000.pt` 就可以停止，进入下一步。

---

### 第二步：收集演示数据集

假设你训练完得到的日志目录是：`Jun08_10-30-00_JLC_obstacles`

```bash
python legged_gym/legged_gym/scripts/collect.py \
    --task=mybot_v3_field \
    --load_run=Jun08_10-30-00_JLC_obstacles \
    --checkpoint=4500 \
    --headless
```

收集完成后，数据集目录生成在：`logs/distill_mybot_v3/<generated_dir>/`

---

### 第三步：修改配置填入路径

编辑 `mybot_v3_field_distill_config.py`，填入数据集路径和教师模型路径：

```python
# Line ~185: 数据集路径
class pretrain_dataset:
    scan_dir = "logs/distill_mybot_v3/<你的生成目录>"

# Line ~217: 教师模型路径
teacher_ac_path = "logs/field_mybot_v3/<你的训练目录>/model_4500.pt"
```

---

### 第四步：训练学生策略（蒸馏）

```bash
python legged_gym/legged_gym/scripts/train.py \
    --task=mybot_v3_distill \
    --headless
```

**输出位置**：`logs/distill_mybot_v3/<your_run_dir>/`

推荐用 `model_70000.pt` 或者 `model_80000.pt` 做测试。

---

### 第五步：测试可视化（GUI）

不要加 `--headless`：

```bash
python legged_gym/legged_gym/scripts/play.py \
    --task=mybot_v3_distill \
    --load_run=<distill日志目录名> \
    --checkpoint=70000
```

---

## 🖼️ 地形预览（不加载机器人）

使用 `terrain_viewer.py` 在训练前预览地形：

```bash
# 默认：四种 Parkour 障碍物
python legged_gym/legged_gym/scripts/terrain_viewer.py

# 查看全部 14 种障碍物
python legged_gym/legged_gym/scripts/terrain_viewer.py --options all --num-rows 2 --num-cols 7

# 不开启 Perlin 噪声（清晰查看地形几何）
python legged_gym/legged_gym/scripts/terrain_viewer.py --perlin-noise

# 自定义障碍物参数
python legged_gym/legged_gym/scripts/terrain_viewer.py \
    --options hurdle,stairsup,bridge_a,bridge_b,t_stairs \
    --track-width 3.0 --track-block-length 1.8 \
    --difficulty 0.7
```

---

## ⏱️ 时间预估（按显卡）

| 阶段             | RTX 3090 (24GB)    | RTX 4090 (24GB)       |
| ---------------- | ------------------ | --------------------- |
| 第一步：训练教师 | 2.5 ~ 3 天         | 1 ~ 1.5 天            |
| 第二步：收集数据 | 2 ~ 4 小时         | 1 ~ 2 小时            |
| 第三步：训练学生 | 1 ~ 2 天           | 0.5 ~ 1 天            |
| **总计**   | **4 ~ 5 天** | **~2.5 ~ 3 天** |

> 如果显存不够，把教师 `num_envs` 改成 `2048`，时间约加倍。

---

## ⚠️ 常见问题

### 1. 显存溢出 (CUDA out of memory)

把 `num_envs` 减半（4096 → 2048）。

### 2. 训练初期机器人不往前走

正常现象，前几百迭代可能一直摔倒，`alive=2.0` 奖励会鼓励前进。

### 3. 单边桥总是摔

增大 `tilt.width` 最小值，如 `(0.25, 0.45)`；或延长蒸馏训练到 10 万 iteration。

### 4. 收集数据速度慢

在 collect.py 中减小 `num_rows` 和 `num_cols`。

---

## 📊 观测空间说明（高程点方案）

学生策略只需要两个观测分量：

| 分量                    | 维度 | 说明                                                 |
| ----------------------- | ---- | ---------------------------------------------------- |
| `proprioception`      | 48   | 关节位置/速度、基座线速度/角速度、重力投影、上一动作 |
| `height_measurements` | 187  | 机器人前方地形高程点采样 (17 × 11)                  |

- **不需要深度相机**，纯 proprioception + 高程点
- **所有五种障碍物都能被高程点检测到**：
  - 木板 → 前方高度升高 ✓
  - 楼梯 → 前方阶梯升高 ✓
  - 多梁桥 → 前方梁高间隙交替 ✓
  - T字台阶 → 中央阶梯升高，两侧为地面 ✓

---

## ✅ 总结

| 项目               | 状态                                                                              |
| ------------------ | --------------------------------------------------------------------------------- |
| 高墙/Wall (hurdle) | ✅ 几何正确，参数对齐 30cm                                                        |
| 楼梯 (stairsup)    | ✅ Teacher 参数已对齐 Distill (8-15cm)                                            |
| 多梁桥A (bridge_a) | ✅**程序化梁** — 梁沿 X 轴, beam=40cm, gap=15cm, 高20cm |
| 多梁桥B (bridge_b) | ✅**程序化梁 (rotate_90)** — 梁沿 Y 轴, beam=20cm, gap=10cm, 高25cm |
| T字台阶 (t_stairs) | ✅**STL 实现** — `t_shaped_step.stl`, 4级×10cm, 80cm宽                  |
| 断层 (leap)        | ❌ 已移除                                                                         |
| Perlin 噪声        | ✅ 已降至 0-3cm                                                                   |
| mesh_type 冲突     | ✅ 修正完成                                                                       |
| play.py 障碍物列表 | ✅ 已更新                                                                         |
| reward 函数兼容性  | ✅ hurdle+jump 双重检测                                                           |
| terrain_viewer.py  | ✅ 已创建                                                                         |
| 教师蒸馏框架       | ✅ 就绪                                                                           |
| 训练命令           | ✅ 准备好                                                                         |
