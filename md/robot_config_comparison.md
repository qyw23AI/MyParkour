# 四足机器人强化学习训练参数全面对比

## 1. 机器人基本信息

| 机器人 | 重量 | Body尺寸 (URDF碰撞盒) | 关节数 | 默认站高 | URDF路径 |
|---|---|---|---|---|---|
| **A1** | 12kg | 0.267×0.194×0.114m | 12 | 0.42m | `resources/robots/a1/urdf/a1.urdf` |
| **Go1** | 14kg | ~0.35×0.10×0.11m | 12 | 0.43m | `resources/robots/go1/urdf/go1.urdf` |
| **Go2** | 15kg | 0.3762×0.0935×0.114m | 12 | 0.5m | `resources/robots/go2/urdf/go2.urdf` |
| **MybotV3** | ~4kg* | **0.30×0.25×0.20m** | 12 | 0.40m | `resources/robots/mybot_v3/urdf/mybot_v3.urdf` |

*注：MybotV3 的 body 质量 3.87kg（从 URDF 提取），总重量约 4-5kg

**关键发现：**
- MybotV3 的 body 宽度（0.25m）比 Go2（0.0935m）大 **2.7 倍**
- MybotV3 的 body 高度（0.20m）比 Go2（0.114m）大 **1.8 倍**
- MybotV3 的 body 长度（0.30m）比 Go2（0.3762m）小 **20%**

---

## 2. 训练配置对比

### 2.1 基础训练参数（Field 配置）

| 参数 | A1 Field | Go1 Field | Go2 Field | MybotV3 Field | 说明 |
|---|---|---|---|---|---|
| **num_envs** | 4096 | **8192** | 4096 | **4096** | Go1 使用 2 倍环境数 |
| **num_steps_per_env** | - | - | 24 | **24** | 每次迭代收集步数 |
| **max_iterations** | 5000 | 20000 | **38000** | **15000** | Go2 训练最充分 |
| **save_interval** | 500 | 500 | **10000** | **5000** | Go2 保存间隔最大 |
| **num_mini_batches** | - | - | 4 | **4** | PPO mini-batch 数量 |
| **learning_rate** | - | - | 1e-3 | **1e-3** | 学习率 |
| **entropy_coef** | 0.01 | 0.0 | **0.0** | **0.0** | 熵系数 |

**关键发现：**
- Go2 训练最充分（38000 迭代），A1 最少（5000 迭代）
- Go1 使用最多的环境数（8192），但迭代次数适中
- Go2 的 save_interval 最大（10000），减少磁盘 I/O

### 2.2 蒸馏训练参数（Distill 配置）

| 参数 | A1 Distill | Go1 Distill | Go2 Distill | MybotV3 Distill | 说明 |
|---|---|---|---|---|---|
| **num_envs** | **256** | **256** | **256** | **4096** | 蒸馏使用少量环境 |
| **max_iterations** | 80000 | - | **60000** | - | 蒸馏训练更长 |
| **num_steps_per_env** | 48 | - | **32** | - | 蒸馏使用更多步数 |
| **learning_rate** | 3e-4 | 1e-4 | **3e-4** | - | 蒸馏学习率更高 |
| **distill_target** | tanh | l1 | **l1** | - | 蒸馏目标函数 |

**关键发现：**
- 蒸馏训练使用少量环境（256），但迭代次数更多（60000-80000）
- 蒸馏学习率更高（3e-4 vs 1e-3）
- Go2 使用 l1 蒸馏目标，A1 使用 tanh

---

## 3. 地形配置对比

### 3.1 地形规模

| 参数 | A1 Field | Go1 Field | Go2 Field | MybotV3 Field | 说明 |
|---|---|---|---|---|---|
| **num_rows** | 20 | 20 | **10** | **16** | 地形行数 |
| **num_cols** | 50 | 80 | **40** | **20** | 地形列数 |
| **总地形数** | 1000 | **1600** | **400** | **320** | Go1 地形最多 |
| **curriculum** | False | False | **True** | **True** | Go2/MybotV3 启用课程学习 |

