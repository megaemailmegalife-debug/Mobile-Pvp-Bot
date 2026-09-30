# Project ledger

PROJECT VERSION: 0.2.0-source

CURRENT PHASE: Native Android experimental agent awaiting cloud build and device verification

COMPLETED: Repository structure; native Android app UI, capture consent, capture foreground service, screenshot colour and control calibration, simple HSV tracker, bounded camera/attack/forward gestures, notification stop; Unity research source; feature/reward contracts; synthetic PPO training and ONNX export source; native cloud APK workflow.

IN PROGRESS: Actual cloud build, Android device QA, robust vision and PPO training/inference.

KNOWN ISSUES: No trained PvP model. Native HSV colour tracker is a heuristic with false positives and limited combat behaviour. It has not been compiled or device-tested. Controls and projection rotation need on-device validation. No kill/death detectors, reward-driven live policy or replay fixtures. No APK.

TECHNICAL DEBT: Replace HSV vision with evaluated HUD/target detectors; add native tensor inference and metadata validation; create recording/replay fixtures; improve responsive movement and multimodal gesture cancellation.

TEST STATUS: Five Python contract/reward checks and one Java vision detector check pass locally. Android integration remains untested.

BUILD STATUS: Android SDK/Gradle unavailable in this environment; GitHub native APK workflow configured, unexecuted.

NEXT MILESTONE: Push source to GitHub, run native APK workflow, repair compiler errors, then validate consent, projection, calibration, input and stop behaviour on an Android phone in a permitted private arena.
