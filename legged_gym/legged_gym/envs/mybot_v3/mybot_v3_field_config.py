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
        num_rows = 20
        num_cols = 50
        selected = "BarrierTrack"
        max_init_terrain_level = 0
        border_size = 5
        slope_treshold = 20.

        curriculum = False
        horizontal_scale = 0.025
        pad_unavailable_info = True

        measure_heights = True
        measured_points_x = [-1.0, -0.8, -0.6, -0.5, -0.4, -0.3, -0.2, -0.1, 0., 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.8, 1.0]
        measured_points_y = [-0.5, -0.4, -0.3, -0.2, -0.1, 0., 0.1, 0.2, 0.3, 0.4, 0.5]

        BarrierTrack_kwargs = dict(
            options= [
                "jump",
                "leap",
                "stairsup",
                "tilt",
            ],
            n_obstacles_per_track= 5,
            randomize_obstacle_order= True,
            track_width= 1.6,
            track_block_length= 2.,
            wall_thickness= (0.04, 0.2),
            wall_height= -0.05,
            jump= dict(
                height= (0.25, 0.35),
                depth= (0.05, 0.15),
                fake_offset= 0.0,
            ),
            leap= dict(
                length= (0.2, 0.5),
                depth= (0.4, 0.6),
                height= 0.2,
            ),
            stairsup= dict(
                height= (0.08, 0.15),
                depth= (0.1, 0.3),
                n_stairs= 3,
            ),
            tilt= dict(
                width= (0.15, 0.35),
                depth= (0.8, 1.5),
                opening_angle= 0.0,
                wall_height= 0.5,
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
            zScale= [0.08, 0.15],
            frequency= 10,
        )

    class commands( MybotV3RoughCfg.commands ):
        heading_command = False
        resampling_time = 10
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
            "z_low",
            "z_high",
        ]

        roll_kwargs = dict(
            threshold= 0.8,
        )
        pitch_kwargs = dict(
            threshold= 1.6,
        )
        z_low_kwargs = dict(
            threshold= 0.10,
        )
        z_high_kwargs = dict(
            threshold= 1.5,
        )
        out_of_track_kwargs = dict(
            threshold= 1.,
        )

        check_obstacle_conditioned_threshold = True
        timeout_at_border = False

    class domain_rand( MybotV3RoughCfg.domain_rand ):
        randomize_com = True
        class com_range:
            x = [-0.05, 0.15]
            y = [-0.1, 0.1]
            z = [-0.05, 0.05]

        randomize_motor = True
        leg_motor_strength_range = [0.9, 1.1]

        randomize_base_mass = True
        added_mass_range = [1.0, 3.0]

        randomize_friction = True
        friction_range = [0., 2.]

        init_base_pos_range = dict(
            x= [0.2, 0.6],
            y= [-0.25, 0.25],
        )

        push_robots = False

    class rewards( MybotV3RoughCfg.rewards ):
        class scales( MybotV3RoughCfg.rewards.scales ):
            tracking_ang_vel = 0.05
            world_vel_l2norm = -1.
            legs_energy_substeps = -2e-5
            alive = 2.
            exceed_dof_pos_limits = -1e-1
            exceed_torque_limits_i = -1e-1
            collision = -10.0

        soft_dof_pos_limit = 1.0
        base_height_target = 0.33


class MybotV3FieldCfgPPO( MybotV3RoughCfgPPO ):
    class algorithm( MybotV3RoughCfgPPO.algorithm ):
        entropy_coef = 0.01
        clip_min_std = 1e-12

    class policy( MybotV3RoughCfgPPO.policy ):
        rnn_type = 'gru'
        mu_activation = "tanh"

    class runner( MybotV3RoughCfgPPO.runner ):
        policy_class_name = "ActorCriticRecurrent"
        experiment_name = "field_mybot_v3"
        resume = False
        run_name = "JLC_obstacles"
        max_iterations = 5000
        save_interval = 500