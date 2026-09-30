using System;

namespace Agent
{
    [Serializable]
    public sealed class RewardWeights
    {
        public float death = -10f, kill = 8f, damage = -0.5f, hit = 0.4f, stall = -0.05f;
    }

    public sealed class RewardEngine
    {
        readonly RewardWeights weights;
        bool wasDead;
        float lastKillConfidence;
        float lastHitConfidence;
        float lastDamage;
        int idleTicks;

        public RewardEngine(RewardWeights weights) { this.weights = weights ?? throw new ArgumentNullException(nameof(weights)); }
        public float Tick(Observation o, bool moved)
        {
            float result = 0f;
            bool dead = o.deathConfidence >= 0.85f;
            if (dead && !wasDead) result += weights.death;
            wasDead = dead;
            if (o.killConfidence >= 0.9f && lastKillConfidence < 0.9f) result += weights.kill;
            lastKillConfidence = o.killConfidence;
            if (o.recentDamage >= 0.8f && lastDamage < 0.8f) result += weights.damage;
            if (o.hitConfidence >= 0.9f && lastHitConfidence < 0.9f) result += weights.hit;
            lastDamage = o.recentDamage;
            lastHitConfidence = o.hitConfidence;
            idleTicks = moved ? 0 : Math.Min(1000, idleTicks + 1);
            if (idleTicks > 150 && o.enemyConfidence > 0.6f) result += weights.stall;
            return result;
        }
    }
}
