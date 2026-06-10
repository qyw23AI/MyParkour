from collections import OrderedDict
import os
import os.path as osp
from datetime import datetime
import numpy as np
from legged_gym.envs.mybot_v3.mybot_v3_field_config import MybotV3FieldCfg, MybotV3FieldCfgPPO
from legged_gym.utils.helpers import merge_dict


class MybotV3FieldDistillCfg( MybotV3FieldCfg ):
    class env( MybotV3FieldCfg.env ):
        num_envs = 4096
        obs_components = [
            "proprioception",
            "height_measurements",
        ]
        privileged_obs_components = [
            "proprioception",
            "base_pose",
            "robot_config",
            "engaging_block",
            "sidewall_distance",
        ]
        use_lin_vel = False
        privileged_use_lin_vel = True
        privileged_obs_gets_privilege = False

    class init_state( MybotV3FieldCfg.init_state ):
        pos = [0.0, 0.0, 0.40]

    class terrain( MybotV3FieldCfg.terrain ):
        num_rows = 8
        num_cols = 4
        max_init_terrain_level = 1
        curriculum = False

        BarrierTrack_kwargs = merge_dict(MybotV3FieldCfg.terrain.BarrierTrack_kwargs, dict(
            options= [
                "hurdle",
                "stairsup",
                "bridge_a",
                "bridge_b",
                "t_stairs",
            ],
            n_obstacles_per_track= 5,
            randomize_obstacle_order= True,
            track_width= 3.0,
            track_block_length= 1.8,
            wall_thickness= (0.2, 1.),
            wall_height= (-0.5, 0.5),
            hurdle= dict(
                height= (0.15, 0.35),
                depth= (0.05, 0.08),
            ),
            stairsup= dict(
                height= (0.08, 0.15),
                depth= (0.10, 0.30),
                n_stairs= 2,
            ),
            bridge_a= dict(
                n_beams= 5,
                beam_width= 0.40,           # 40cm (along X)
                gap_width= 0.15,            # 15cm (along X)
                bridge_height= 0.15,        # 15cm
                bridge_mesh_source= "procedural",
                rotate_90= True,
                ramp_length= 0.40,           # [m] approach ramp length
            ),
            bridge_b= dict(
                n_beams= 3,
                beam_width= 0.20,           # 20cm (along X)
                gap_width= 0.10,            # 10cm (along X)
                bridge_height= 0.20,        # 20cm
                bridge_mesh_source= "procedural",
                rotate_90= False,
                ramp_length= 0.40,           # [m] approach ramp length
            ),
            t_stairs= dict(
                step_height= 0.10,
                step_depth= 0.18,
                n_steps= 4,
                stair_width= 2.00,          # I-stairs: full track width
                platform_width= 0.80,
                rotate_90= False,
            ),
            add_perlin_noise= True,
            border_perlin_noise= True,
            border_height= -0.5,
            virtual_terrain= False,
            draw_virtual_terrain= True,
            engaging_next_threshold= 1.2,
            check_skill_combinations= True,
            curriculum_perlin= False,
            no_perlin_threshold= 0.04,
            walk_in_skill_gap= True,
        ))

        TerrainPerlin_kwargs = dict(
            zScale= [0.0, 0.02],
            frequency= 10,
        )

    class commands( MybotV3FieldCfg.commands ):
        class ranges( MybotV3FieldCfg.commands.ranges ):
            lin_vel_x = [0.0, 0.0]
            lin_vel_y = [0.0, 0.0]
            ang_vel_yaw = [0., 0.]

    class control( MybotV3FieldCfg.control ):
        stiffness = {'joint': 40.0}
        damping = {'joint': 1.0}
        action_scale = 0.25
        torque_limits = 25.
        computer_clip_torque = True
        motor_clip_torque = False

    class termination:
        termination_terms = [
            "roll",
            "pitch",
            "out_of_track",
        ]
        roll_kwargs = dict(
            threshold= 0.8,
            crawl_threshold= 0.4,
            stairsup_threshold= 0.8,
            hurdle_threshold= 0.8,
            bridge_a_threshold= 0.8,
            bridge_b_threshold= 0.8,
            t_stairs_threshold= 0.8,
            walk_threshold= 0.8,
        )
        pitch_kwargs = dict(
            threshold= 1.6,
            hurdle_threshold= 1.6,
            walk_threshold= 1.6,
            stairsup_threshold= 1.6,
            bridge_a_threshold= 1.6,
            bridge_b_threshold= 1.6,
            t_stairs_threshold= 1.6,
        )

        check_obstacle_conditioned_threshold = True
        timeout_at_border = True

    class domain_rand( MybotV3FieldCfg.domain_rand ):
        push_robots = False

    class rewards( MybotV3FieldCfg.rewards ):
        class scales( MybotV3FieldCfg.rewards.scales ):
            tracking_ang_vel = 0.0
            tracking_lin_vel = 1.0
            world_vel_l2norm = -1.0
            energy_substeps = -2e-5
            alive = 2.0
            exceed_dof_pos_limits = -1e-1
            exceed_torque_limits_i = -1e-1
            collision = -1.0

        soft_dof_pos_limit = 1.0
        base_height_target = 0.33
        max_contact_force = 100.0

    class normalization:
        class obs_scales:
            lin_vel = 2.0
            ang_vel = 0.25
            base_pose = 1.0
            robot_config = 1.0
            engaging_block = 1.0
            sidewall_distance = 1.0
            commands = [2., 2., 0.25]
            dof_pos = 1.0
            dof_vel = 0.05
            last_actions = 1.0
            proprioception = 1.0
            height_measurements = 1.0
        clip_observations = 100.
        clip_actions = 100.

    class noise:
        add_noise = True
        noise_level = 1.0
        class noise_scales:
            dof_pos = 0.01
            dof_vel = 1.5
            ang_vel = 0.2
            gravity = 0.05


