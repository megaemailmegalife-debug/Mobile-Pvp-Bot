package com.harvey.pvpagent;

import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Service;
import android.content.Context;
import android.content.Intent;
import android.content.pm.ServiceInfo;
import android.graphics.PixelFormat;
import android.hardware.display.DisplayManager;
import android.hardware.display.VirtualDisplay;
import android.media.Image;
import android.media.ImageReader;
import android.media.projection.MediaProjection;
import android.media.projection.MediaProjectionManager;
import android.os.Build;
import android.os.Handler;
import android.os.HandlerThread;
import android.os.IBinder;
import java.nio.ByteBuffer;

public final class CaptureService extends Service {
    public static final String ACTION_START = "com.harvey.pvpagent.START";
    public static final String ACTION_STOP = "com.harvey.pvpagent.STOP";
    public static final String RESULT_CODE = "result_code";
    public static final String RESULT_DATA = "result_data";
    private static final String CHANNEL = "pvp_capture";
    private static volatile boolean running;
    private static volatile byte[] latestRgba;
    private HandlerThread captureThread;
    private ImageReader reader;
    private VirtualDisplay display;
    private MediaProjection projection;
    private final MediaProjection.Callback callback = new MediaProjection.Callback() {
        @Override public void onStop() { stopSelf(); }
    };

    public static boolean isRunning() { return running; }
    // The caller must treat this as transient; the byte array is replaced atomically each frame.
    public static byte[] latestFrame() { return latestRgba; }
    @Override public IBinder onBind(Intent intent) { return null; }

    @Override public int onStartCommand(Intent intent, int flags, int startId) {
        if (intent == null || ACTION_STOP.equals(intent.getAction())) {
            GestureService.disable();
            stopSelf();
            return START_NOT_STICKY;
        }
        if (!ACTION_START.equals(intent.getAction()) || running) return START_NOT_STICKY;
        createNotification();
        try {
            if (Build.VERSION.SDK_INT >= 29)
                startForeground(15, notification(), ServiceInfo.FOREGROUND_SERVICE_TYPE_MEDIA_PROJECTION);
            else startForeground(15, notification());
            Intent data = Build.VERSION.SDK_INT >= 33
                ? intent.getParcelableExtra(RESULT_DATA, Intent.class)
                : intent.getParcelableExtra(RESULT_DATA);
            if (data == null) throw new IllegalArgumentException("Projection consent missing");
            MediaProjectionManager manager = (MediaProjectionManager) getSystemService(Context.MEDIA_PROJECTION_SERVICE);
            projection = manager.getMediaProjection(intent.getIntExtra(RESULT_CODE, 0), data);
            if (projection == null) throw new IllegalStateException("Projection refused");
            captureThread = new HandlerThread("pvp-capture");
            captureThread.start();
            Handler handler = new Handler(captureThread.getLooper());
            projection.registerCallback(callback, handler);
            final int width = 256, height = 144;
            reader = ImageReader.newInstance(width, height, PixelFormat.RGBA_8888, 2);
            reader.setOnImageAvailableListener(source -> {
                Image image = null;
                try {
                    image = source.acquireLatestImage();
                    if (image == null) return;
                    Image.Plane plane = image.getPlanes()[0];
                    ByteBuffer buffer = plane.getBuffer();
                    int stride = plane.getRowStride(), pixelStride = plane.getPixelStride();
                    byte[] pixels = new byte[width * height * 4];
                    for (int y = 0; y < height; y++) {
                        int row = y * stride;
                        for (int x = 0; x < width; x++) {
                            int src = row + x * pixelStride, dst = (y * width + x) * 4;
                            pixels[dst] = buffer.get(src);
                            pixels[dst + 1] = buffer.get(src + 1);
                            pixels[dst + 2] = buffer.get(src + 2);
                            pixels[dst + 3] = buffer.get(src + 3);
                        }
                    }
                    latestRgba = pixels;
                } catch (RuntimeException ignored) {
                    // A revoked projection is handled by its registered callback.
                } finally { if (image != null) image.close(); }
            }, handler);
            display = projection.createVirtualDisplay("PvP capture", width, height,
                getResources().getDisplayMetrics().densityDpi,
                DisplayManager.VIRTUAL_DISPLAY_FLAG_AUTO_MIRROR,
                reader.getSurface(), null, handler);
            running = true;
        } catch (RuntimeException e) {
            GestureService.disable();
            stopSelf();
        }
        return START_NOT_STICKY;
    }

    private void createNotification() {
        NotificationManager manager = (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        manager.createNotificationChannel(new NotificationChannel(CHANNEL, "Screen capture", NotificationManager.IMPORTANCE_LOW));
    }

    private Notification notification() {
        Intent stop = new Intent(this, CaptureService.class).setAction(ACTION_STOP);
        PendingIntent pending = PendingIntent.getService(this, 0, stop,
            PendingIntent.FLAG_IMMUTABLE | PendingIntent.FLAG_UPDATE_CURRENT);
        return new Notification.Builder(this, CHANNEL)
            .setSmallIcon(android.R.drawable.ic_menu_close_clear_cancel)
            .setContentTitle("PvP agent screen capture")
            .setContentText("Capture active; autonomous controls locked")
            .setOngoing(true)
            .addAction(new Notification.Action.Builder(null, "Stop capture and agent", pending).build())
            .build();
    }

    @Override public void onDestroy() {
        running = false;
        latestRgba = null;
        GestureService.disable();
        if (display != null) { display.release(); display = null; }
        if (reader != null) { reader.close(); reader = null; }
        if (projection != null) {
            projection.unregisterCallback(callback);
            projection.stop(); projection = null;
        }
        if (captureThread != null) { captureThread.quitSafely(); captureThread = null; }
        super.onDestroy();
    }
}
