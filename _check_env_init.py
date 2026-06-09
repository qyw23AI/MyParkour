import sys, os
sys.argv = ['', '--task=mybot_v3_field', '--headless']
from legged_gym.utils import task_registry
env, env_cfg = task_registry.make_env(name='mybot_v3_field', args=None)
print('=== Env init OK ===')
print(f'num_envs: {env_cfg.env.num_envs}')
print(f'reward_scales: {env_cfg.rewards.scales}')