### 3.2 BarrierTrack 配置

| 参数 | A1 Field | Go1 Field | Go2 Field | MybotV3 Field |
|---|---|---|---|---|
| **track_width** | 1.6m | 1.6m | **3.2m** | **2.4m** |
| **track_block_length** | 2.0m | 2.0m | **2.4m** | **2.4m** |
| **n_obstacles_per_track** | - | - | **1** | **2** |
| **options** | 空 | 空 | **10 种** | **4 种** |

**障碍类型对比：**

| 障碍类型 | A1 | Go1 | Go2 | MybotV3 |
|---|---|---|---|---|
| jump | ✅ | ✅ | ✅ | ✅ |
| leap | ✅ | ✅ | ✅ | ✅ |
| crawl | ✅ | ✅ | ❌ | ❌ |
| tilt | ✅ | ✅ | ❌ | ✅ |
| hurdle | ❌ | ❌ | ✅ | ❌ |
| down | ❌ | ❌ | ✅ | ❌ |
| stairsup | ❌ | ❌ | ✅ | ✅ |
| stairsdown | ❌ | ❌ | ✅ | ❌ |
| slope | ❌ | ❌ | ✅ | ❌ |
| wave | ❌ | ❌ | ✅ | ❌ |

**关键发现：**
- Go2 的障碍类型最多（10 种），训练最全面
- MybotV3 只有 4 种障碍类型，训练相对简单
- Go2 的 track_width 最大（3.2m），给机器人更多空间

### 3.3 障碍物参数对比

**Jump（跳跃）：**

| 参数 | A1 | Go1 | Go2 | MybotV3 |
|---|---|---|---|---|
| height | (0.2, 0.6) | - | (0.05, 0.5) | **(0.15, 0.3)** |
| depth | (0.1, 0.8) | - | (0.1, 0.3) | **(0.05, 0.1)** |

**Leap（跨栏）：**

| 参数 | A1 | Go1 | Go2 | MybotV3 |
|---|---|---|---|---|
| length | (0.2, 1.0) | - | (0.05, 0.8) | **(0.1, 0.3)** |
| depth | (0.4, 0.8) | - | (0.5, 0.8) | **(0.2, 0.4)** |
| height | 0.2 | - | 0.2 | **0.1** |

**关键发现：**
- Go2 的障碍物参数范围最大，训练难度最高
- MybotV3 的障碍物参数最保守，适合初期训练

---

## 4. 奖励函数配置对比

### 4.1 Field 配置奖励权重

| 奖励项 | A1 Field | Go1 Field | Go2 Field | MybotV3 Field |
|---|---|---|---|---|
| **tracking_lin_vel** | - | 3.0 | **1.0** | **1.0** |
| **tracking_ang_vel** | 0.05 | 0.05 | **1.0** | **1.0** |
| **tracking_world_vel** | - | 3.0 | - | - |
| **world_vel_l2norm** | -1.0 | - | - | **-1.0** |
| **alive** | 2.0 | - | - | **0.5** |
| **energy_substeps** | -2e-5 | -2e-5 | **-2e-7** | **-2e-7** |
| **legs_energy** | -0.0 | - | - | - |
| **collision** | - | -10.0 | **-0.05** | **-0.05** |
| **penetrate_depth** | - | - | **-0.05** | **-0.05** |
| **lazy_stop** | - | - | **-3.0** | **-3.0** |
| **dof_error** | - | -0.04 | **-0.005** | **-0.005** |
| **dof_error_named** | - | - | **-1.0** | - |
| **exceed_dof_pos_limits** | -0.1 | -0.8 | **-0.1** | **-0.1** |
| **exceed_torque_limits_l1norm** | - | -0.8 | **-0.1** | **-0.1** |
| **exceed_torque_limits_i** | -0.2 | - | - | - |
| **lin_vel_z** | -1.0 | -1.0 | - | - |
| **ang_vel_xy** | -0.05 | -0.05 | - | - |
| **orientation** | - | -4.0 | - | - |
| **dof_acc** | - | -2.5e-7 | - | - |
| **action_rate** | - | -0.1 | - | - |
| **torques** | - | -1e-5 | **-1e-7** | - |
| **yaw_abs** | - | -0.8 | - | - |
| **lin_pos_y** | - | -0.8 | - | - |
| **hip_pos** | - | -0.4 | - | - |

