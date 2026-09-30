using System;
using System.IO;
using Agent.UI;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Agent.Editor
{
    public static class AndroidBuild
    {
        public static void Build()
        {
            Directory.CreateDirectory("Assets/Scenes");
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            new GameObject("Dashboard").AddComponent<Dashboard>();
            const string path = "Assets/Scenes/Main.unity";
            EditorSceneManager.SaveScene(scene, path);
            PlayerSettings.SetApplicationIdentifier(NamedBuildTarget.Android, "com.harvey.pvpagent");
            PlayerSettings.productName = "PvP Vision Agent";
            PlayerSettings.bundleVersion = "0.1.0";
            PlayerSettings.Android.bundleVersionCode = 1;
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel29;
            PlayerSettings.Android.targetSdkVersion = AndroidSdkVersions.AndroidApiLevelAuto;
            EditorUserBuildSettings.SwitchActiveBuildTarget(BuildTargetGroup.Android, BuildTarget.Android);
            Directory.CreateDirectory("../build/Android");
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
                scenes = new[] { path },
                locationPathName = "../build/Android/MinecraftPvPAgent-v0.1.0.apk",
                target = BuildTarget.Android,
                options = BuildOptions.None
            });
            if (report.summary.result != UnityEditor.Build.Reporting.BuildResult.Succeeded)
                throw new Exception("Android build failed: " + report.summary.result);
        }
    }
}
