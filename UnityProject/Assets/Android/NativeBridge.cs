using System;
using UnityEngine;

namespace Agent.Android
{
    public static class NativeBridge
    {
        const string ClassName = "com.harvey.pvpagent.AgentBridge";
        static void Invoke(string method)
        {
            if (Application.platform != RuntimePlatform.Android) return;
            using (var bridge = new AndroidJavaClass(ClassName)) bridge.CallStatic(method);
        }
        public static void RequestCapture() => Invoke("requestCapture");
        public static void Stop() => Invoke("stop");
        public static void OpenAccessibilitySettings() => Invoke("openAccessibilitySettings");
        public static string Status()
        {
            if (Application.platform != RuntimePlatform.Android) return "Android device required";
            try { using (var bridge = new AndroidJavaClass(ClassName)) return bridge.CallStatic<string>("status"); }
            catch (Exception ex) { return "Bridge unavailable: " + ex.Message; }
        }
    }
}
