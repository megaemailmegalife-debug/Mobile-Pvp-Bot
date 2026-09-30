package com.harvey.pvpagent;

import android.accessibilityservice.AccessibilityService;
import android.accessibilityservice.GestureDescription;
import android.graphics.Path;
import android.os.Handler;
import android.os.Looper;
import android.os.SystemClock;
import android.view.accessibility.AccessibilityEvent;

public final class GestureService extends AccessibilityService {
    private static volatile GestureService instance;
    private static volatile boolean armed;
    private static long lastGesture;
    private final Handler handler = new Handler(Looper.getMainLooper());

    public static boolean isConnected() { return instance != null; }
    // No UI path arms this service in this source release. A validated native policy is required.
    public static void disable() { armed = false; }

    @Override protected void onServiceConnected() { instance = this; armed = false; }
    @Override public void onAccessibilityEvent(AccessibilityEvent event) { }
    @Override public void onInterrupt() { disable(); }
    @Override public void onDestroy() { disable(); instance = null; super.onDestroy(); }

    private static float clamp(float v) { return Math.max(0f, Math.min(1f, v)); }
    private static boolean valid(float v) { return !Float.isNaN(v) && !Float.isInfinite(v); }

    static boolean sendSwipe(float sx, float sy, float ex, float ey, int durationMs) {
        GestureService service = instance;
        if (!armed || service == null || !CaptureService.isRunning()) return false;
        if (!valid(sx) || !valid(sy) || !valid(ex) || !valid(ey)) return false;
        long now = SystemClock.uptimeMillis();
        if (now - lastGesture < 65) return false;
        lastGesture = now;
        final int duration = Math.max(40, Math.min(300, durationMs));
        service.handler.post(() -> {
            if (!armed || !CaptureService.isRunning()) return;
            android.util.DisplayMetrics dm = service.getResources().getDisplayMetrics();
            Path path = new Path();
            path.moveTo(clamp(sx) * dm.widthPixels, clamp(sy) * dm.heightPixels);
            path.lineTo(clamp(ex) * dm.widthPixels, clamp(ey) * dm.heightPixels);
            GestureDescription gesture = new GestureDescription.Builder()
                .addStroke(new GestureDescription.StrokeDescription(path, 0, duration)).build();
            service.dispatchGesture(gesture, null, service.handler);
        });
        return true;
    }
}
