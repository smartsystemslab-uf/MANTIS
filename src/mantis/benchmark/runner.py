import asyncio
import statistics
import time
import json
from pathlib import Path
from mantis.config.models import ExperimentConfig
import yaml
import subprocess
import os


def _percentile(sorted_values: list, pct: float) -> float:
    """Nearest-rank percentile -- well-defined even for very small samples
    (e.g. a single repetition), unlike interpolation-based methods."""
    if not sorted_values:
        return 0.0
    idx = max(0, min(len(sorted_values) - 1, int(round(pct / 100 * len(sorted_values))) - 1))
    return sorted_values[idx]

class BenchmarkRunner:
    def __init__(self, config_path: str):
        self.config_path = config_path
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)

        self.benchmark = self.config.get("benchmark", {})
        self.concurrency = self.benchmark.get("concurrency", 1)
        self.repetitions = self.benchmark.get("repetitions", 1)
        self.mock_llm = self.benchmark.get("mock_llm", False)
        self.scaling_repetitions = self.benchmark.get("scaling_repetitions")

    async def run_single(self, run_idx: int) -> dict:
        start_time = time.time()

        env = os.environ.copy()
        if self.mock_llm:
            env["MANTIS_MOCK_LLM"] = "1"

        # We run the command via subprocess to ensure a clean process state per run
        # but we use asyncio to manage concurrency.
        process = await asyncio.create_subprocess_exec(
            "mantis", "--run", self.config_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env=env,
        )

        stdout, stderr = await process.communicate()
        end_time = time.time()

        latency = end_time - start_time
        success = process.returncode == 0

        return {
            "run_idx": run_idx,
            "success": success,
            "latency_s": latency,
            "error": stderr.decode() if not success else None
        }

    async def run_batch(self, start_idx: int, count: int) -> list:
        tasks = []
        for i in range(count):
            tasks.append(self.run_single(start_idx + i))
        return await asyncio.gather(*tasks)

    def _run_at(self, total_runs: int) -> dict:
        results = []
        start_time = time.time()

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            for i in range(0, total_runs, self.concurrency):
                batch_count = min(self.concurrency, total_runs - i)
                batch_results = loop.run_until_complete(self.run_batch(i, batch_count))
                results.extend(batch_results)
        finally:
            loop.close()

        end_time = time.time()

        successful_runs = [r for r in results if r["success"]]
        latencies = sorted(r["latency_s"] for r in successful_runs)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        # stdev needs >=2 points; a single repetition has no meaningful
        # spread, so report 0.0 rather than raising.
        stdev_latency = statistics.stdev(latencies) if len(latencies) >= 2 else 0.0

        return {
            "total_runs": total_runs,
            "successful_runs": len(successful_runs),
            "failed_runs": total_runs - len(successful_runs),
            "concurrency": self.concurrency,
            "mock_llm": self.mock_llm,
            "total_time_s": end_time - start_time,
            "avg_latency_s": avg_latency,
            "stdev_latency_s": stdev_latency,
            "p50_latency_s": _percentile(latencies, 50),
            "p90_latency_s": _percentile(latencies, 90),
            "p99_latency_s": _percentile(latencies, 99),
            "throughput_runs_per_s": len(successful_runs) / (end_time - start_time) if (end_time - start_time) > 0 else 0,
            "runs": results
        }

    def execute(self) -> dict:
        if self.scaling_repetitions:
            levels = []
            for n in self.scaling_repetitions:
                level_report = self._run_at(n)
                level_report["repetitions"] = n
                levels.append(level_report)
            return {
                "scaling": True,
                "concurrency": self.concurrency,
                "mock_llm": self.mock_llm,
                "levels": levels,
            }

        return self._run_at(self.repetitions)