**关键发现：**
- Go2 的奖励配置最简洁，只关注关键指标
- Go1 的奖励配置最复杂，包含多个惩罚项
- MybotV3 的奖励配置已对齐 Go2

### 4.2 Rough 配置奖励权重

| 奖励项 | A1 Rough | Go2 Rough | MybotV3 Rough |
|---|---|---|---|
| **tracking_lin_vel** | - | 1.0 | **2.0** |
| **tracking_ang_vel** | - | 1.0 | **0.5** |
| **energy_substeps** | - | -2e-5 | **-2e-5** |
| **stand_still** | - | -2.0 | **0.0** |
| **dof_error_named** | - | -1.0 | - |
| **dof_error** | - | -0.01 | **-0.1** |
| **exceed_dof_pos_limits** | - | -0.4 | **0.0** |
| **exceed_torque_limits_l1norm** | - | -0.4 | **0.0** |
| **dof_vel_limits** | - | -0.4 | **0.0** |
| **torques** | -0.0002 | - | **0.0** |
| **dof_pos_limits** | -10.0 | - | **0.0** |

**关键发现：**
- Go2 Rough 配置包含硬件安全惩罚（exceed_dof_pos_limits, exceed_torque_limits_l1norm）
- MybotV3 Rough 配置缺少这些安全惩罚

---

## 5. 终止条件配置对比

### 5.1 Field 配置终止条件

| 终止条件 | A1 Field | Go1 Field | Go2 Field | MybotV3 Field |
|---|---|---|---|---|
| **roll threshold** | 0.8 | 1.5 | **1.4** | **1.4** |
| **pitch threshold** | 1.6 | 1.5 | **1.6** | **1.6** |
| **z_low** | ✅ (0.15m) | ❌ | ❌ | ❌ |
| **z_high** | ✅ (1.5m) | ❌ | ❌ | ❌ |
| **out_of_track** | ❌ | ❌ | ❌ | ❌ |
| **timeout_at_border** | False | - | **True** | **True** |

**关键发现：**
- A1 使用 z_low 和 z_high 终止条件，Go2 和 MybotV3 不使用
- Go2 和 MybotV3 的 roll threshold 更宽松（1.4 vs 0.8）
- Go2 和 MybotV3 启用 timeout_at_border

### 5.2 障碍物特定终止条件

**A1 Field Distill（障碍物条件终止）：**

```python
roll_kwargs = dict(
    threshold= 0.8,
    crawl_threshold= 0.4,
    climb_threshold= 0.8,
    leap_threshold= 0.6,
    tilt_threshold= 1.0,
)
pitch_kwargs = dict(
    threshold= 1.5,
    crawl_threshold= 0.7,
    climb_threshold= 1.5,
    leap_threshold= 0.7,
    tilt_threshold= 0.5,
)
```

**关键发现：**
- 不同障碍类型使用不同的终止阈值
- crawl（爬行）的阈值最严格（roll=0.4, pitch=0.7）
- tilt（倾斜）的 roll 阈值最宽松（1.0）

---

## 6. 控制参数对比

### 6.1 PD 控制参数

