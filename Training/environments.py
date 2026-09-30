"""Synthetic control task for checking PPO wiring, not gameplay competence."""
import gymnasium as gym
from gymnasium import spaces
import numpy as np


class SyntheticArena(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self):
        super().__init__()
        self.observation_space = spaces.Box(-1, 1, shape=(12,), dtype=np.float32)
        self.action_space = spaces.Box(-1, 1, shape=(6,), dtype=np.float32)
        self.target = np.zeros(2, dtype=np.float32)
        self.aim = np.zeros(2, dtype=np.float32)
        self.ticks = 0

    def _observation(self):
        difference = np.clip(self.target - self.aim, -1, 1)
        obs = np.zeros(12, dtype=np.float32)
        obs[0] = 1
        obs[2] = 1
        obs[3:5] = difference
        obs[5] = 1 - float(np.linalg.norm(difference)) / 2
        obs[10] = min(1, self.ticks / 450)
        return obs

    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.target = self.np_random.uniform(-0.8, 0.8, size=2).astype(np.float32)
        self.aim = np.zeros(2, dtype=np.float32)
        self.ticks = 0
        return self._observation(), {}

    def step(self, action):
        action = np.clip(np.asarray(action, dtype=np.float32), -1, 1)
        self.aim = np.clip(self.aim + action[2:4] * 0.06, -1, 1)
        distance = float(np.linalg.norm(self.target - self.aim))
        hit = distance < 0.12 and action[4] > 0
        reward = 1.0 if hit else -0.001 - 0.01 * distance
        self.ticks += 1
        return self._observation(), reward, hit, self.ticks >= 450, {"hit": hit}
