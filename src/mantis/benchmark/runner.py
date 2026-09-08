import asyncio
import resource
import statistics
import time
import json
from pathlib import Path
from mantis.config.models import ExperimentConfig
import yaml
import subprocess
import os
import sys


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
        self._run_artifacts_dir = (
            Path("run_artifacts") / self.config.get("experiment", {}).get("name", "")
        )

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

        # Trace volume (spec §WP6: "latency, throughput, CPU, memory, and
        # trace volume"). Each run overwrites the same experiment's
        # traces.jsonl (TraceArtifactWriter starts every run's file empty),
        # so this must be read immediately after this specific run
        # completes, before the next repetition's subprocess starts.
        trace_event_count = None
        trace_file = self._run_artifacts_dir / "traces.jsonl"
        if trace_file.exists():
            with open(trace_file, "r") as f:
                trace_event_count = sum(1 for line in f if line.strip())

        return {
            "run_idx": run_idx,
            "success": success,
            "latency_s": latency,
            "trace_event_count": trace_event_count,
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
        # CPU/memory (spec §WP6). Each repetition is a separate `mantis
        # --run` subprocess (see run_single), so its CPU time and peak RSS
        # are only visible to the parent via RUSAGE_CHILDREN -- ru_utime/
        # ru_stime accumulate additively across every child that has exited,
        # so a delta over this batch is exactly the aggregate CPU time spent
        # by these `total_runs` subprocesses. ru_maxrss is a high-water mark
        # (not additive), so it's reported as the peak observed by the end
        # of this batch rather than a delta. RUSAGE_CHILDREN is POSIX-only
        # (Linux/macOS; not Windows), consistent with the rest of this
        # POSIX-oriented toolchain (uvicorn, the MCP stdio subprocess, etc).
        rusage_before = resource.getrusage(resource.RUSAGE_CHILDREN)

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
        rusage_after = resource.getrusage(resource.RUSAGE_CHILDREN)
        cpu_time_s = (
            (rusage_after.ru_utime - rusage_before.ru_utime)
            + (rusage_after.ru_stime - rusage_before.ru_stime)
        )
        # ru_maxrss is KB on Linux, bytes on macOS.
        peak_rss_mb = rusage_after.ru_maxrss / (1024 if sys.platform == "darwin" else 1) / 1024

        successful_runs = [r for r in results if r["success"]]
        latencies = sorted(r["latency_s"] for r in successful_runs)
        avg_latency = sum(latencies) / len(latencies) if latencies else 0
        # stdev needs >=2 points; a single repetition has no meaningful
        # spread, so report 0.0 rather than raising.
        stdev_latency = statistics.stdev(latencies) if len(latencies) >= 2 else 0.0

        trace_counts = [r["trace_event_count"] for r in successful_runs if r.get("trace_event_count") is not None]
        avg_trace_events = sum(trace_counts) / len(trace_counts) if trace_counts else None

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
            "cpu_time_s": cpu_time_s,
            "peak_rss_mb": peak_rss_mb,
            "avg_trace_events_per_run": avg_trace_events,
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

    # ------------------------------------------------------------------
    # Gap 4 (spec §WP6): CSV and Parquet summary export
    # "Generate CSV/Parquet summaries and paper-ready plots through scripts."
    # Called by cli/main.py after execute() saves the JSON result.
    # ------------------------------------------------------------------

    def export_csv(self, results: dict, output_path: str) -> None:
        """Write a flat CSV summary of benchmark results.

        For a scaling run each level becomes one row; for a single-mode run
        the aggregate statistics are written as a single-row CSV.
        """
        import pandas as pd

        if results.get("scaling"):
            rows = []
            for lv in results.get("levels", []):
                rows.append({
                    "repetitions": lv.get("repetitions"),
                    "concurrency": lv.get("concurrency"),
                    "mock_llm": lv.get("mock_llm"),
                    "successful_runs": lv.get("successful_runs"),
                    "failed_runs": lv.get("failed_runs"),
                    "avg_latency_s": lv.get("avg_latency_s"),
                    "stdev_latency_s": lv.get("stdev_latency_s"),
                    "p50_latency_s": lv.get("p50_latency_s"),
                    "p90_latency_s": lv.get("p90_latency_s"),
                    "p99_latency_s": lv.get("p99_latency_s"),
                    "throughput_runs_per_s": lv.get("throughput_runs_per_s"),
                    "total_time_s": lv.get("total_time_s"),
                    "cpu_time_s": lv.get("cpu_time_s"),
                    "peak_rss_mb": lv.get("peak_rss_mb"),
                    "avg_trace_events_per_run": lv.get("avg_trace_events_per_run"),
                })
        else:
            rows = [{
                "repetitions": results.get("total_runs"),
                "concurrency": results.get("concurrency"),
                "mock_llm": results.get("mock_llm"),
                "successful_runs": results.get("successful_runs"),
                "failed_runs": results.get("failed_runs"),
                "avg_latency_s": results.get("avg_latency_s"),
                "stdev_latency_s": results.get("stdev_latency_s"),
                "p50_latency_s": results.get("p50_latency_s"),
                "p90_latency_s": results.get("p90_latency_s"),
                "p99_latency_s": results.get("p99_latency_s"),
                "throughput_runs_per_s": results.get("throughput_runs_per_s"),
                "total_time_s": results.get("total_time_s"),
                "cpu_time_s": results.get("cpu_time_s"),
                "peak_rss_mb": results.get("peak_rss_mb"),
                "avg_trace_events_per_run": results.get("avg_trace_events_per_run"),
            }]

        df = pd.DataFrame(rows)
        df.to_csv(output_path, index=False)
        print(f"Benchmark CSV saved to {output_path}")

    def export_parquet(self, results: dict, output_path: str) -> None:
        """Write a Parquet summary of benchmark results (same schema as CSV).

        Requires pyarrow or fastparquet. If neither is installed the method
        logs a clear message instead of crashing the whole benchmark run.
        """
        import pandas as pd

        # Re-use the same flattening logic as export_csv
        if results.get("scaling"):
            rows = []
            for lv in results.get("levels", []):
                rows.append({
                    "repetitions": lv.get("repetitions"),
                    "concurrency": lv.get("concurrency"),
                    "mock_llm": lv.get("mock_llm"),
                    "successful_runs": lv.get("successful_runs"),
                    "failed_runs": lv.get("failed_runs"),
                    "avg_latency_s": lv.get("avg_latency_s"),
                    "stdev_latency_s": lv.get("stdev_latency_s"),
                    "p50_latency_s": lv.get("p50_latency_s"),
                    "p90_latency_s": lv.get("p90_latency_s"),
                    "p99_latency_s": lv.get("p99_latency_s"),
                    "throughput_runs_per_s": lv.get("throughput_runs_per_s"),
                    "total_time_s": lv.get("total_time_s"),
                    "cpu_time_s": lv.get("cpu_time_s"),
                    "peak_rss_mb": lv.get("peak_rss_mb"),
                    "avg_trace_events_per_run": lv.get("avg_trace_events_per_run"),
                })
        else:
            rows = [{
                "repetitions": results.get("total_runs"),
                "concurrency": results.get("concurrency"),
                "mock_llm": results.get("mock_llm"),
                "successful_runs": results.get("successful_runs"),
                "failed_runs": results.get("failed_runs"),
                "avg_latency_s": results.get("avg_latency_s"),
                "stdev_latency_s": results.get("stdev_latency_s"),
                "p50_latency_s": results.get("p50_latency_s"),
                "p90_latency_s": results.get("p90_latency_s"),
                "p99_latency_s": results.get("p99_latency_s"),
                "throughput_runs_per_s": results.get("throughput_runs_per_s"),
                "total_time_s": results.get("total_time_s"),
                "cpu_time_s": results.get("cpu_time_s"),
                "peak_rss_mb": results.get("peak_rss_mb"),
                "avg_trace_events_per_run": results.get("avg_trace_events_per_run"),
            }]

        df = pd.DataFrame(rows)
        try:
            df.to_parquet(output_path, index=False)
            print(f"Benchmark Parquet saved to {output_path}")
        except ImportError:
            print(
                f"⚠ Parquet export skipped: install pyarrow or fastparquet "
                f"(`pip install pyarrow`) to enable Parquet output."
            )
