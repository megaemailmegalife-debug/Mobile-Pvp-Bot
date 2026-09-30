package com.harvey.pvpagent;

import android.content.Intent;
import android.provider.Settings;
import android.app.Activity;

public final class AgentBridge {
    private AgentBridge() { }

    private static Activity activity() {
        try {
            return (Activity) Class.forName("com.unity3d.player.UnityPlayer")
                .getField("currentActivity").get(null);
        } catch (ReflectiveOperationException ex) {
            throw new IllegalStateException("Unity activity unavailable", ex);
        }
    }

    public static void requestCapture() {
        Activity host = activity();
        Intent intent = new Intent(host, ConsentActivity.class);
        host.startActivity(intent);
    }

    public static void openAccessibilitySettings() {
        activity().startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS));
    }

    public static void stop() {
        GestureService.disable();
        Activity host = activity();
        Intent intent = new Intent(host, CaptureService.class);
        intent.setAction(CaptureService.ACTION_STOP);
        host.startService(intent);
    }

    public static String status() {
        return "Capture: " + (CaptureService.isRunning() ? "active" : "stopped")
            + " | Accessibility: " + (GestureService.isConnected() ? "enabled" : "disabled")
            + " | Agent: locked (no validated model)";
    }
}
