# 强化学习训练配置问题记录

## 问题1: AttributeError: '_reward_dof_pos' 不存在

**错误信息:**
```
AttributeError: 'LeggedRobotField' object has no attribute '_reward_dof_pos'
```

**原因:**
`mybot_v3_config.py` 中 `rewards.scales` 引用了不存在的奖励函数名 `dof_pos`。

**解决方案:**
将 `dof_pos = -0.1` 改为 `dof_error = -0.1`。

**文件位置:** `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_config.py:111`

**相关函数:** `_reward_dof_error()` 在 `legged_robot.py:1764` 中实现

---

## 问题2: AttributeError: '_reward_legs_energy_substeps' 不存在

**错误信息:**
```
AttributeError: 'LeggedRobotField' object has no attribute '_reward_legs_energy_substeps'
```

**原因:**
`mybot_v3_field_config.py` 和 `mybot_v3_field_distill_config.py` 中使用了错误的奖励函数名 `legs_energy_substeps`。

**解决方案:**
将 `legs_energy_substeps = -2e-5` 改为 `energy_substeps = -2e-5`。

**文件位置:**
- `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_config.py:160`
- `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_distill_config.py:156`

**相关函数:** `_reward_energy_substeps()` 在 `legged_robot.py:1747` 中实现

---

## 问题3: 多个奖励函数名称不匹配

**原因:**
从其他项目（如 himloco）复制配置时，引用了当前框架中未实现的奖励函数。

**解决方案:**

| 配置中的名称 | 状态 | 处理方式 |
|---|---|---|
| `lin_vel_y = 0.0` | 无对应函数 | 注释掉（tracking_lin_vel 已覆盖） |
| `joint_power = -2e-5` | 名称错误 | 改为 `energy_substeps = -2e-5` |
| `foot_clearance = -0.02` | 无对应函数 | 注释掉 |
| `smoothness = -0.01` | 无对应函数 | 注释掉 |
| `feet_stumble = -0.0` | 名称不匹配 | 注释掉（正确名应为 stumble） |
| `rear_thigh_pos = -0.2` | 无对应函数 | 注释掉 |

**文件位置:** `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_config.py:84-114`

**验证方法:**
```bash
# 检查所有已实现的奖励函数
grep -n "def _reward_" legged_gym/legged_gym/envs/base/legged_robot.py
grep -n "def _reward_" legged_gym/legged_gym/envs/base/legged_robot_field.py
```

---

## 问题4: AttributeError: 'body_measure_name_order' 不存在

**错误信息:**
```
AttributeError: 'LeggedRobotField' object has no attribute 'body_measure_name_order'
```

**原因:**
`mybot_v3_field_config.py` 使用了 `engaging_block` 观测组件，该组件需要 `body_measure_points` 配置来定义机器人身体各部位的体积采样点，但 `mybot_v3_config.py` 中缺少此配置。

**解决方案:**
在 `MybotV3RoughCfg` 中添加 `sim.body_measure_points` 配置：

```python
class sim( LeggedRobotCfg.sim ):
    body_measure_points = {  # transform are related to body frame
        "body": dict(
            x= [i for i in np.arange(-0.15, 0.151, 0.03)],
            y= [i for i in np.arange(-0.125, 0.126, 0.03)],
            z= [i for i in np.arange(-0.10, 0.101, 0.03)],
            transform= [0., 0., 0., 0., 0., 0.],
        ),
        "thigh": dict(
            x= [-0.16, -0.155, -0.15, -0.145, -0.14, -0.135, -0.13,
                -0.125, -0.12, -0.115, -0.11, -0.105, -0.1, -0.095,
                -0.09, -0.085, -0.08, -0.075, -0.07, -0.065, -0.05,
                0.0, 0.05, 0.1],
            y= [-0.015, 0.0, 0.015],
            z= [-0.03, -0.015, 0.0, 0.015],
            transform= [0., 0., -0.1, 0., 1.57079632679, 0.],
        ),
        "calf": dict(
            x= [i for i in np.arange(-0.13, 0.111, 0.03)],
            y= [-0.015, 0.0, 0.015],
            z= [-0.015, 0.0, 0.015],
            transform= [0., 0., -0.11, 0., 1.57079632679, 0.],
        ),
    }
```

**文件位置:** `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_config.py:125-155`

**注意事项:**
- key 必须是 URDF 中 link name 的子字符串（如 `"body"` 匹配 `<link name="body">`）
- `transform` 格式: `[x, y, z, roll, pitch, yaw]`
- 采样点数量会影响计算性能，需平衡精度和效率

**相关代码:**
- `_init_body_volume_points()` 在 `legged_robot.py:1071` 中使用此配置
- `refresh_volume_sample_points()` 在 `legged_robot.py:1151` 中调用

---

## 问题5: BarrierTrack 障碍物难度过高导致训练崩溃

