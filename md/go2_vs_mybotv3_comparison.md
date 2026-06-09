# Go2 vs MybotV3 配置详细对照表

## 1. 奖励函数权重对照

### 1.1 Rough 配置（基础行走）

| 奖励函数 | go2_rough | mybot_v3_rough | 差异分析 |
|---|---|---|---|
| **tracking_lin_vel** | 1.0 | **2.0** | ⚠️ mybot_v3 高 2 倍 |
| **tracking_ang_vel** | 1.0 | **0.5** | mybot_v3 低 50% |
| **energy_substeps** | -2e-5 | -2e-5 | ✅ 相同 |
| **stand_still** | -2.0 | **0.0** | ⚠️ go2 惩罚站立不动 |
| **dof_error_named** | -1.0 | **无** | ⚠️ mybot_v3 缺少髋关节惩罚 |
| **dof_error** | -0.01 | **-0.1** | ⚠️ mybot_v3 高 10 倍 |
| **exceed_dof_pos_limits** | -0.4 | **0.0** | ⚠️ go2 惩罚关节超限 |
| **exceed_torque_limits_l1norm** | -0.4 | **0.0** | ⚠️ go2 惩罚力矩超限 |
| **dof_vel_limits** | -0.4 | **0.0** | ⚠️ go2 惩罚速度超限 |
| lin_vel_z | 无 | -2.0 | mybot_v3 额外惩罚 |
| ang_vel_xy | 无 | -0.05 | mybot_v3 额外惩罚 |
| orientation | 无 | -0.2 | mybot_v3 额外惩罚 |
| dof_acc | 无 | -2.5e-7 | mybot_v3 额外惩罚 |
| base_height | 无 | -1.0 | mybot_v3 额外惩罚 |
| action_rate | 无 | -0.01 | mybot_v3 额外惩罚 |
| feet_air_time | 无 | 0.0 | mybot_v3 额外配置 |
| collision | 无 | 0.0 | mybot_v3 额外配置 |

**关键差异：**
- go2 rough 配置更简洁，只关注速度跟踪和硬件安全
- mybot_v3 rough 配置包含更多惩罚项，可能导致奖励信号混乱

### 1.2 Field 配置（障碍穿越）

| 奖励函数 | go2_field | mybot_v3_field | 差异分析 |
|---|---|---|---|
| **tracking_lin_vel** | 1.0 | **2.0**（继承） | ⚠️ mybot_v3 高 2 倍 |
| **tracking_ang_vel** | 1.0 | **0.05** | ⚠️ mybot_v3 低 20 倍 |
| **energy_substeps** | -2e-7 | **-2e-5** | ⚠️ mybot_v3 高 100 倍 |
| **stand_still** | -1.0 | **0.0**（继承） | ⚠️ go2 惩罚站立不动 |
| **dof_error_named** | -1.0 | **无**（继承） | ⚠️ mybot_v3 缺少 |
| **dof_error** | -0.005 | **-0.1**（继承） | ⚠️ mybot_v3 高 20 倍 |
| **torques** | -1e-7 | **0.0**（继承） | go2 额外惩罚 |
| **collision** | -0.05 | **-0.05** | ✅ 相同 |
| **penetrate_depth** | -0.05 | **-0.05** | ✅ 相同 |
| **lazy_stop** | -3.0 | **无** | ⚠️ go2 惩罚懒惰停止 |
| **exceed_dof_pos_limits** | -0.1 | **-0.1** | ✅ 相同 |
| **exceed_torque_limits_l1norm** | -0.1 | **无** | ⚠️ mybot_v3 用 exceed_torque_limits_i |
| **exceed_torque_limits_i** | 无 | **-0.1** | mybot_v3 用不同的惩罚方式 |
| **alive** | 无 | **2.0** | ⚠️ mybot_v3 存活奖励 |
| **world_vel_l2norm** | 无 | **-1.0** | ⚠️ mybot_v3 额外惩罚 |
| lin_vel_z | 无 | -2.0（继承） | mybot_v3 额外惩罚 |
| ang_vel_xy | 无 | -0.05（继承） | mybot_v3 额外惩罚 |
| orientation | 无 | -0.2（继承） | mybot_v3 额外惩罚 |
| dof_acc | 无 | -2.5e-7（继承） | mybot_v3 额外惩罚 |
| base_height | 无 | -1.0（继承） | mybot_v3 额外惩罚 |
| action_rate | 无 | -0.01（继承） | mybot_v3 额外惩罚 |