| 参数 | A1 | Go1 | Go2 | MybotV3 |
|---|---|---|---|---|
| **stiffness (Kp)** | 50.0 | **40.0** | **40.0** | **40.0** |
| **damping (Kd)** | 1.0 | **0.5** | **1.0** | **1.0** |
| **action_scale** | 0.5 | **0.5** | **0.5** | **0.25** |
| **decimation** | 4 | 4 | 4 | 4 |
| **torque_limits** | 25 | [20,20,25]×4 | - | **25** |
| **computer_clip_torque** | True | **False** | **False** | **True** |
| **motor_clip_torque** | False | False | **True** | **False** |

**关键发现：**
- A1 的 stiffness 最高（50.0），控制更刚性
- MybotV3 的 action_scale 最小（0.25），动作幅度更小
- Go2 使用 motor_clip_torque=True，硬件安全更好

### 6.2 默认关节角度

| 关节 | A1 | Go1 | Go2 | MybotV3 |
|---|---|---|---|---|
| **FL_hip** | 0.1 | -0.1 | **0.1** | **0.1** |
| **FR_hip** | -0.1 | 0.1 | **-0.1** | **-0.1** |
| **RL_hip** | 0.1 | -0.1 | **0.1** | **0.1** |
| **RR_hip** | -0.1 | 0.1 | **-0.1** | **-0.1** |
| **FL_thigh** | 0.8 | 0.8 | **0.7** | **0.8** |
| **FR_thigh** | 0.8 | 0.8 | **0.7** | **0.8** |
| **RL_thigh** | 1.0 | 1.0 | **1.0** | **1.0** |
| **RR_thigh** | 1.0 | 1.0 | **1.0** | **1.0** |
| **FL_calf** | -1.5 | -1.5 | **-1.5** | **-1.5** |
| **FR_calf** | -1.5 | -1.5 | **-1.5** | **-1.5** |
| **RL_calf** | -1.5 | -1.5 | **-1.5** | **-1.5** |
| **RR_calf** | -1.5 | -1.5 | **-1.5** | **-1.5** |

**关键发现：**
- 所有机器人的 calf 角度一致（-1.5）
- Go2 的 thigh 角度稍小（0.7 vs 0.8）
- MybotV3 的默认角度与 A1 完全一致

---

## 7. 域随机化配置对比

### 7.1 基础随机化

| 参数 | A1 Field | Go1 Field | Go2 Field | MybotV3 Field |
|---|---|---|---|---|
| **randomize_com** | True | True | True | **True** |
| **com_range x** | [-0.05, 0.15] | [-0.2, 0.2] | [-0.2, 0.2] | **[-0.05, 0.15]** |
| **com_range y** | [-0.1, 0.1] | - | [-0.1, 0.1] | **[-0.1, 0.1]** |
| **com_range z** | [-0.05, 0.05] | - | [-0.05, 0.05] | **[-0.05, 0.05]** |
| **randomize_motor** | True | True | True | **True** |
| **leg_motor_strength** | [0.9, 1.1] | - | [0.8, 1.2] | **[0.8, 1.2]** |
| **randomize_base_mass** | True | True | True | **True** |
| **added_mass_range** | [1.0, 3.0] | - | [1.0, 3.0] | **[1.0, 3.0]** |
| **randomize_friction** | True | True | True | **True** |
| **friction_range** | [0., 2.] | - | [0., 2.] | **[0., 2.]** |
| **push_robots** | False | - | **True** | **True** |
| **max_push_vel_xy** | - | - | 0.5 | **0.5** |
| **push_interval_s** | - | - | 2 | **2** |

**关键发现：**
- Go2 的域随机化范围最大（com_range, leg_motor_strength）
- Go2 和 MybotV3 启用 push_robots，提高泛化能力
- MybotV3 的域随机化配置已对齐 Go2

### 7.2 初始状态随机化