**训练现象:**
```
Learning iteration 104/3000
Mean reward: -17.60
Mean episode length: 38.91        # 极短（正常应 >500）
timeout_ratio: 0.0002             # 几乎全部提前终止
tracking_lin_vel: 0.0326          # 几乎不前进
num_terminated: 184.5208          # 大量终止
```

**原因:**
BarrierTrack 障碍物难度过高，机器人在训练初期无法学会通过，策略选择"躺平"（立即终止）来避免碰撞惩罚。

**原始配置:**
```python
jump= dict(height= (0.25, 0.35))      # 机器人身高 0.4m，跳跃高度达 87%
leap= dict(length= (0.2, 0.5))        # 跨栏距离过大
stairsup= dict(height= (0.08, 0.15))  # 台阶过高
```

**解决方案:**
降低障碍物难度，平衡训练稳定性和最终目标：

```python
BarrierTrack_kwargs = dict(
    jump= dict(
        height= (0.15, 0.3),      # 最大 30cm（目标）
        depth= (0.05, 0.1),
    ),
    leap= dict(
        length= (0.1, 0.3),       # 降低 40%
        depth= (0.2, 0.4),        # 降低 33%
        height= 0.1,
    ),
    stairsup= dict(
        height= (0.06, 0.1),      # 最大 10cm（目标）
        depth= (0.15, 0.25),
    ),
)
```

**文件位置:** `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_config.py:43-65`

**训练阶段建议:**
- 初期（0-1000 迭代）：降低难度，确保策略学会基本行走
- 中期（1000-2000 迭代）：可适当提高障碍物高度
- 后期（2000+ 迭代）：达到最终目标难度

---

## 问题6: collision 惩罚过高导致策略崩溃

**训练现象:**
```
Learning iteration 82: Mean reward -111.46, Episode length 216
Learning iteration 104: Mean reward -17.60, Episode length 39
# 策略从"学会避免碰撞"退化为"立即终止"
```

**原因:**
`collision` 惩罚权重过高（-10.0），策略发现"立即终止"可以避免累积碰撞惩罚。

**配置对比:**

| 项目 | go2 | mybot_v3（错误） | 差异 |
|---|---|---|---|
| `collision` | **-0.05** | -10.0 | **惩罚高 200 倍** |
| `penetrate_depth` | -0.05 | 无 | 缺少穿透惩罚 |

**解决方案:**
```python
# mybot_v3_field_config.py
class rewards:
    class scales:
        collision = -0.05           # 从 -10.0 降到 -0.05
        penetrate_depth = -0.05     # 新增穿透惩罚
```

**文件位置:** `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_config.py:166-167`

**关键经验:**
- collision 惩罚应该"温和"，允许策略探索
- 过高的惩罚会导致策略选择"保守策略"（不作为）
- 参考 go2 的配置作为基准

---

## 问题7: 碰撞配置与 URDF link name 不匹配

**错误配置:**
```python
# mybot_v3_config.py（错误）
penalize_contacts_on = ["thigh", "calf", "base"]      # ❌ "base" 不存在于 URDF
terminate_after_contacts_on = ["base", "body"]        # ❌ "base" 不存在于 URDF
```

**原因:**
从 go2 配置复制时，未检查 URDF link name 差异：
- go2 URDF: `<link name="base">`
- mybot_v3 URDF: `<link name="body">`

**解决方案:**
```python
# mybot_v3_config.py（正确）
penalize_contacts_on = ["thigh", "calf"]              # ✅ 移除不存在的 "base"
terminate_after_contacts_on = ["body"]                # ✅ 匹配 URDF link name
```

**文件位置:** `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_config.py:78-79`

**验证方法:**
```bash
# 检查 URDF 中的 link name
grep -o 'link name="[^"]*"' legged_gym/resources/robots/mybot_v3/urdf/mybot_v3.urdf
```

**配置对比:**

| 配置项 | go2 | mybot_v3（修正后） |
|---|---|---|
| `penalize_contacts_on` | `["thigh", "calf"]` | `["thigh", "calf"]` ✅ |
| `terminate_after_contacts_on` | `["base"]` | `["body"]` ✅ |
| `collision` | -0.05 | -0.05 ✅ |
| `penetrate_depth` | -0.05 | -0.05 ✅ |

---

## 问题8: z_low 和 z_high 终止条件不适用于障碍穿越任务

**参数含义:**
```python
z_low_kwargs = dict(threshold=0.10)   # 机器人高度 < 0.10m 时终止
z_high_kwargs = dict(threshold=1.5)   # 机器人高度 > 1.5m 时终止
```

**作用:**
- **z_low**: 防止机器人掉到地面以下（穿透地面或掉入坑中）
- **z_high**: 防止机器人飞得太高（异常行为或仿真错误）

**为什么移除:**

