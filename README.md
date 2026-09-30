# Minecraft PvP Vision Agent — Android source, v0.2.0

An Android-only research project for permitted private arenas. The intended boundary is visible screen pixels, local perception, a versioned ONNX policy, bounded gestures, and explicit Android consent. No game memory, packets, or hidden state are used.

**Status:** The new `AndroidApp/` has a native background colour-tracking agent with explicit capture/accessibility controls. It is a limited heuristic for distinctive opponent colours in permitted training arenas, **not** a trained PPO PvP policy. No Android APK or on-device verification exists yet. See `PROJECT_LEDGER.md`.

## Layout

- `AndroidApp/` — primary native Android application: capture, colour vision, calibration, bounded gestures, notification stop.
- `UnityProject/` — earlier Unity 6 research source with feature/action contracts and Sentis replay backend; not the recommended APK route.
- `UnityProject/Assets/Plugins/Android/PvPBridge.androidlib/` — Android capture foreground service and accessibility gesture service.
- `Training/` — feature-only PPO training example, evaluation and ONNX export. Its example environment is synthetic and cannot produce a capable Minecraft policy.
- `Config/` — sample calibration and reward profile.
- `.github/workflows/native-android.yml` — recommended phone-controlled native APK build.

## Build from a phone

1. Create a private GitHub repository and upload the contents of this directory (the `UnityProject` directory must retain its own `Assets`, `Packages` and `ProjectSettings`).
2. Run **Actions → Native Android APK → Run workflow** on GitHub mobile/web. It uses the hosted Android SDK and Gradle to create a debug-signed APK without Unity credentials.
3. Download the `PvPVisionAgent-v0.2.0-debug-apk` workflow artifact on Android, unzip it, and install `app-debug.apk`. Android may ask whether that browser or file manager may install unknown apps.
4. Allow notification permission. In Android settings, explicitly enable the app's accessibility service. Android may require an additional **Allow restricted settings** step for a sideloaded accessibility app.
5. Save a screenshot of an allowed training arena with a visually distinctive opponent and your touch controls. Import it, then tap the opponent's colour, attack button, safe camera area and joystick centre. Grant capture and choose the entire display rather than this app alone. Arm the agent and switch to Minecraft within five seconds. The notification stops capture and input.

This repository has not been pushed to GitHub. No credentials are included. The Android SDK and Gradle are absent from the present environment and cannot be downloaded through its network policy, so the APK cannot be built here. The workflow has not yet run.

## Permissions and safety

The user must consent to each MediaProjection session and manually enable the accessibility service in system settings. A foreground notification exposes capture and includes a **Stop capture and agent** action. The app also has an emergency stop. Projection revocation and permission denial disable input. Gesture coordinates are calibrated, clamped and rate limited. A gesture already dispatched may take up to 170 ms to finish. Android may stop background execution or restrict capture of protected content. Only use this in places where automation is allowed.

No screen frames are uploaded. This early implementation does not persist frame telemetry. Delete app data in Android Settings to remove local configuration. The sample profile is illustrative; it is not calibrated to a device or Minecraft HUD.

## Model contract

The policy accepts `float32[1,12]` and returns `float32[1,6]` in order: movement X/Y, camera X/Y, attack probability, jump probability. `Models/metadata.example.json` records the schema. The model must be trained and evaluated using a representative permitted environment; the included synthetic Gym environment merely tests the pipeline. It must never be represented as a PvP baseline.

The native `AndroidApp/` deliberately uses a simple colour tracker rather than loading the model. It may aim at similarly coloured scenery, miss opponents whose appearance differs, or fail with another touch layout. It does not detect kills, deaths or health and has no reward telemetry. PPO inference and reliable trained weights remain future work. The Unity research source still cannot drive a game from a paused activity.

## Local checks

`python3 -m unittest discover -s Training/tests -v` tests the portable schemas and reward rules. The native workflow also compiles and tests the actual Java colour detector using a minimal Android colour shim. A full Android cloud build and device tests are still required.
