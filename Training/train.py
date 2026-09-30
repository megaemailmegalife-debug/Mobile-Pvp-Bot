import argparse
from pathlib import Path
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from Training.environments import SyntheticArena


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--steps", type=int, default=100000)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    if args.steps <= 0:
        parser.error("steps must be positive")
    out = Path("Training/checkpoints")
    out.mkdir(parents=True, exist_ok=True)
    model = PPO("MlpPolicy", Monitor(SyntheticArena()), seed=args.seed,
                verbose=1, tensorboard_log=None, n_steps=1024, batch_size=256)
    model.learn(total_timesteps=args.steps)
    model.save(str(out / "synthetic_ppo"))
    print(f"Synthetic task only. Requested timesteps: {args.steps}.")


if __name__ == "__main__":
    main()
