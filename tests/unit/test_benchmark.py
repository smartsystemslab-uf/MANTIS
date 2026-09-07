from unittest.mock import AsyncMock, patch
import yaml
from mantis.benchmark.runner import BenchmarkRunner


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


def test_scaling_repetitions_produces_one_level_per_entry(tmp_path):
    config_path = _write_config(tmp_path, {"concurrency": 1, "scaling_repetitions": [1, 2, 4]})
    runner = BenchmarkRunner(config_path)

    with patch("asyncio.create_subprocess_exec", new=AsyncMock(return_value=_FakeProcess())):
        report = runner.execute()

    assert report["scaling"] is True
    assert [lv["repetitions"] for lv in report["levels"]] == [1, 2, 4]
    assert all(lv["successful_runs"] == lv["repetitions"] for lv in report["levels"])