| 参数 | A1 Field | Go1 Field | Go2 Field | MybotV3 Field |
|---|---|---|---|---|
| **init_base_pos x** | [0.2, 0.6] | [0.05, 0.6] | [0.05, 0.6] | **[0.2, 0.6]** |
| **init_base_pos y** | [-0.25, 0.25] | - | [-0.25, 0.25] | **[-0.25, 0.25]** |
| **init_base_rot roll** | - | [-0.75, 0.75] | [-0.75, 0.75] | - |
| **init_base_rot pitch** | - | [-0.75, 0.75] | [-0.75, 0.75] | - |
| **init_base_vel x** | - | [-0.2, 1.5] | [-0.2, 1.5] | - |
| **init_dof_vel** | - | [-5, 5] | [-5, 5] | - |

**关键发现：**
- Go1 和 Go2 的初始状态随机化更全面（包括旋转和速度）
- MybotV3 缺少 init_base_rot 和 init_base_vel 随机化

---

## 8. 观测空间配置对比

### 8.1 Field 配置观测组件

| 观测组件 | A1 Field | Go1 Field | Go2 Field | MybotV3 Field |
|---|---|---|---|---|
| **proprioception** | ✅ | ✅ | ✅ | ✅ |
| **base_pose** | ✅ | ✅ | ❌ | ✅ |
| **robot_config** | ✅ | ✅ | ❌ | ✅ |
| **engaging_block** | ✅ | ✅ | ❌ | ✅ |
| **sidewall_distance** | ✅ | ✅ | ❌ | ✅ |
| **height_measurements** | ❌ | ❌ | ✅ | ✅ |
| **lin_vel** | ❌ | ❌ | ✅ | ❌ |
| **ang_vel** | ❌ | ❌ | ✅ | ❌ |
| **projected_gravity** | ❌ | ❌ | ✅ | ❌ |
| **commands** | ❌ | ❌ | ✅ | ❌ |
| **dof_pos** | ❌ | ❌ | ✅ | ❌ |
| **dof_vel** | ❌ | ❌ | ✅ | ❌ |
| **last_actions** | ❌ | ❌ | ✅ | ❌ |

**关键发现：**
- Go2 使用独立的观测组件（lin_vel, ang_vel 等），而不是 proprioception
- MybotV3 的观测组件与 A1 一致

### 8.2 Distill 配置观测组件

| 观测组件 | A1 Distill | Go1 Distill | Go2 Distill |
|---|---|---|---|
| **proprioception** | ✅ | ✅ | ❌ |
| **forward_depth** | ✅ | ✅ | ✅ |
| **lin_vel** | ❌ | ❌ | ✅ |
| **ang_vel** | ❌ | ❌ | ✅ |
| **projected_gravity** | ❌ | ❌ | ✅ |
| **commands** | ❌ | ❌ | ✅ |
| **dof_pos** | ❌ | ❌ | ✅ |
| **dof_vel** | ❌ | ❌ | ✅ |
| **last_actions** | ❌ | ❌ | ✅ |

**关键发现：**
- 蒸馏配置都包含 forward_depth（视觉输入）
- Go2 Distill 使用完整的观测组件，而不是 proprioception

---

## 9. 碰撞与终止配置对比

### 9.1 碰撞惩罚配置

| 参数 | A1 | Go1 | Go2 | MybotV3 |
|---|---|---|---|---|
| **penalize_contacts_on** | ["base", "thigh", "calf"] | - | ["thigh", "calf"] | **["thigh", "calf"]** |
| **terminate_after_contacts_on** | ["base", "imu"] | ["base"] | ["base"] | **["body"]** |
| **privileged_contacts_on** | - | - | - | ["base", "body", "thigh", "calf"] |

**关键发现：**
- A1 的惩罚最严格（包括 base）
- Go2 和 MybotV3 只惩罚 thigh 和 calf
- MybotV3 的 terminate_after_contacts_on 使用 "body"（匹配 URDF）

### 9.2 URDF Link Name 对比

