package com.harvey.pvpagent;

import android.graphics.Color;

/** Visible-colour tracker for controlled arenas. This is a heuristic, not PPO. */
public final class VisionPolicy {
    public static final class Decision {
        public final float dx, dy, confidence;
        Decision(float dx, float dy, float confidence) {
            this.dx = dx; this.dy = dy; this.confidence = confidence;
        }
    }

    public static Decision detect(byte[] rgba, int width, int height, int target) {
        if (rgba == null || rgba.length != width * height * 4) return new Decision(0, 0, 0);
        float[] targetHsv = new float[3], hsv = new float[3];
        Color.colorToHSV(target, targetHsv);
        long sx = 0, sy = 0;
        int hits = 0;
        // Ignore HUD margins. Sampling every other pixel limits load on phones.
        for (int y = height / 8; y < height * 7 / 8; y += 2) {
            for (int x = width / 8; x < width * 7 / 8; x += 2) {
                int pos = (y * width + x) * 4;
                int r = rgba[pos] & 255, g = rgba[pos + 1] & 255, b = rgba[pos + 2] & 255;
                Color.RGBToHSV(r, g, b, hsv);
                float hue = Math.abs(hsv[0] - targetHsv[0]);
                hue = Math.min(hue, 360 - hue);
                if (hue < 15 && hsv[1] > 0.42f && hsv[2] > 0.23f
                    && Math.abs(hsv[1] - targetHsv[1]) < 0.28f) {
                    sx += x; sy += y; hits++;
                }
            }
        }
        if (hits < 18) return new Decision(0, 0, 0);
        float cx = sx / (float) hits, cy = sy / (float) hits;
        float confidence = Math.min(1f, hits / 140f);
        return new Decision((cx - width / 2f) / (width / 2f),
            (cy - height / 2f) / (height / 2f), confidence);
    }

    private VisionPolicy() { }
}