**关键差异：**
- go2 field 有 **lazy_stop = -3.0**（惩罚懒惰停止），mybot_v3 没有
- mybot_v3 有 **alive = 2.0**（存活奖励），可能导致策略选择"活着但不前进"
- mybot_v3 的 **tracking_lin_vel = 2.0** 过高，可能导致策略过度追求速度

---

## 2. 穿透惩罚分析

### 2.1 为什么 penetrate_depth = 0？

**配置检查：**
```python
# mybot_v3_field_config.py
virtual_terrain= False        # ✅ 物理碰撞启用
draw_virtual_terrain= True    # 仅可视化，不影响物理
penetrate_depth = -0.05       # ✅ 穿透惩罚已配置
```

**根本原因：**

`_reward_penetrate_depth()` 函数的实现逻辑：
```python
def _reward_penetrate_depth(self):
    if not self.check_BarrierTrack_terrain(): 
        return torch.zeros_like(self.root_states[:, 0])
    self.refresh_volume_sample_points()
    penetration_depths = self.terrain.get_penetration_depths(
        self.volume_sample_points.view(-1, 3)
    ).view(self.num_envs, -1)
    penetration_depths *= torch.norm(self.volume_sample_points_vel, dim= -1) + 1e-3
    return torch.sum(penetration_depths, dim= -1)
```

**关键点：**
1. `virtual_terrain = False` 时，物理引擎会阻止穿透
2. 机器人无法穿透障碍物，所以 `penetrate_depth` 始终为 0
3. `penetrate_depth` 惩罚只在 `virtual_terrain = True` 时有意义

**对比 go2：**
```python
# go2_field_config.py
virtual_terrain= False        # 同样禁用虚拟地形
penetrate_depth = -0.05       # 同样配置了穿透惩罚
```

**结论：**
- ✅ 配置正确，`penetrate_depth = 0` 是正常现象
- ✅ 物理引擎阻止了穿透，不需要穿透惩罚
- ⚠️ 如果想启用穿透惩罚，需要设置 `virtual_terrain = True`（但会失去物理碰撞）

---

## 3. 奖励值分析

### 3.1 当前训练奖励（第9次迭代）

```
Mean reward: 15.31
Mean episode length: 441.02
```

**奖励分解：**
```
tracking_lin_vel: 0.3725      # 正奖励，机器人前进
alive: 0.8606                 # 正奖励，存活时间长
world_vel_l2norm: -0.2226     # 负奖励，世界坐标系速度惩罚
tracking_ang_vel: 0.0163      # 正奖励，角度跟踪
collision: -0.0714            # 负奖励，碰撞惩罚
其他小惩罚: ~-0.1              # 各种小惩罚
```

### 3.2 奖励过高的原因

**问题1：alive = 2.0 过高**
```python
# mybot_v3_field_config.py
alive = 2.0                   # ⚠️ 存活奖励过高

# go2_field_config.py
alive = 无                    # ✅ go2 没有存活奖励
```

**影响：**
- episode length = 441 步 × 0.02秒/步 = 8.82秒
- alive 奖励 = 2.0 × (441 / 1000) ≈ 0.86
- 占总奖励的 5.6%

**问题2：tracking_lin_vel = 2.0 过高**
```python
# mybot_v3_field_config.py
tracking_lin_vel = 2.0        # ⚠️ 速度跟踪奖励过高

# go2_field_config.py
tracking_lin_vel = 1.0        # ✅ go2 使用 1.0
```

**影响：**
- 机器人可能为了追求速度奖励而绕过障碍物
- 不利于学习翻越障碍物的技能

**问题3：缺少 lazy_stop 惩罚**
```python
# go2_field_config.py
lazy_stop = -3.0              # ✅ 惩罚懒惰停止

# mybot_v3_field_config.py
lazy_stop = 无                # ⚠️ 缺少此惩罚
```

**影响：**
- 机器人可能选择"站着不动"来避免惩罚
- 不利于学习前进行为

---

## 4. 完整配置对照表

### 4.1 环境配置

| 配置项 | go2_field | mybot_v3_field | 差异 |
|---|---|---|---|
| num_envs | 4096 | **8192** | mybot_v3 高 2 倍 |
| episode_length_s | 20 | 继承（20） | 相同 |
| use_lin_vel | False | 继承 | 相同 |

