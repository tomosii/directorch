import gymnasium as gym
import numpy as np
import cv2

from gymnasium.wrappers import PixelObservationWrapper


class PixelEnv(gym.ObservationWrapper):
    """Use image as observation."""

    def __init__(self, env):
        env = PixelObservationWrapper(env)
        super().__init__(env)

    def observation(self, obs):
        # Normalize image from [0, 255] to [0, 1]
        image = obs["pixels"] / 255.0
        return image


class ChannelFirstEnv(gym.ObservationWrapper):
    """Convert [H, W, C] to [C, H, W]."""

    def __init__(self, env):
        super().__init__(env)

    def observation(self, obs):
        return np.transpose(obs, (2, 0, 1))


class ResizeImageEnv(gym.ObservationWrapper):
    """Resize image observation."""

    def __init__(self, env, size):
        super().__init__(env)
        self.size = size

    def observation(self, obs):
        image = cv2.resize(obs, self.size)
        return image