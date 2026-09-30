package com.harvey.pvpagent;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Bitmap;
import android.graphics.Color;
import android.graphics.ImageDecoder;
import android.net.Uri;
import android.os.Bundle;
import android.os.Build;
import android.provider.Settings;
import android.widget.Button;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;
import java.io.IOException;

public final class MainActivity extends Activity {
    private static final int PICK_IMAGE = 41;
    private static final int TARGET = 0, ATTACK = 1, CAMERA = 2, JOYSTICK = 3;
    private int sampleMode = TARGET;
    private ImageView sample;
    private Bitmap bitmap;
    private TextView status;

    private void button(LinearLayout layout, String text, Runnable action) {
        Button button = new Button(this);
        button.setText(text);
        button.setOnClickListener(v -> action.run());
        layout.addView(button);
    }

    @Override public void onCreate(Bundle saved) {
        super.onCreate(saved);
        if (Build.VERSION.SDK_INT >= 33 &&
            checkSelfPermission("android.permission.POST_NOTIFICATIONS") != android.content.pm.PackageManager.PERMISSION_GRANTED)
            requestPermissions(new String[]{"android.permission.POST_NOTIFICATIONS"}, 7);
        ScrollView scroll = new ScrollView(this);
        LinearLayout content = new LinearLayout(this);
        content.setPadding(28, 24, 28, 24);
        content.setOrientation(LinearLayout.VERTICAL);
        scroll.addView(content);
        TextView title = new TextView(this);
        title.setTextSize(24);
        title.setText("PvP Vision Agent · private arena research");
        content.addView(title);
        status = new TextView(this);
        content.addView(status);
        TextView info = new TextView(this);
        info.setText("This build tracks a distinctive opponent colour. It is not a trained PPO player. Use only where automation is allowed. Set up your controls, then stop at any time from the notification.");
        content.addView(info);
        button(content, "1 · Choose screenshot of the arena", () -> {
            Intent pick = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            pick.setType("image/*"); pick.addCategory(Intent.CATEGORY_OPENABLE);
            startActivityForResult(pick, PICK_IMAGE);
        });
        sample = new ImageView(this);
        sample.setAdjustViewBounds(true);
        sample.setMaxHeight(550);
        sample.setOnTouchListener((v, event) -> {
            if (event.getAction() != 1 || bitmap == null) return true;
            android.graphics.Matrix inverse = new android.graphics.Matrix();
            if (!sample.getImageMatrix().invert(inverse)) return true;
            float[] point = {event.getX() - sample.getPaddingLeft(), event.getY() - sample.getPaddingTop()};
            inverse.mapPoints(point);
            int x = Math.max(0, Math.min(bitmap.getWidth() - 1, (int) point[0]));
            int y = Math.max(0, Math.min(bitmap.getHeight() - 1, (int) point[1]));
            float nx = x / (float) bitmap.getWidth(), ny = y / (float) bitmap.getHeight();
            if (sampleMode == TARGET) {
                long red = 0, green = 0, blue = 0;
                int count = 0;
                for (int py = Math.max(0, y - 2); py <= Math.min(bitmap.getHeight() - 1, y + 2); py++)
                    for (int px = Math.max(0, x - 2); px <= Math.min(bitmap.getWidth() - 1, x + 2); px++) {
                        int pixel = bitmap.getPixel(px, py);
                        red += Color.red(pixel); green += Color.green(pixel); blue += Color.blue(pixel); count++;
                    }
                getPreferences(0).edit().putInt("target_colour", Color.rgb(
                    (int) (red / count), (int) (green / count), (int) (blue / count))).apply();
            }
            if (sampleMode == ATTACK) getPreferences(0).edit()
                .putFloat("attack_x", nx).putFloat("attack_y", ny).apply();
            if (sampleMode == CAMERA) getPreferences(0).edit()
                .putFloat("camera_x", nx).putFloat("camera_y", ny).apply();
            if (sampleMode == JOYSTICK) getPreferences(0).edit()
                .putFloat("joystick_x", nx).putFloat("joystick_y", ny).apply();
            refresh(); return true;
        });
        content.addView(sample);
        button(content, "Tap opponent colour in screenshot", () -> { sampleMode = TARGET; refresh(); });
        button(content, "Tap attack button in screenshot", () -> { sampleMode = ATTACK; refresh(); });
        button(content, "Tap safe camera area in screenshot", () -> { sampleMode = CAMERA; refresh(); });
        button(content, "Tap movement joystick centre in screenshot", () -> { sampleMode = JOYSTICK; refresh(); });
        button(content, "2 · Enable touch service in Android settings", () ->
            startActivity(new Intent(Settings.ACTION_ACCESSIBILITY_SETTINGS)));
        button(content, "3 · Grant screen capture", () ->
            startActivity(new Intent(this, ConsentActivity.class)));
        button(content, "4 · Arm agent, then switch to allowed arena", () -> {
            if (!CaptureService.isRunning() || !GestureService.isConnected()
                || !getPreferences(0).contains("target_colour")
                || !getPreferences(0).contains("attack_x")
                || !getPreferences(0).contains("camera_x")
                || !getPreferences(0).contains("joystick_x")) {
                status.setText("Capture, touch service and all four screenshot points are required.");
                return;
            }
            GestureService.configure(
                getPreferences(0).getFloat("attack_x", .88f), getPreferences(0).getFloat("attack_y", .73f),
                getPreferences(0).getFloat("camera_x", .72f), getPreferences(0).getFloat("camera_y", .46f),
                getPreferences(0).getFloat("joystick_x", .16f), getPreferences(0).getFloat("joystick_y", .78f));
            CaptureService.arm(getPreferences(0).getInt("target_colour", Color.RED));
            refresh();
        });
        button(content, "EMERGENCY STOP", () -> {
            CaptureService.disarm(); GestureService.disable();
            Intent stop = new Intent(this, CaptureService.class).setAction(CaptureService.ACTION_STOP);
            startService(stop); refresh();
        });
        setContentView(scroll);
        refresh();
    }

    @Override protected void onResume() { super.onResume(); if (status != null) refresh(); }

    private void refresh() {
        status.setText("Capture: " + CaptureService.isRunning()
            + " · Touch service: " + GestureService.isConnected()
            + " · Target colour selected: " + getPreferences(0).contains("target_colour")
            + " · Controls calibrated: " + (getPreferences(0).contains("attack_x")
                && getPreferences(0).contains("camera_x") && getPreferences(0).contains("joystick_x"))
            + " · Next screenshot tap: " + new String[]{"opponent colour", "attack", "camera", "joystick"}[sampleMode]
            + " · Agent armed: " + CaptureService.isArmed());
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request != PICK_IMAGE || result != RESULT_OK || data == null) return;
        try {
            Uri uri = data.getData();
            if (uri == null) return;
            bitmap = ImageDecoder.decodeBitmap(ImageDecoder.createSource(getContentResolver(), uri),
                (decoder, info, source) -> decoder.setAllocator(ImageDecoder.ALLOCATOR_SOFTWARE));
            sample.setImageBitmap(bitmap);
        } catch (IOException ex) { status.setText("Could not read screenshot: " + ex.getMessage()); }
    }
}