### 4.2 地形配置

| 配置项 | go2_field | mybot_v3_field | 差异 |
|---|---|---|---|
| num_rows | 10 | **32** | mybot_v3 高 3.2 倍 |
| num_cols | 40 | **32** | go2 更宽 |
| selected | BarrierTrack | BarrierTrack | 相同 |
| curriculum | **True** | **False** | ⚠️ go2 启用课程学习 |
| track_width | 3.2 | **1.6** | go2 宽 2 倍 |
| track_block_length | 2.4 | **2.0** | go2 稍长 |
| n_obstacles_per_track | 1 | **5** | ⚠️ mybot_v3 障碍物多 5 倍 |
| virtual_terrain | False | False | 相同 |

### 4.3 障碍物配置

| 障碍类型 | go2_field | mybot_v3_field | 差异 |
|---|---|---|---|
| **options** | 10 种 | **4 种** | go2 更多样化 |
| jump height | [0.05, 0.5] | (0.15, 0.3) | go2 范围更大 |
| leap length | [0.05, 0.8] | (0.1, 0.3) | go2 范围更大 |
| stairsup height | [0.1, 0.3] | (0.06, 0.1) | go2 更高 |

### 4.4 控制配置

| 配置项 | go2_field | mybot_v3_field | 差异 |
|---|---|---|---|
| stiffness | {'joint': 40.} | {'joint': 40.0} | 相同 |
| damping | {'joint': 1.} | {'joint': 1.0} | 相同 |
| action_scale | 0.5 | **0.25** | mybot_v3 小 2 倍 |
| computer_clip_torque | False | **True** | 不同 |
| motor_clip_torque | True | **False** | ⚠️ 相反 |

### 4.5 终止条件

| 配置项 | go2_field | mybot_v3_field | 差异 |
|---|---|---|---|
| roll threshold | 1.4 rad | **0.8 rad** | mybot_v3 更严格 |
| pitch threshold | 1.6 rad | 1.6 rad | 相同 |
| z_low threshold | 无 | **0.10 m** | mybot_v3 额外限制 |
| z_high threshold | 无 | **1.5 m** | mybot_v3 额外限制 |
| timeout_at_border | True | **False** | 不同 |

### 4.6 域随机化

| 配置项 | go2_field | mybot_v3_field | 差异 |
|---|---|---|---|
| randomize_com | True | True | 相同 |
| com_range x | [-0.2, 0.2] | [-0.05, 0.15] | go2 范围更大 |
| leg_motor_strength_range | [0.8, 1.2] | [0.9, 1.1] | go2 范围更大 |
| added_mass_range | [1.0, 3.0] | [1.0, 3.0] | 相同 |
| friction_range | [0., 2.] | [0., 2.] | 相同 |
| push_robots | True | **False** | ⚠️ mybot_v3 禁用推力 |

---

## 5. 问题总结与建议

### 5.1 奖励函数问题

**问题1：alive = 2.0 过高**
- **影响**：机器人可能选择"活着但不前进"
- **建议**：降低到 0.5 或移除

**问题2：tracking_lin_vel = 2.0 过高**
- **影响**：机器人可能绕过障碍物追求速度
- **建议**：降低到 1.0（与 go2 一致）

**问题3：缺少 lazy_stop 惩罚**
- **影响**：机器人可能站着不动
- **建议**：添加 `lazy_stop = -3.0`

**问题4：dof_error = -0.1 过高**
- **影响**：过度惩罚关节偏离，限制探索
- **建议**：降低到 -0.005（与 go2 一致）

### 5.2 地形配置问题

**问题1：curriculum = False**
- **影响**：训练初期难度过高
- **建议**：启用课程学习 `curriculum = True`

**问题2：n_obstacles_per_track = 5**
- **影响**：障碍物密度过高，训练困难
- **建议**：降低到 1-2（与 go2 一致）

**问题3：track_width = 1.6**
- **影响**：轨道过窄，机器人容易撞墙
- **建议**：增加到 2.4-3.2（与 go2 一致）

### 5.3 终止条件问题

**问题1：roll threshold = 0.8**
- **影响**：终止条件过严，episode 过短
- **建议**：放宽到 1.4（与 go2 一致）

**问题2：z_low threshold = 0.10**
- **影响**：机器人高度限制过严
- **建议**：移除或放宽到 0.05

