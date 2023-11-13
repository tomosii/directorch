import gymnasium as gym
import numpy as np

from omegaconf import DictConfig
from tqdm import tqdm

from agents.dreamer import DreamerAgent
from utils.transition import Transition
from utils.replay import ReplayBuffer
from utils.image import save_image, save_gif_video


class Driver:
    """
    A driver that runs N steps in an environment.
    """

    def __init__(
        self,
        env: gym.Env,
        agent: DreamerAgent,
        buffer: ReplayBuffer,
    ):
        self.env = env
        self.agent = agent
        self.buffer = buffer

    def run(self, max_steps: int = 1000, train_every: int = 5):
        """
        Run environment steps and train until reaching max_steps.
        """
        total_step = 0

        # Fill the replay buffer
        print("Filling the replay buffer...\n")
        with tqdm(total=self.buffer.capacity) as progress_bar:
            obs, info = self.env.reset()
            while not self.buffer.is_full:
                progress_bar.update(1)
                # action = self.env.action_space.sample()
                action = 0
                next_obs, reward, terminated, truncated, info = self.env.step(action)
                total_step += 1
                transition = Transition(
                    observation=next_obs,
                    action=action,
                    reward=reward,
                    terminated=terminated,
                    truncated=truncated,
                )
                self.buffer.add(transition)
                obs = next_obs
                if terminated or truncated:
                    obs, info = self.env.reset()
        print(f"Replay buffer has {len(self.buffer)} transitions.\n")

        obs, info = self.env.reset()
        env_step = 0

        print("Start training...\n")

        while total_step < max_steps:
            # action = self.agent.select_aciton(obs)
            # action = self.env.action_space.sample()
            action = 0

            # Take a step in the environment
            next_obs, reward, terminated, truncated, info = self.env.step(action)

            env_step += 1
            total_step += 1

            transition = Transition(
                observation=next_obs,
                action=action,
                reward=reward,
                terminated=terminated,
                truncated=truncated,
            )

            # Add transition to the buffer
            self.buffer.add(transition)

            obs = next_obs

            if terminated or truncated:
                # print(f"Episode finished after {env_step} steps.")
                obs, info = self.env.reset()
                env_step = 0

            if total_step % train_every == 0:
                # print(f"Training at step {total_step}.")

                # Get a batch from the buffer
                transitions = self.buffer.sample()

                # Train agent with the batch data
                metrics = self.agent.train(transitions)

            # Print metrics
            if total_step % 1000 == 0:
                print(f"Step {total_step}: {metrics}")

        print("Training finished.")
