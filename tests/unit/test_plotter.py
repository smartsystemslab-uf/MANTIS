import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from mantis.benchmark.plotter import plot_volume_scaling


def _levels(axis, fixed_key, fixed_value, values):
    return [
        {axis: v, fixed_key: fixed_value, "avg_latency_s": 1.0 + v, "throughput_runs_per_s": 0.1 * v}
        for v in values
    ]


def test_plot_repetitions_scaling_uses_repetitions_as_x(tmp_path):
    # Regression test: plot_volume_scaling once hardcoded "repetitions" as
    # the x-axis key regardless of which axis was actually varied -- a
    # concurrency-scaling result (every level sharing the same fixed
    # repetitions value) would have plotted the same x-value repeated N
    # times instead of the real concurrency levels.
    data = {
        "scaling_axis": "repetitions",
        "concurrency": 2,
        "levels": _levels("repetitions", "concurrency", 2, [1, 2, 4, 8]),
    }
    path = tmp_path / "reps.json"
    path.write_text(json.dumps(data))

    plt.close("all")
    plot_volume_scaling(str(path), str(tmp_path / "reps.png"))
    fig = plt.gcf()
    x_data = list(fig.axes[0].lines[0].get_xdata())
    assert x_data == [1, 2, 4, 8]
    assert "Repetitions" in fig.axes[0].get_xlabel()


def test_plot_concurrency_scaling_uses_concurrency_as_x(tmp_path):
    data = {
        "scaling_axis": "concurrency",
        "repetitions": 8,
        "levels": _levels("concurrency", "repetitions", 8, [1, 2, 4, 8]),
    }
    path = tmp_path / "conc.json"
    path.write_text(json.dumps(data))

    plt.close("all")
    plot_volume_scaling(str(path), str(tmp_path / "conc.png"))
    fig = plt.gcf()
    x_data = list(fig.axes[0].lines[0].get_xdata())
    assert x_data == [1, 2, 4, 8]
    assert "Concurrency" in fig.axes[0].get_xlabel()
