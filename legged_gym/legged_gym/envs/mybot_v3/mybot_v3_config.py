# SPDX-FileCopyrightText: Copyright (c) 2021 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: BSD-3-Clause
#
# Copyright (c) 2021 ETH Zurich, Nikita Rudin

import numpy as np
from legged_gym.envs.base.legged_robot_config import LeggedRobotCfg, LeggedRobotCfgPPO


class MybotV3RoughCfg(LeggedRobotCfg):
    class env(LeggedRobotCfg.env):
        num_envs = 4096
        obs_components = [
            "proprioception",       # lin_vel + ang_vel + gravity + commands + dof_pos + dof_vel + last_actions
            "height_measurements",  # terrain heights around the robot
        ]

    class init_state(LeggedRobotCfg.init_state):
        pos = [0.0, 0.0, 0.43]          #
        default_joint_angles = {
            "FL_hip_joint": 0.1,
            "RL_hip_joint": 0.1,
            "FR_hip_joint": -0.1,
            "RR_hip_joint": -0.1,

            "FL_thigh_joint": 0.8,
            "RL_thigh_joint": 1.0,
            "FR_thigh_joint": 0.8,
            "RR_thigh_joint": 1.0,

            "FL_calf_joint": -1.5,
            "RL_calf_joint": -1.5,
            "FR_calf_joint": -1.5,
            "RR_calf_joint": -1.5,
        }

    class control(LeggedRobotCfg.control):
        control_type = "P"
        stiffness = {
           
            "FL_hip": 40.0,
            "FR_hip": 40.0,
            "RL_hip": 40.0,
            "RR_hip": 40.0,
    
            "FL_thigh": 40.0,
            "FR_thigh": 40.0,
            "RL_thigh": 40.0,
            "RR_thigh": 40.0,

            "FL_calf": 40.0,
            "FR_calf": 40.0,
            "RL_calf": 40.0,
            "RR_calf": 40.0,
        }
        damping = {
            "FL_hip": 1.0, "FR_hip": 1.0, "RL_hip": 1.0, "RR_hip": 1.0,
            "FL_thigh": 1.0, "FR_thigh": 1.0, "RL_thigh": 1.0, "RR_thigh": 1.0,
            "FL_calf": 1.0, "FR_calf": 1.0, "RL_calf": 1.0, "RR_calf": 1.0,
        }
        action_scale = 0.25  # 调整动作幅度，使小腿运动更平稳
        decimation = 4
        hip_reduction = 1.0

    class terrain(LeggedRobotCfg.terrain):
        selected = "TerrainPerlin"  # Perlin 噪声粗糙地形，用于基础行走训练
        mesh_type = None            # 使用 selected 时必须为 None
        measure_heights = True
        horizontal_scale = 0.025
        vertical_scale = 0.005
        border_size = 5
        curriculum = False
        static_friction = 1.0
        dynamic_friction = 1.0
        restitution = 0.0
        max_init_terrain_level = 5
        terrain_length = 4.0
        terrain_width = 4.0
        num_rows = 20
        num_cols = 20
        slope_treshold = 1.0

        TerrainPerlin_kwargs = dict(
            zScale= [0.0, 0.07],    # [0, 0.07]: 低端为平地，高端为粗糙地形，混合训练
            frequency= 10,
        )

    class commands(LeggedRobotCfg.commands):
        curriculum = True
        max_curriculum = 2.0
        num_commands = 4
        resampling_time = 10.0
        heading_command = True

        class ranges(LeggedRobotCfg.commands.ranges):
            lin_vel_x = [-0.2,0.2]
            lin_vel_y = [-0.2, 0.2]
            ang_vel_yaw = [-3.14, 3.14]
            heading = [-3.14, 3.14]


    class asset(LeggedRobotCfg.asset):
        file = "{LEGGED_GYM_ROOT_DIR}/resources/robots/mybot_v3/urdf/mybot_v3.urdf"
        name = "mybot_v3"
        foot_name = "foot"
        penalize_contacts_on = ["thigh", "calf"]
        terminate_after_contacts_on = ["body"]
        privileged_contacts_on = ["base", "body", "thigh", "calf"]
        self_collisions = 1
        flip_visual_attachments = False
        armature = 0.01

    class rewards(LeggedRobotCfg.rewards):
        class scales:
            termination = -0.1     # 终止惩罚（倒下/出界）
            tracking_lin_vel = 2.0
            tracking_ang_vel = 0.5
            lin_vel_z = -2.0
            ang_vel_xy = -0.05
            orientation = -0.2
            dof_acc = -2.5e-7
            energy_substeps = -2e-5
            base_height = -1.0
            action_rate = -0.01
            feet_air_time = 0.01     # 鼓励迈步步态（trot）
            collision = -0.0
            stand_still = -0.0
            torques = -0.0
            dof_vel = -0.0
            dof_pos_limits = -0.0
            dof_vel_limits = -0.0
            torque_limits = -0.0
            dof_error = -0.1         # 适当减小，避免抑制正常行走时的关节运动

        only_positive_rewards = False
        tracking_sigma = 0.25
        soft_dof_pos_limit = 1.0
        soft_dof_vel_limit = 1.0
        soft_torque_limit = 1.0
        base_height_target = 0.33
        max_contact_force = 100.0
        clearance_height_target = -0.21

    class sim( LeggedRobotCfg.sim ):
        body_measure_points = {  # transform are related to body frame, key must be substring of URDF link name
            "body": dict(
                x= [i for i in np.arange(-0.15, 0.151, 0.03)],
                y= [i for i in np.arange(-0.125, 0.126, 0.03)],
                z= [i for i in np.arange(-0.10, 0.101, 0.03)],
                transform= [0., 0., 0., 0., 0., 0.],
            ),
            "thigh": dict(
                x= [
                    -0.16, -0.155, -0.15, -0.145, -0.14, -0.135, -0.13,
                    -0.125, -0.12, -0.115, -0.11, -0.105, -0.1, -0.095,
                    -0.09, -0.085, -0.08, -0.075, -0.07, -0.065, -0.05,
                    0.0, 0.05, 0.1,
                ],
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


class MybotV3RoughCfgPPO(LeggedRobotCfgPPO):
    class policy(LeggedRobotCfgPPO.policy):
        init_noise_std = 1.0
        actor_hidden_dims = [512, 256, 128]
        critic_hidden_dims = [512, 256, 128]
        activation = 'elu'
        rnn_type = 'gru'            # ActorCriticRecurrent 需要

    class algorithm(LeggedRobotCfgPPO.algorithm):
        entropy_coef = 0.01

    class runner(LeggedRobotCfgPPO.runner):
        policy_class_name = "ActorCriticRecurrent"  # 与 field 训练保持一致，避免 hidden_states=None bug
        run_name = ""
        experiment_name = "rough_mybot_v3"
        num_steps_per_env = 100