| 机器人 | Body Link Name | Base Link Name |
|---|---|---|
| A1 | "base" | - |
| Go1 | "base" | - |
| Go2 | "base" | - |
| MybotV3 | "body" | - |

**关键发现：**
- MybotV3 的 URDF 使用 "body"，而其他机器人使用 "base"
- 配置时需要匹配 URDF 中的 link name

---

## 10. PPO 算法参数对比

### 10.1 基础 PPO 参数

| 参数 | A1 | Go1 | Go2 | MybotV3 |
|---|---|---|---|---|
| **entropy_coef** | 0.01 | 0.0 | **0.0** | **0.0** |
| **clip_min_std** | 1e-12 | 0.2 | **1e-12** | **1e-12** |
| **learning_rate** | - | - | 1e-3 | **1e-3** |
| **num_mini_batches** | - | - | 4 | **4** |
| **optimizer** | - | - | AdamW | AdamW |

### 10.2 策略网络配置

| 参数 | A1 | Go1 | Go2 | MybotV3 |
|---|---|---|---|---|
| **rnn_type** | gru | - | **gru** | **gru** |
| **mu_activation** | tanh | None | **None** | **tanh** |
| **init_noise_std** | - | - | 0.5 | **1.0** |
| **actor_hidden_dims** | - | - | [512, 256, 128] | **[512, 256, 128]** |
| **critic_hidden_dims** | - | - | [512, 256, 128] | **[512, 256, 128]** |

**关键发现：**
- Go2 的 mu_activation=None，允许负动作
- MybotV3 使用 tanh 激活，限制动作范围
- MybotV3 的 init_noise_std 更高（1.0 vs 0.5），探索更多

---

## 11. 最佳实践总结

### 11.1 训练配置建议

**基础训练（Field）：**
```python
num_envs = 4096              # Go2 标准
num_steps_per_env = 24       # Go2 标准
max_iterations = 15000-38000 # 根据任务复杂度
save_interval = 5000-10000   # 减少磁盘 I/O
num_mini_batches = 4         # Go2 标准
learning_rate = 1e-3         # Go2 标准
entropy_coef = 0.0           # Go2 标准
```

**蒸馏训练（Distill）：**
```python
num_envs = 256               # 少量环境
max_iterations = 60000-80000 # 长时间训练
num_steps_per_env = 32-48    # 更多步数
learning_rate = 3e-4         # 更高学习率
distill_target = "l1"        # Go2 标准
```

### 11.2 地形配置建议

**障碍穿越任务：**
```python
num_rows = 10-16             # 适中
num_cols = 20-40             # 适中
curriculum = True            # 启用课程学习
track_width = 2.4-3.2        # 给机器人足够空间
n_obstacles_per_track = 1-2  # 不要太多
options = 4-10 种            # 根据需求
```

**障碍物参数：**
```python
# 初期训练
jump_height = (0.15, 0.3)    # 保守
leap_length = (0.1, 0.3)     # 保守

# 后期训练
jump_height = (0.05, 0.5)    # Go2 标准
leap_length = (0.05, 0.8)    # Go2 标准
```

### 11.3 奖励函数建议

**核心奖励：**
```python
tracking_lin_vel = 1.0       # 速度跟踪
tracking_ang_vel = 1.0       # 角速度跟踪
energy_substeps = -2e-7      # 能量惩罚
collision = -0.05            # 碰撞惩罚
penetrate_depth = -0.05      # 穿透惩罚
lazy_stop = -3.0             # 懒惰停止惩罚
```

**硬件安全：**
```python
exceed_dof_pos_limits = -0.1      # 关节超限
exceed_torque_limits_l1norm = -0.1 # 力矩超限
```

**避免使用：**
```python
alive = 0.0                  # 避免存活奖励
world_vel_l2norm = 0.0       # 避免世界坐标系速度惩罚
```

### 11.4 终止条件建议

