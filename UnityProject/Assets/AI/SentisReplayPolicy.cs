using System;
using Unity.InferenceEngine;

namespace Agent.AI
{
    // Foreground replay only. Android's background service needs its own native runtime.
    public sealed class SentisReplayPolicy : IDisposable
    {
        readonly Worker worker;
        public SentisReplayPolicy(ModelAsset asset)
        {
            if (asset == null) throw new ArgumentNullException(nameof(asset));
            worker = new Worker(ModelLoader.Load(asset), BackendType.CPU);
        }
        public AgentAction Evaluate(Observation observation)
        {
            using (var input = new Tensor<float>(new TensorShape(1, Observation.Size), observation.ToArray()))
            {
                worker.Schedule(input);
                var output = worker.PeekOutput() as Tensor<float>;
                if (output == null || output.shape.length != 6) throw new InvalidOperationException("Incompatible policy output");
                var values = output.DownloadToArray();
                return AgentAction.FromArray(values);
            }
        }
        public void Dispose() => worker.Dispose();
    }
}