class MybotV3FieldDistillCfgPPO( MybotV3FieldCfgPPO ):
    runner_class_name = "TwoStageRunner"
    class runner( MybotV3FieldCfgPPO.runner ):
        policy_class_name = "ActorCriticRecurrent"
        algorithm_class_name = "TPPO"
        experiment_name = "distill_mybot_v3"
        num_steps_per_env = 48

        pretrain_iterations = -1
        class pretrain_dataset:
            scan_dir = ""
            max_episode_length = 2000
            shuffle_env = False
            dataset_loops = -1
            random_shuffle_traj_order = True
            keep_latest_ratio = 1.0
            keep_latest_n_trajs = 2000
            starting_frame_range = [0, 100]

        resume = False
        load_run = None
        max_iterations = 80000
        save_interval = 2000

    class policy( MybotV3FieldCfgPPO.policy ):
        init_noise_std = 0.5
        actor_hidden_dims = [512, 256, 128]
        critic_hidden_dims = [512, 256, 128]
        activation = 'elu'

    class algorithm( MybotV3FieldCfgPPO.algorithm ):
        entropy_coef = 0.005
        learning_rate = 1.e-4
        value_loss_coef = 0.0
        num_learning_epochs = 1
        num_mini_batches = 4
        teacher_act_prob = "exp"
        distillation_loss_coef = 1.0
        distill_target = "tanh"
        buffer_dilation_ratio = 1.
        optimizer_class_name = "AdamW"

        teacher_policy_class_name = "ActorCriticRecurrent"
        teacher_ac_path = None
        class teacher_policy( MybotV3FieldCfgPPO.policy ):
            num_actor_obs = 276
            num_critic_obs = 276
            num_actions = 12
            obs_segments = OrderedDict(
                proprioception= (48,),
                base_pose= (6,),
                robot_config= (1 + 3 + 1 + 12,),
                engaging_block= (1 + 200 + 2,),
                sidewall_distance= (2,),
            )
            env_action_scale = MybotV3FieldCfg.control.action_scale