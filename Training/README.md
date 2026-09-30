# PPO training research harness

The included `SyntheticArena` tests observation/action compatibility, reward plumbing and export. It is a toy control task. Training it does **not** yield a Minecraft PvP agent.

From a remote Python environment with appropriate packages:

```sh
python -m venv .venv
. .venv/bin/activate
pip install -r Training/requirements.txt
python -m Training.train --steps 100000 --seed 42
python -m Training.export --checkpoint Training/checkpoints/synthetic_ppo.zip
```

The exporter places an ONNX policy and matching metadata under `Training/export/`, including its SHA-256 hash. A representative permitted training environment would need to implement the same 12 feature observations and six actions, record actual reward event confidence, and be evaluated on held-out maps, textures and opponents. The current example is unsuitable as deployable weights.

The Android agent refuses to arm even if a model is exported because native inference, detector evaluation and lifecycle testing remain unfinished.
