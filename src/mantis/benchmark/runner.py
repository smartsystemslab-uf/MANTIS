import asyncio
import time
import json
from pathlib import Path
from mantis.config.models import ExperimentConfig
import yaml
import subprocess
import os

class BenchmarkRunner:
    def __init__(self, config_path: str):
        self.config_path = config_path
        with open(config_path, "r") as f:
            self.config = yaml.safe_load(f)
        
        self.benchmark = self.config.get("benchmark", {})
        self.concurrency = self.benchmark.get("concurrency", 1)
        self.repetitions = self.benchmark.get("repetitions", 1)

    async def run_single(self, run_idx: int) -> dict:
        start_time = time.time()
        
        # We run the command via subprocess to ensure a clean process state per run
        # but we use asyncio to manage concurrency.
        process = await asyncio.create_subprocess_exec(
            "mantis", "--run", self.config_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
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

    def execute(self) -> dict:
        results = []
        total_runs = self.repetitions
        
        start_time = time.time()
        
        loop = asyncio.get_event_loop()
        for i in range(0, total_runs, self.concurrency):
            batch_count = min(self.concurrency, total_runs - i)
            batch_results = loop.run_until_complete(self.run_batch(i, batch_count))
            results.extend(batch_results)
            
        end_time = time.time()
        
        successful_runs = [r for r in results if r["success"]]
        avg_latency = sum(r["latency_s"] for r in successful_runs) / len(successful_runs) if successful_runs else 0
        
        report = {
            "total_runs": total_runs,
            "successful_runs": len(successful_runs),
            "failed_runs": total_runs - len(successful_runs),
            "concurrency": self.concurrency,
            "total_time_s": end_time - start_time,
            "avg_latency_s": avg_latency,
            "runs": results
        }
        
        return report
