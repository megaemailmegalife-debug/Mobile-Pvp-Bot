import unittest
from Training.contracts import (action_from_policy, validate_metadata,
                                RewardEngine, OBS_SIZE)


class ContractTests(unittest.TestCase):
    def test_action_clamp_and_invalid_number(self):
        self.assertEqual(action_from_policy([2, -2, float("nan"), .5, 7, -1]),
                         (1, -1, 0, .5, 1, 0))

    def test_metadata_rejects_missing_hash_and_schema(self):
        meta = dict(observation_schema=1, action_schema=1,
                    input_shape=[1, OBS_SIZE], output_shape=[1, 6],
                    training_environment="SyntheticArena", sha256="a" * 64)
        validate_metadata(meta)
        with self.assertRaises(ValueError):
            validate_metadata({**meta, "observation_schema": 2})
        with self.assertRaises(ValueError):
            validate_metadata({**meta, "sha256": None})

    def test_death_and_kill_are_debounced(self):
        engine = RewardEngine()
        self.assertEqual(engine.tick(death_confidence=.9, kill_confidence=.95, moved=True), -2)
        self.assertEqual(engine.tick(death_confidence=.9, kill_confidence=.95, moved=True), 0)
        engine.tick(moved=True)
        self.assertEqual(engine.tick(death_confidence=.9, kill_confidence=.95, moved=True), -2)

    def test_stalling_requires_enemy_and_threshold(self):
        engine = RewardEngine()
        for _ in range(150):
            self.assertEqual(engine.tick(enemy_confidence=.9), 0)
        self.assertEqual(engine.tick(enemy_confidence=.9), -.05)
        self.assertEqual(engine.tick(enemy_confidence=.9, moved=True), 0)

    def test_damage_and_hit(self):
        engine = RewardEngine()
        self.assertAlmostEqual(engine.tick(damage=.9, hit_confidence=.95), -.1)
        self.assertEqual(engine.tick(damage=.9, hit_confidence=.95), 0)


if __name__ == "__main__":
    unittest.main()