**基础终止：**
```python
roll_threshold = 1.4         # 宽松
pitch_threshold = 1.6        # 宽松
timeout_at_border = True     # 边界超时
```

**避免使用：**
```python
z_low = False                # 障碍穿越不需要
z_high = False               # 障碍穿越不需要
```

### 11.5 控制参数建议

**PD 控制：**
```python
stiffness = 40.0             # Go2 标准
damping = 1.0                # Go2 标准
action_scale = 0.5           # Go2 标准
motor_clip_torque = True     # 硬件安全
```

### 11.6 域随机化建议

**基础随机化：**
```python
randomize_com = True
com_range = [-0.2, 0.2]      # Go2 标准
randomize_motor = True
leg_motor_strength = [0.8, 1.2]  # Go2 标准
randomize_friction = True
friction_range = [0., 2.]    # Go2 标准
push_robots = True           # 提高泛化
max_push_vel_xy = 0.5
push_interval_s = 2
```

---

## 12. MybotV3 配置优化建议

### 12.1 当前配置问题

| 问题 | 当前值 | 建议值 | 原因 |
|---|---|---|---|
| **max_iterations** | 15000 | **20000-30000** | 训练不充分 |
| **mu_activation** | tanh | **None** | 限制探索 |
| **init_noise_std** | 1.0 | **0.5** | 探索过多 |
| **缺少 init_base_rot** | - | **添加** | 提高鲁棒性 |
| **缺少 init_base_vel** | - | **添加** | 提高鲁棒性 |

### 12.2 推荐配置

```python
# MybotV3 Field 配置优化
class MybotV3FieldCfg:
    class env:
        num_envs = 4096
    
    class terrain:
        num_rows = 16
        num_cols = 20
        curriculum = True
        track_width = 2.4
        n_obstacles_per_track = 2
    
    class rewards:
        tracking_lin_vel = 1.0
        tracking_ang_vel = 1.0
        energy_substeps = -2e-7
        collision = -0.05
        penetrate_depth = -0.05
        lazy_stop = -3.0
        dof_error = -0.005
        exceed_dof_pos_limits = -0.1
        exceed_torque_limits_l1norm = -0.1
    
    class termination:
        roll_threshold = 1.4
        pitch_threshold = 1.6
        timeout_at_border = True
    
    class control:
        stiffness = 40.0
        damping = 1.0
        action_scale = 0.5
        motor_clip_torque = True
    
    class domain_rand:
        randomize_com = True
        com_range = [-0.2, 0.2]
        leg_motor_strength = [0.8, 1.2]
        push_robots = True
        max_push_vel_xy = 0.5
        init_base_rot_range = dict(
            roll = [-0.75, 0.75],
            pitch = [-0.75, 0.75],
        )
        init_base_vel_range = dict(
            x = [-0.2, 1.5],
            y = [-0.2, 0.2],
            z = [-0.2, 0.2],
        )

class MybotV3FieldCfgPPO:
    class algorithm:
        entropy_coef = 0.0
        learning_rate = 1e-3
        num_mini_batches = 4
    
    class policy:
        rnn_type = 'gru'
        mu_activation = None  # 改为 None
        init_noise_std = 0.5  # 降低
    
    class runner:
        num_steps_per_env = 24
        max_iterations = 20000  # 增加
        save_interval = 5000
```

---

## 13. 参考资源

- A1 配置: `legged_gym/legged_gym/envs/a1/`
- Go1 配置: `legged_gym/legged_gym/envs/go1/`
- Go2 配置: `legged_gym/legged_gym/envs/go2/`
- MybotV3 配置: `legged_gym/legged_gym/envs/mybot_v3/`
- 基础配置: `legged_gym/legged_gym/envs/base/`
- 奖励函数实现: `legged_gym/legged_gym/envs/base/legged_robot.py`
- Field 特有实现: `legged_gym/legged_gym/envs/base/legged_robot_field.py`