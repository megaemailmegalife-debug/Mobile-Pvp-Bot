"""Portable schema and reward contract used by training and offline tests."""
from dataclasses import dataclass
import math

OBS_SIZE = 12
ACTION_SIZE = 6
OBSERVATION_SCHEMA = 1
ACTION_SCHEMA = 1


def clamp(value, low, high):
    if not math.isfinite(value):
        return 0.0
    return max(low, min(high, value))


def action_from_policy(values):
    if len(values) != ACTION_SIZE:
        raise ValueError("action must have six scalars")
    return tuple(clamp(float(v), -1.0 if i < 4 else 0.0, 1.0)
                 for i, v in enumerate(values))


def validate_metadata(meta):
    if meta.get("observation_schema") != OBSERVATION_SCHEMA:
        raise ValueError("observation schema mismatch")
    if meta.get("action_schema") != ACTION_SCHEMA:
        raise ValueError("action schema mismatch")
    if meta.get("input_shape") != [1, OBS_SIZE] or meta.get("output_shape") != [1, ACTION_SIZE]:
        raise ValueError("tensor shape mismatch")
    digest = meta.get("sha256")
    if not isinstance(digest, str) or len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
        raise ValueError("model hash missing or invalid")
    if meta.get("training_environment") in (None, "", "none"):
        raise ValueError("training provenance missing")


@dataclass
class RewardWeights:
    death: float = -10.0
    kill: float = 8.0
    damage: float = -0.5
    hit: float = 0.4
    stall: float = -0.05


class RewardEngine:
    def __init__(self, weights=None):
        self.weights = weights or RewardWeights()
        self.was_dead = False
        self.last_kill_confidence = 0.0
        self.last_hit_confidence = 0.0
        self.last_damage = 0.0
        self.idle_ticks = 0

    def tick(self, death_confidence=0.0, kill_confidence=0.0,
             damage=0.0, hit_confidence=0.0, moved=False, enemy_confidence=0.0):
        score = 0.0
        dead = death_confidence >= 0.85
        if dead and not self.was_dead:
            score += self.weights.death
        self.was_dead = dead
        if kill_confidence >= 0.9 and self.last_kill_confidence < 0.9:
            score += self.weights.kill
        self.last_kill_confidence = kill_confidence
        if damage >= 0.8 and self.last_damage < 0.8:
            score += self.weights.damage
        if hit_confidence >= 0.9 and self.last_hit_confidence < 0.9:
            score += self.weights.hit
        self.last_damage = damage
        self.last_hit_confidence = hit_confidence
        self.idle_ticks = 0 if moved else min(1000, self.idle_ticks + 1)
        if self.idle_ticks > 150 and enemy_confidence > 0.6:
            score += self.weights.stall
        return score
