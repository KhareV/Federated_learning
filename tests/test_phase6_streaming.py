import numpy as np

from inference.streaming import StreamingInferenceEngine, WindowInference


def test_streaming_is_deterministic_and_coalesces_events():
    def predictor(window, fs):
        return WindowInference(0.9 if np.mean(window) > 0.5 else 0.1, "GOOD", 0.9)

    samples = np.concatenate((np.zeros(1250), np.ones(5000), np.zeros(1250)))
    def replay():
        engine = StreamingInferenceEngine(predictor, 250, threshold=0.5, smoothing_windows=1)
        outputs = []
        for chunk in np.array_split(samples, 7):
            outputs.extend(engine.push(chunk))
        engine.finalize()
        return outputs, [event.to_dict() for event in engine.events], engine.summary()

    first = replay()
    second = replay()
    assert first == second
    assert len(first[1]) == 1
    assert first[1][0]["state"] == "POTENTIALLY_ABNORMAL"
    assert first[0][0]["state"] == "NORMAL"
    assert first[2]["state_flap_count"] >= 1


def test_unreliable_signal_does_not_become_abnormal():
    engine = StreamingInferenceEngine(
        lambda window, fs: WindowInference(0.99, "UNRELIABLE"), 100,
        threshold=0.1,
    )
    outputs = engine.push(np.ones(1000))
    engine.finalize()
    assert outputs
    assert all(item["state"] == "UNRELIABLE" for item in outputs)
    assert all(event.state == "UNRELIABLE" for event in engine.events)