1. **BarrierTrack 地形复杂**:
   - 包含跳跃（jump height 0.15-0.3m）、跨栏（leap）等障碍
   - 机器人需要跳跃到不同高度
   - 固定的 z_high 限制会阻碍正常行为

2. **Go2 配置中没有这两个终止条件**:
   ```python
   # go2_field_config.py
   class termination:
       termination_terms = ["roll", "pitch"]  # 只有 roll 和 pitch
       # 没有 z_low 和 z_high
   ```

3. **roll/pitch 已经足够**:
   - 机器人摔倒时 roll/pitch 会超限（threshold=1.4/1.6）
   - 不需要额外的高度限制

4. **out_of_track 更灵活**（仅 distill 配置）:
   - 检测机器人是否在轨道范围内
   - 比固定高度限制更合理

**适用场景对比:**

| 场景 | z_low | z_high | 建议 |
|---|---|---|---|
| **平地行走（Rough）** | ✅ 需要 | ❌ 不需要 | 防止穿透地面 |
| **障碍穿越（Field）** | ❌ 不需要 | ❌ 不需要 | 限制跳跃探索 |
| **复杂地形** | ❌ 不需要 | ❌ 不需要 | 限制探索空间 |

**修改位置:**
- `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_config.py:102-124`
- `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_distill_config.py:105-132`

**修改内容:**
```python
# 修改前
class termination:
    termination_terms = ["roll", "pitch", "z_low", "z_high"]
    z_low_kwargs = dict(threshold=0.10)
    z_high_kwargs = dict(threshold=1.5)

# 修改后（与 Go2 一致）
class termination:
    termination_terms = ["roll", "pitch"]  # 移除 z_low 和 z_high
    roll_kwargs = dict(threshold=1.4)
    pitch_kwargs = dict(threshold=1.6)
```

**关键经验:**
- 障碍穿越任务需要允许机器人在不同高度移动
- 固定的高度限制会阻碍策略学习跳跃、跨栏等技能
- roll/pitch 终止条件已经能有效检测机器人摔倒

---

## 总结：配置迁移最佳实践

1. **奖励函数验证**
   - 从其他项目复制配置后，必须验证所有 reward 名称
   - 使用 `grep "def _reward_"` 检查实际实现的函数
   - 参考 go2_config.py 作为标准配置示例

2. **观测组件依赖**
   - `engaging_block` 需要 `body_measure_points`
   - `height_measurements` 需要 `terrain.measure_heights = True`
   - 检查 `_get_<component>_obs()` 函数的依赖

3. **URDF 匹配**
   - `body_measure_points` 的 key 必须匹配 URDF link name
   - `penalize_contacts_on` 和 `terminate_after_contacts_on` 也需匹配 link name

4. **继承关系**
   - field_config 继承 rough_config
   - distill_config 继承 field_config
   - 修改基类会影响所有子类

---

## 已验证的配置文件

| 文件 | 状态 | 修改内容 |
|---|---|---|
| `mybot_v3_config.py` | ✅ 已修复 | 奖励函数、碰撞配置、body_measure_points |
| `mybot_v3_field_config.py` | ✅ 已修复 | 障碍物难度、collision 权重、penetrate_depth |
| `mybot_v3_field_distill_config.py` | ✅ 已修复 | energy_substeps 名称 |

---

## 修改历史

### 2026-06-09 训练配置修复

**问题发现过程:**
1. 训练第 28 次迭代：collision 惩罚 -28.06（占 95%）
2. 训练第 82 次迭代：collision 降至 -7.67，但 episode length 从 872 降至 216
3. 训练第 104 次迭代：策略崩溃，episode length 仅 39，几乎全部提前终止

**根本原因:**
- collision 惩罚过高（-10.0 vs go2 的 -0.05）
- 障碍物难度过高（jump height 0.35m 达机器人身高 87%）
- 终止条件过严（["base", "body"] vs go2 的 ["base"]）

**修复措施:**
1. 降低 collision 惩罚：-10.0 → -0.05
2. 新增 penetrate_depth = -0.05
3. 降低障碍物难度：jump height 0.25-0.35m → 0.15-0.3m
4. 修正终止条件：["base", "body"] → ["body"]
5. 移除多余的惩罚部位：["thigh", "calf", "base"] → ["thigh", "calf"]

**预期效果:**
- 策略不再选择"躺平"避免惩罚
- Episode length 恢复到正常范围（>500）
- tracking_lin_vel 提升到 >0.5

---

## 参考资源

- Go2 配置示例: `legged_gym/legged_gym/envs/go2/go2_config.py`
- 奖励函数实现: `legged_gym/legged_gym/envs/base/legged_robot.py`
- Field 特有函数: `legged_gym/legged_gym/envs/base/legged_robot_field.py`
- URDF 文件: `legged_gym/resources/robots/mybot_v3/urdf/mybot_v3.urdf`