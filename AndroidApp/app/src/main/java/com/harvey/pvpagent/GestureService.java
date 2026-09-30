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
    private static volatile float attackX = .88f, attackY = .73f;
    private static volatile float cameraX = .72f, cameraY = .46f;
    private static volatile float joystickX = .16f, joystickY = .78f;
    private final Handler handler = new Handler(Looper.getMainLooper());

    public static boolean isConnected() { return instance != null; }
    static void enable() { armed = instance != null && CaptureService.isRunning(); }
    public static void disable() { armed = false; }
    static void configure(float ax, float ay, float cx, float cy, float jx, float jy) {
        attackX = clamp(ax); attackY = clamp(ay);
        cameraX = clamp(cx); cameraY = clamp(cy);
        joystickX = clamp(jx); joystickY = clamp(jy);
    }

    @Override protected void onServiceConnected() { instance = this; armed = false; }
    @Override public void onAccessibilityEvent(AccessibilityEvent event) { }
    @Override public void onInterrupt() { CaptureService.disarm(); }
    @Override public void onDestroy() { CaptureService.disarm(); instance = null; super.onDestroy(); }

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
            android.util.DisplayMetrics dm = new android.util.DisplayMetrics();
            ((android.view.WindowManager) service.getSystemService(WINDOW_SERVICE))
                .getDefaultDisplay().getRealMetrics(dm);
            Path path = new Path();
            path.moveTo(clamp(sx) * dm.widthPixels, clamp(sy) * dm.heightPixels);
            path.lineTo(clamp(ex) * dm.widthPixels, clamp(ey) * dm.heightPixels);
            GestureDescription gesture = new GestureDescription.Builder()
                .addStroke(new GestureDescription.StrokeDescription(path, 0, duration)).build();
            service.dispatchGesture(gesture, null, service.handler);
        });
        return true;
    }

    static boolean sendAction(float dx, float dy, boolean attack) {
        GestureService service = instance;
        if (!armed || service == null || !CaptureService.isArmed() || !CaptureService.isRunning()) return false;
        if (!valid(dx) || !valid(dy)) return false;
        long now = SystemClock.uptimeMillis();
        if (now - lastGesture < 225) return false;
        lastGesture = now;
        service.handler.post(() -> {
            if (!armed || !CaptureService.isArmed() || !CaptureService.isRunning()) return;
            android.util.DisplayMetrics dm = new android.util.DisplayMetrics();
            ((android.view.WindowManager) service.getSystemService(WINDOW_SERVICE))
                .getDefaultDisplay().getRealMetrics(dm);
            GestureDescription.Builder builder = new GestureDescription.Builder();
            Path camera = new Path();
            camera.moveTo(dm.widthPixels * cameraX, dm.heightPixels * cameraY);
            camera.lineTo(dm.widthPixels * clamp(cameraX + Math.max(-.12f, Math.min(.12f, dx * .14f))),
                dm.heightPixels * clamp(cameraY + Math.max(-.10f, Math.min(.10f, dy * .12f))));
            builder.addStroke(new GestureDescription.StrokeDescription(camera, 0, 170));
            if (Math.abs(dx) < .6f && Math.abs(dy) < .6f) {
                Path movement = new Path();
                movement.moveTo(dm.widthPixels * joystickX, dm.heightPixels * joystickY);
                movement.lineTo(dm.widthPixels * joystickX,
                    dm.heightPixels * clamp(joystickY - .07f));
                builder.addStroke(new GestureDescription.StrokeDescription(movement, 0, 170));
            }
            if (attack) {
                Path tap = new Path();
                tap.moveTo(dm.widthPixels * attackX, dm.heightPixels * attackY);
                builder.addStroke(new GestureDescription.StrokeDescription(tap, 0, 55));
            }
            service.dispatchGesture(builder.build(), null, service.handler);
        });
        return true;
    }
}
