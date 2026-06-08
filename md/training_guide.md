# MyBotV3 Parkour Training Guide - 四个任务完整训练流程

## 🎯 训练目标

| 序号 | 任务 | 障碍物类型 | 参数设置 |
|------|------|------------|----------|
| 1 | 翻越 **30cm** 高木板 | `jump` | `height=(0.25, 0.35)` |
| 2 | 过 **中间断层** 平地 | `leap` | `length=(0.2, 0.5)` |
| 3 | 稳定上 **10cm** 楼梯 | `stairsup` | `height=(0.08, 0.15), n_stairs=3` |
| 4 | **走单边桥（窄桥）** | `tilt` | `width=(0.15, 0.35), opening_angle=0.0` (两侧木板，中间镂空) |

**方案：高程点 + TPPO蒸馏训练** - 比深度相机快 **5~10倍**

---

## 📋 代码审查结果（三次审查）

> **详细维度审查报告**：请查看 [dimension_audit.md](file:///home/qyw/MyParkour/md/dimension_audit.md)

### ✅ 已修正问题（共 8 个）

| # | 问题 | 影响 | 文件 | 修正 |
|---|------|------|------|------|
| 1 | `engaging_block` 维度少算 | 教师策略输入维度不对，训练会 crash | [mybot_v3_field_distill_config.py:246](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_distill_config.py#L246) | `(1+(2+1)+2)` → `(1+(4+1)+2)` = 8维 |
| 2 | `mesh_type = "trimesh"` 与 BarrierTrack 冲突 | BarrierTrack 断言要求 `mesh_type = None`，启动直接报错 | [mybot_v3_field_config.py:18](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_config.py#L18) | `mesh_type = "trimesh"` → `mesh_type = None` |
| 3 | `climb` 不是 BarrierTrack 支持的障碍物 | 启动时 KeyError，地形生成失败 | 所有配置文件 | `climb` → `stairsup`（BarrierTrack 内置的上楼梯障碍物） |
| 4 | `teacher_policy_class_name = "ActorCriticClimbMutex"` | collect.py 加载 teacher 时 class 不匹配，crash | [mybot_v3_field_distill_config.py:236](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_distill_config.py#L236) | → `"ActorCriticRecurrent"`（与教师训练一致） |
| 5 | `play.py` 硬编码覆盖障碍物列表 | 测试时不会出现 `stairsup` 和 `tilt` | [play.py:96](file:///home/qyw/MyParkour/legged_gym/legged_gym/scripts/play.py#L96) | 改为 `["jump", "leap", "stairsup", "tilt"]` |
| 6 | **distill 配置中 `options` 仍有 `climb`** | merge_dict 完全覆盖导致教师配置的 `stairsup` 被覆盖 | [mybot_v3_field_distill_config.py:43](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_distill_config.py#L43) | `climb` → `stairsup` |
| 7 | **teacher_policy 维度严重错误** | `num_actor_obs=81` 但环境实际输出 `235` 维，MLP 输入维度不匹配，训练 crash | [mybot_v3_field_distill_config.py:239-240](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_distill_config.py#L239-L240) | `num_actor_obs = 81` → `276`，`num_critic_obs = 81` → `276` |
| 8 | **teacher_policy engaging_block 维度错误** | 实际环境生成 203 维 `(1+200+2)`，配置写的是 8 维 | [mybot_v3_field_distill_config.py:243](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_distill_config.py#L243) | `(1+(4+1)+2)` → `(1+200+2)` |

### ✅ 维度计算验证

**学生环境观测维度：**
```
num_obs (学生可见) = 48 (proprioception) + 187 (height_measurements) = 235 ✓
num_privileged_obs (教师特权) = 48 + 6 + 17 + 203 + 2 = 276 ✓
```

**教师策略维度（修正后）：**
```
num_actor_obs = 276 ✓
num_critic_obs = 276 ✓
obs_segments = 48 + 6 + 17 + 203 + 2 = 276 ✓
```

**obs_segments 详细：**
| 分量 | 维度 | 说明 |
|------|------|------|
| proprioception | 48 | 基座线速度/角速度/重力投影/关节位置/速度/上一动作 |
| base_pose | 6 | 基座位姿 xyz + rpy |
| robot_config | 17 | 1+3+1+12 = mass+inertia+length+dof limit |
| engaging_block | 203 | 1 + 200 (max_track_options) + 2 (block_info_dim) |
| sidewall_distance | 2 | 左右离墙距离 |
| **TOTAL** | **276** | |

### ✅ 配置清单

| 文件 | 状态 | 说明 |
|------|------|------|
| [mybot_v3_config.py](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/mybot_v3/mybot_v3_config.py) | ✅ OK | 基础配置，关节PD增益、默认姿态 |
| [mybot_v3_field_config.py](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_config.py) | ✅ OK | 教师训练配置，包含四个障碍物 |
| [mybot_v3_field_distill_config.py](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_distill_config.py) | ✅ OK | 学生蒸馏配置，高程点观测 |
| [__init__.py](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/__init__.py) | ✅ OK | 任务注册正确 |
| [play.py](file:///home/qyw/MyParkour/legged_gym/legged_gym/scripts/play.py) | ✅ OK | 测试时障碍物列表已修正 |
| URDF文件 | ✅ OK | 不需要深度相机，不修改 |

### ✅ 关键参数验证

- **Teacher**: `num_envs=4096`, `max_iterations=5000`, `measure_heights=True` ✓
- **Student**: `num_envs=2048`, `num_obs=235`, `privileged_obs=276`, `max_iterations=80000`, `obs_components=["proprioception", "height_measurements"]` ✓
- **Teacher Policy (Distill)**: `num_actor_obs=276`, `num_critic_obs=276`, `obs_segments=276` ✓
- **BarrierTrack**: 四个障碍物 `["jump", "leap", "stairsup", "tilt"]` ✓
- **单边桥（tilt）**: `opening_angle=0` → 平桥，正好符合需求 ✓
- **终止条件**: 每个障碍物都有对应的roll/pitch/z阈值 ✓
- **teacher_policy_class_name**: `ActorCriticRecurrent`（与教师训练一致）✓
- **collect.py teacher class**: `ActorCriticRecurrent`（与教师训练一致）✓

**结论：代码完整，所有问题已修正，可以直接开始训练！**

---

## ⏱️ 时间预估（按显卡）

| 阶段 | RTX 3090 (24GB) | RTX 4090 (24GB) |
|------|-----------------|-----------------|
| 第一步：训练教师 | 2.5 ~ 3 天 | 1 ~ 1.5 天 |
| 第二步：收集数据 | 2 ~ 4 小时 | 1 ~ 2 小时 |
| 第三步：训练学生 | 1 ~ 2 天 | 0.5 ~ 1 天 |
| **总计** | **4 ~ 5 天** | **~2.5 ~ 3 天** |

> 如果显存不够，把教师 `num_envs` 改成 `2048`，时间约加倍。

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

**参数说明**：
- `--checkpoint=4500` → 选最后几个 checkpoint 就行
- 收集完成后，会生成数据集目录在：
```
logs/distill_mybot_v3/<generated_dir>/
```

比如：`Jun08_15-30-00_jumpleapstairuptilt_...`

---

### 第三步：修改配置填入路径

编辑 [mybot_v3_field_distill_config.py](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_distill_config.py)，找到这两行：

```python
# Line ~225: 数据集路径
class pretrain_dataset:
    scan_dir = "logs/distill_mybot_v3/<你的生成目录>"

# Line ~237: 教师模型路径
teacher_ac_path = "logs/field_mybot_v3/<你的训练目录>/model_4500.pt"
```

示例：
```python
class pretrain_dataset:
    scan_dir = "logs/distill_mybot_v3/Jun08_15-30-00_jumpleapstairuptilt_fric0.0-2.0"

teacher_ac_path = "logs/field_mybot_v3/Jun08_10-30-00_JLC_obstacles/model_4500.pt"
```

---

### 第四步：训练学生策略（蒸馏）

```bash
python legged_gym/legged_gym/scripts/train.py \
    --task=mybot_v3_distill \
    --headless
```

**输出位置**：
```
logs/distill_mybot_v3/
  └─ <your_run_dir>/
      ├─ config.json
      └─ model_*.pt
```

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

比如：
```bash
python legged_gym/legged_gym/scripts/play.py \
    --task=mybot_v3_distill \
    --load_run=Jun09_10-00-00_... \
    --checkpoint=70000
```

在 Isaac Gym 可视化中你应该能看到：
- 机器人尝试翻越 30cm 木板
- 机器人跳过中间断层
- 机器人稳定走上 10cm 楼梯
- 机器人走窄桥（单边桥）只踩两边木板，不踩中间空隙

---

## 📐 地形参数说明

### 单边桥 (tilt) 参数

```python
tilt= dict(
    width= (0.15, 0.35),      # 中间可通行宽度（单位：米）
    depth= (0.8, 1.5),       # 桥沿前进方向长度（米）
    opening_angle= 0.0,      # ⬅️ 关键！0就是平桥，不是斜的
    wall_height= 0.5,        # 两侧侧板高度
)
```

**横截面示意图（从机器人正前方看）**：

```
┌───────────────────────────────────────────┐  ← 总宽度 1.6m
│                                            │
│  ████████████        gap (镂空)     ████████████  ← 左右两块木板
│  ████████████                      ████████████
│            ↑         ↑                       │
│            |< 15~35cm >|                   │
│                                            │
│                                            │
└───────────────────────────────────────────┘
```

正好满足你说的：**两边有木板，中间是空的**，机器人需要避免踩到中间的空。

---

### 其他障碍物参数

| 障碍物 | 参数 | 范围说明 |
|--------|------|----------|
| **jump** (30cm木板) | `height=(0.25, 0.35)` | 正好覆盖 30cm 木板高度 |
| **leap** (断层) | `length=(0.2, 0.5)` | 断层宽度 20~50cm |
| **stairsup** (10cm楼梯) | `height=(0.08, 0.15), n_stairs=3` | 正好覆盖 10cm 楼梯高度，3级台阶 |

---

## ⚠️ 可能遇到的问题与解决

### 1. 显存溢出 (CUDA out of memory)

**解决**：减小 `num_envs`

编辑 [mybot_v3_field_config.py](file:///home/qyw/MyParkour/legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_config.py#L8)：
```python
class env( MybotV3RoughCfg.env ):
    num_envs = 2048  # 原来 4096 改成 2048，显存减少约一半
```

时间会变长，但结果质量差不多。

---

### 2. 训练初期机器人不往前走

这是正常的：
- 前几百迭代机器人可能一直摔倒
- 随着训练，会逐渐学会往前走
- 奖励中 `alive = 2.` 会鼓励它继续走

---

### 3. 单边桥总是摔

- 如果训练完还是不稳，可以：
  1. 增大 `tilt.width` 的最小值，比如改成 `(0.25, 0.45)`
  2. 延长训练迭代，学生训练到 10万 iteration
  3. 收集更多演示数据

---

### 4. 收集数据速度很慢

这正常，因为 `env_cfg.terrain.num_rows = 8; env_cfg.terrain.num_cols = 40` 就是 320 个环境同时跑。如果很慢，可以在 `collect.py` 开头改小：

```python
env_cfg.terrain.num_rows = 4; env_cfg.terrain.num_cols = 20
```

---

## 📊 观测空间说明（高程点方案）

学生策略只需要两个观测分量：

| 分量 | 维度 | 说明 |
|------|------|------|
| `proprioception` | 48 | 关节位置/速度、基座线速度/角速度、重力投影、上一动作 |
| `height_measurements` | 187 | 机器人前方地形高程点采样 (17 × 11) |

- **不需要深度相机！** 完全纯 proprioception + 高程点
- **计算量小**，推理快，部署简单
- **所有四个障碍物都能被高程点检测到**：
  - 木板 → 前方高度升高 ✓
  - 断层 → 前方高度突然降低 ✓
  - 楼梯 → 前方阶梯升高 ✓
  - 单边桥 → 两侧高度正常，中间低 ✓

---

## 🚀 部署到实机

因为你用的是高程点方案：
1. 和你之前 `himloco` 部署流程几乎一样
2. 只需要：IMU + 关节编码器 + 地形高程地图（可以从激光雷达建图得到）
3. 不需要实时深度相机推理，计算量小很多

---

## ✅ 总结

| 项目 | 状态 |
|------|------|
| 四个任务配置 | ✅ 完成 |
| 单边桥地形设置 | ✅ 完成 |
| mesh_type 冲突 | ✅ 修正完成 |
| climb → stairsup | ✅ 修正完成 |
| teacher_policy_class_name | ✅ 修正完成 |
| play.py 障碍物列表 | ✅ 修正完成 |
| distill options 中 climb | ✅ 修正完成 |
| teacher_policy 维度 (81→276) | ✅ 修正完成 |
| teacher obs_segments 维度 (8→203) | ✅ 修正完成 |
| teacher-student 框架 | ✅ 就绪 |
| 高程点方案 | ✅ 配置完成 |
| 训练命令 | ✅ 准备好 |

**可以直接开始第一步训练了！**