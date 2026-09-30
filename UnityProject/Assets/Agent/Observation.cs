using System;
using UnityEngine;

namespace Agent
{
    [Serializable]
    public struct Observation
    {
        public const int Size = 12;
        public float health, healthDelta, enemyConfidence, enemyX, enemyY,
            alignment, recentDamage, hitConfidence, killConfidence,
            deathConfidence, secondsSinceCombat, motion;

        public float[] ToArray()
        {
            return new[] {
                Clamp01(health), Mathf.Clamp(healthDelta, -1f, 1f), Clamp01(enemyConfidence),
                Mathf.Clamp(enemyX, -1f, 1f), Mathf.Clamp(enemyY, -1f, 1f), Clamp01(alignment),
                Clamp01(recentDamage), Clamp01(hitConfidence), Clamp01(killConfidence),
                Clamp01(deathConfidence), Clamp01(secondsSinceCombat / 30f), Clamp01(motion)
            };
        }

        private static float Clamp01(float x) => float.IsNaN(x) ? 0f : Mathf.Clamp01(x);
    }

    public struct AgentAction
    {
        public float moveX, moveY, lookX, lookY, attack, jump;
        public static AgentAction FromArray(float[] values)
        {
            if (values == null || values.Length != 6) throw new ArgumentException("Action requires six values");
            float Safe(float value, float lo, float hi) => float.IsNaN(value) || float.IsInfinity(value) ? 0f : Mathf.Clamp(value, lo, hi);
            return new AgentAction {
                moveX = Safe(values[0], -1f, 1f), moveY = Safe(values[1], -1f, 1f),
                lookX = Safe(values[2], -1f, 1f), lookY = Safe(values[3], -1f, 1f),
                attack = Safe(values[4], 0f, 1f), jump = Safe(values[5], 0f, 1f)
            };
        }
    }
}
