import numpy as np

from tools.benchmark_computer_vision import make_synthetic_inputs, summarize, timed_inference


def test_synthetic_benchmark_inputs_are_deterministic_and_nonmedical():
    first_oct, first_frame = make_synthetic_inputs()
    second_oct, second_frame = make_synthetic_inputs()
    assert first_oct.shape == (496, 768)
    assert first_frame.shape == (240, 320, 3)
    assert first_oct.dtype == np.uint8 and first_frame.dtype == np.uint8
    assert np.array_equal(first_oct, second_oct)
    assert np.array_equal(first_frame, second_frame)


def test_latency_summary_and_timed_measurement_report_units_and_samples():
    result = summarize([0.1, 0.2, 0.3])
    assert result["samples"] == 3
    assert result["units"] == "seconds"
    assert result["median"] == 0.2
    assert result["p95_nearest_rank"] == 0.3
    assert result["throughput_per_second_at_median"] == 5

    calls = []

    def infer():
        calls.append(len(calls))
        return len(calls)

    measured, output = timed_inference(infer, warmup=2, repeats=3)
    assert len(calls) == 5
    assert measured["samples"] == 3
    assert output == 5
