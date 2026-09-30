using Agent.Android;
using UnityEngine;

namespace Agent.UI
{
    public sealed class Dashboard : MonoBehaviour
    {
        void Awake() { Application.runInBackground = true; }
        void OnGUI()
        {
            float s = Mathf.Max(1f, Screen.width / 480f);
            GUI.matrix = Matrix4x4.Scale(new Vector3(s, s, 1));
            float w = Screen.width / s;
            GUILayout.BeginArea(new Rect(20, 20, w - 40, Screen.height / s - 30));
            GUILayout.Label("PvP Vision Agent — research build");
            GUILayout.Label(NativeBridge.Status());
            GUILayout.Label("Autonomous input locked: native policy and trained model required.");
            if (GUILayout.Button("Request screen capture", GUILayout.Height(52))) NativeBridge.RequestCapture();
            if (GUILayout.Button("Open accessibility settings", GUILayout.Height(52))) NativeBridge.OpenAccessibilitySettings();
            if (GUILayout.Button("STOP CAPTURE AND AGENT", GUILayout.Height(64))) NativeBridge.Stop();
            GUILayout.EndArea();
        }
        void OnApplicationQuit() => NativeBridge.Stop();
    }
}
