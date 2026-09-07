from unittest.mock import AsyncMock, patch
import yaml
from mantis.benchmark.runner import BenchmarkRunner, _percentile


def _write_config(tmp_path, benchmark_block):
    cfg = {
        "experiment": {"name": "bench_test", "seed": 1, "domain": "front_office",
                        "workflow": "front_office_monitoring", "scenario": "front_office_monitoring"},
        "benchmark": benchmark_block,
    }
    path = tmp_path / "bench.yaml"
    path.write_text(yaml.dump(cfg))
    return str(path)


class _FakeProcess:
    def __init__(self, returncode=0):
        self.returncode = returncode

    async def communicate(self):
        return b"", b""


def test_single_level_execute_unchanged(tmp_path):
    # execute() manages its own event loop internally (its real call site in
    # cli/main.py is synchronous) -- these tests call it the same way, not
    # from inside an already-running loop.
    config_path = _write_config(tmp_path, {"concurrency": 2, "repetitions": 4})
    runner = BenchmarkRunner(config_path)

    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=_FakeProcess())):
        report = runner.execute()

    assert report["total_runs"] == 4
    assert report["successful_runs"] == 4
    assert report["concurrency"] == 2
    assert "scaling" not in report


def test_mock_llm_flag_sets_env_var(tmp_path):
    config_path = _write_config(tmp_path, {"repetitions": 1, "mock_llm": True})
    runner = BenchmarkRunner(config_path)

    fake_exec = AsyncMock(return_value=_FakeProcess())
    with patch("asyncio.create_subprocess_exec", new=fake_exec):
        runner.execute()

    _, kwargs = fake_exec.call_args
    assert kwargs["env"]["MANTIS_MOCK_LLM"] == "1"


def test_percentile_nearest_rank_on_small_samples():
    assert _percentile([], 50) == 0.0
    assert _percentile([5.0], 50) == 5.0
    assert _percentile([5.0], 99) == 5.0
    values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    assert _percentile(values, 50) == 5.0
    assert _percentile(values, 90) == 9.0
    assert _percentile(values, 99) == 10.0


def test_execute_reports_stdev_and_percentiles(tmp_path):
    config_path = _write_config(tmp_path, {"concurrency": 1, "repetitions": 3})
    runner = BenchmarkRunner(config_path)

    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=_FakeProcess())):
        report = runner.execute()

    for key in ("stdev_latency_s", "p50_latency_s", "p90_latency_s", "p99_latency_s"):
        assert key in report

    single_config = _write_config(tmp_path, {"concurrency": 1, "repetitions": 1})
    single_runner = BenchmarkRunner(single_config)
    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=_FakeProcess())):
        single_report = single_runner.execute()
    assert single_report["stdev_latency_s"] == 0.0  # stdev undefined for n=1, not an error


def test_scaling_repetitions_produces_one_level_per_entry(tmp_path):
    config_path = _write_config(tmp_path, {"concurrency": 1, "scaling_repetitions": [1, 2, 4]})
    runner = BenchmarkRunner(config_path)

    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=_FakeProcess())):
        report = runner.execute()

    assert report["scaling"] is True
    assert [lv["repetitions"] for lv in report["levels"]] == [1, 2, 4]
    assert all(lv["successful_runs"] == lv["repetitions"] for lv in report["levels"])
