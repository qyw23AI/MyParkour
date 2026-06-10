import numpy as np
from legged_gym.envs.base.legged_robot_config import LeggedRobotCfg, LeggedRobotCfgPPO
from legged_gym.envs.mybot_v3.mybot_v3_config import MybotV3RoughCfg, MybotV3RoughCfgPPO


class MybotV3FieldCfg( MybotV3RoughCfg ):
    class env( MybotV3RoughCfg.env ):
        num_envs = 4096
        obs_components = [
            "proprioception", # 48
            "base_pose",
            "robot_config",
            "engaging_block",
            "sidewall_distance",
        ]

    class terrain( MybotV3RoughCfg.terrain ):
        mesh_type = None
        num_rows = 16
        num_cols = 20
        selected = "BarrierTrack"
        max_init_terrain_level = 0
        border_size = 5
        slope_treshold = 20.

        curriculum = True
        horizontal_scale = 0.025
        pad_unavailable_info = True

        measure_heights = True
        measured_points_x = [-1.0, -0.8, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0., 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]
        measured_points_y = [-0.5, -0.4, -0.3, -0.2, -0.1, 0., 0.1, 0.2, 0.3, 0.4, 0.5]

        BarrierTrack_kwargs = dict(
            options= [
                "hurdle",
                "stairsup",
                "bridge_a",
                "bridge_b",
                "t_stairs",
            ],
            n_obstacles_per_track= 4,
            randomize_obstacle_order= True,
            track_width= 2.4,
            track_block_length= 2.4,
            wall_thickness= (0.04, 0.2),
            wall_height= 0.3,
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
                ramp_length= 0.40,          # [m] approach ramp length
            ),
            bridge_b= dict(
                n_beams= 3,
                beam_width= 0.20,           # 20cm (along X)
                gap_width= 0.10,            # 10cm (along X)
                bridge_height= 0.20,        # 20cm
                bridge_mesh_source= "procedural",
                rotate_90= False,
                ramp_length= 0.40,          # [m] approach ramp length
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
            border_height= 0.,
            virtual_terrain= False,
            draw_virtual_terrain= True,
            engaging_next_threshold= 1.2,
            engaging_finish_threshold= 0.,
            curriculum_perlin= False,
            no_perlin_threshold= 0.1,
        )

        TerrainPerlin_kwargs = dict(
            zScale= [0.0, 0.03],
            frequency= 10,
        )

    class commands( MybotV3RoughCfg.commands ):
        heading_command = False
        resampling_time = 10
        lin_cmd_cutoff = 0.2
        class ranges( MybotV3RoughCfg.commands.ranges ):
            lin_vel_x = [-1.0, 1.0]
            lin_vel_y = [0.0, 0.0]
            ang_vel_yaw = [0., 0.]

    class control( MybotV3RoughCfg.control ):
        stiffness = {'joint': 40.0}
        damping = {'joint': 1.0}
        action_scale = 0.25
        torque_limits = 25
        computer_clip_torque = True
        motor_clip_torque = False

    class asset( MybotV3RoughCfg.asset ):
        penalize_contacts_on = ["thigh", "calf", "body"]
        terminate_after_contacts_on = ["body"]
        front_hip_names = ["FR_hip_joint", "FL_hip_joint"]
        rear_hip_names = ["RR_hip_joint", "RL_hip_joint"]

    class termination:
        termination_terms = [
            "roll",
            "pitch",
        ]

        roll_kwargs = dict(
            threshold= 1.4,
        )
        pitch_kwargs = dict(
            threshold= 1.6,
        )

        check_obstacle_conditioned_threshold = True
        timeout_at_border = True

    class domain_rand( MybotV3RoughCfg.domain_rand ):
        randomize_com = True
        class com_range:
            x = [-0.05, 0.15]
            y = [-0.1, 0.1]
            z = [-0.05, 0.05]

        randomize_motor = True
        leg_motor_strength_range = [0.8, 1.2]

        randomize_base_mass = True
        added_mass_range = [1.0, 3.0]

        randomize_friction = True
        friction_range = [0., 2.]

        init_base_pos_range = dict(
            x= [0.2, 0.6],
            y= [-0.25, 0.25],
        )

        push_robots = True
        max_push_vel_xy = 0.5
        push_interval_s = 2

    class rewards( MybotV3RoughCfg.rewards ):
        class scales( MybotV3RoughCfg.rewards.scales ):
            tracking_lin_vel = 1.0
            tracking_ang_vel = 1.0
            world_vel_l2norm = -1.
            energy_substeps = -2e-7
            alive = 0.5
            dof_error = -0.005
            lazy_stop = -3.0
            exceed_dof_pos_limits = -0.1
            exceed_torque_limits_l1norm = -0.1
            collision = -0.05
            penetrate_depth = -0.05

        soft_dof_pos_limit = 1.0
        base_height_target = 0.33

    class curriculum:
        penetrate_depth_threshold_harder = 100
        penetrate_depth_threshold_easier = 200
        no_moveup_when_fall = True


class MybotV3FieldCfgPPO( MybotV3RoughCfgPPO ):
    class algorithm( MybotV3RoughCfgPPO.algorithm ):
        entropy_coef = 0.0
        clip_min_std = 1e-12
        num_mini_batches = 4
        learning_rate = 1e-3

    class policy( MybotV3RoughCfgPPO.policy ):
        rnn_type = 'gru'
        mu_activation = "tanh"

    class runner( MybotV3RoughCfgPPO.runner ):
        policy_class_name = "ActorCriticRecurrent"
        experiment_name = "field_mybot_v3"
        num_steps_per_env = 24
        resume = False
        run_name = "JLC_obstacles"
        max_iterations = 20000
        save_interval = 1000
        log_interval = 100