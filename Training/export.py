import argparse
import hashlib
import json
from pathlib import Path
import torch
from stable_baselines3 import PPO
from Training.contracts import OBS_SIZE, ACTION_SIZE, OBSERVATION_SCHEMA, ACTION_SCHEMA


class DeterministicPolicy(torch.nn.Module):
    def __init__(self, policy):
        super().__init__()
        self.policy = policy

    def forward(self, observation):
        raw = self.policy._predict(observation, deterministic=True)
        movement = torch.clamp(raw[:, :4], -1, 1)
        buttons = torch.clamp((raw[:, 4:] + 1) * 0.5, 0, 1)
        return torch.cat((movement, buttons), dim=1)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", required=True)
    args = parser.parse_args()
    model = PPO.load(args.checkpoint, device="cpu")
    model.policy.eval()
    output = Path("Training/export")
    output.mkdir(parents=True, exist_ok=True)
    policy_path = output / "synthetic_policy.onnx"
    wrapper = DeterministicPolicy(model.policy)
    torch.onnx.export(wrapper, torch.zeros(1, OBS_SIZE), str(policy_path),
                      opset_version=17, input_names=["observation"],
                      output_names=["action"], do_constant_folding=True)
    metadata = {
        "model": "Synthetic-PPO", "version": "0.1.0-synthetic",
        "observation_schema": OBSERVATION_SCHEMA, "action_schema": ACTION_SCHEMA,
        "input_name": "observation", "output_name": "action",
        "input_shape": [1, OBS_SIZE], "output_shape": [1, ACTION_SIZE],
        "trained_steps": model.num_timesteps,
        "training_environment": "SyntheticArena (not Minecraft)",
        "sha256": hashlib.sha256(policy_path.read_bytes()).hexdigest()
    }
    (output / "metadata.json").write_text(json.dumps(metadata, indent=2) + "\n")
    print("Exported synthetic policy; never deploy as a PvP model.")


if __name__ == "__main__":
    main()