### 5.4 域随机化问题

**问题1：push_robots = False**
- **影响**：训练环境过于理想，泛化能力差
- **建议**：启用 `push_robots = True`

**问题2：leg_motor_strength_range = [0.9, 1.1]**
- **影响**：随机化范围过小
- **建议**：扩大到 [0.8, 1.2]（与 go2 一致）

---

## 6. 推荐修改方案

### 6.1 奖励函数修改

```python
# mybot_v3_field_config.py
class rewards( MybotV3RoughCfg.rewards ):
    class scales( MybotV3RoughCfg.rewards.scales ):
        tracking_lin_vel = 1.0        # 从 2.0 降到 1.0
        tracking_ang_vel = 1.0        # 从 0.05 提高到 1.0
        energy_substeps = -2e-7       # 从 -2e-5 降到 -2e-7
        alive = 0.5                   # 从 2.0 降到 0.5
        dof_error = -0.005            # 从 -0.1 降到 -0.005
        lazy_stop = -3.0              # 新增
        collision = -0.05             # 保持
        penetrate_depth = -0.05       # 保持
        exceed_dof_pos_limits = -0.1  # 保持
        exceed_torque_limits_l1norm = -0.1  # 改用 l1norm
```

### 6.2 地形配置修改

```python
# mybot_v3_field_config.py
class terrain( MybotV3RoughCfg.terrain ):
    curriculum = True                 # 从 False 改为 True
    num_rows = 16                     # 从 32 降到 16
    num_cols = 20                     # 从 32 降到 20
    
    BarrierTrack_kwargs = dict(
        n_obstacles_per_track= 2,     # 从 5 降到 2
        track_width= 2.4,             # 从 1.6 提高到 2.4
        track_block_length= 2.4,      # 从 2.0 提高到 2.4
        # ... 其他保持不变
    )
```

### 6.3 终止条件修改

```python
# mybot_v3_field_config.py
class termination:
    roll_kwargs = dict(threshold= 1.4)   # 从 0.8 放宽到 1.4
    pitch_kwargs = dict(threshold= 1.6)  # 保持
    # 移除 z_low 和 z_high 限制
    timeout_at_border = True              # 从 False 改为 True
```

### 6.4 域随机化修改

```python
# mybot_v3_field_config.py
class domain_rand( MybotV3RoughCfg.domain_rand ):
    leg_motor_strength_range = [0.8, 1.2]  # 从 [0.9, 1.1] 扩大
    push_robots = True                      # 从 False 改为 True
    max_push_vel_xy = 0.5                   # 新增
    push_interval_s = 2                     # 新增
```

---

## 7. 训练监控建议

### 7.1 关键指标

| 指标 | 目标值 | 当前值 | 状态 |
|---|---|---|---|
| Mean reward | >20 | 15.31 | ⚠️ 偏低 |
| Episode length | >800 | 441 | ⚠️ 偏短 |
| tracking_lin_vel | >0.5 | 0.37 | ⚠️ 偏低 |
| n_obstacle_passed | >0 | 0 | ⚠️ 未通过障碍 |
| collision | <0.1 | 0.07 | ✅ 正常 |
| penetrate_depth | 0 | 0 | ✅ 正常 |

### 7.2 训练阶段建议

**阶段1（0-500 迭代）：基础行走**
- 目标：episode length >800，tracking_lin_vel >0.5
- 监控：collision 是否下降，alive 是否稳定

**阶段2（500-1500 迭代）：障碍穿越**
- 目标：n_obstacle_passed >0，max_pos_x >5m
- 监控：是否开始通过障碍物

**阶段3（1500-3000 迭代）：技能提升**
- 目标：n_obstacle_passed >5，tracking_lin_vel >0.8
- 监控：通过障碍物的数量和速度

---

## 8. 参考资源

- Go2 Rough 配置: `legged_gym/legged_gym/envs/go2/go2_config.py`
- Go2 Field 配置: `legged_gym/legged_gym/envs/go2/go2_field_config.py`
- MybotV3 Rough 配置: `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_config.py`
- MybotV3 Field 配置: `legged_gym/legged_gym/envs/mybot_v3/mybot_v3_field_config.py`
- 奖励函数实现: `legged_gym/legged_gym/envs/base/legged_robot.py`
- Field 特有函数: `legged_gym/legged_gym/envs/base/legged_robot_field.py`