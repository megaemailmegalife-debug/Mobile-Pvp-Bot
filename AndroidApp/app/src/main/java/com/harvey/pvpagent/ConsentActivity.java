package com.harvey.pvpagent;

import android.app.Activity;
import android.content.Intent;
import android.media.projection.MediaProjectionManager;
import android.os.Bundle;

public final class ConsentActivity extends Activity {
    private static final int CONSENT = 1001;

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        if (state != null) { finish(); return; }
        MediaProjectionManager manager = (MediaProjectionManager) getSystemService(MEDIA_PROJECTION_SERVICE);
        startActivityForResult(manager.createScreenCaptureIntent(), CONSENT);
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request == CONSENT && result == RESULT_OK && data != null) {
            Intent service = new Intent(this, CaptureService.class);
            service.setAction(CaptureService.ACTION_START);
            service.putExtra(CaptureService.RESULT_CODE, result);
            service.putExtra(CaptureService.RESULT_DATA, data);
            startForegroundService(service);
        }
        finish();
    }
}
