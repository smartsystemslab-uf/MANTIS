import mlflow
import os
import json
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class MLflowExporter:
    def __init__(self, tracking_uri: str = "sqlite:///mlflow.db", experiment_name: str = "mantis_experiments"):
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self.active_run_id: Optional[str] = None
        
        try:
            mlflow.set_tracking_uri(self.tracking_uri)
            mlflow.set_experiment(self.experiment_name)
        except Exception as e:
            logger.warning(f"Failed to initialize MLflow: {e}")

    def start_run(self, run_name: str, config_hash: str, seed: int):
        """Starts an MLflow run and logs initial configuration."""
        try:
            run = mlflow.start_run(run_name=run_name)
            self.active_run_id = run.info.run_id
            mlflow.log_param("config_hash", config_hash)
            mlflow.log_param("seed", seed)
            logger.info(f"Started MLflow run: {self.active_run_id}")
        except Exception as e:
            logger.warning(f"Failed to start MLflow run: {e}")

    def log_metrics(self, metrics: Dict[str, float]):
        """Logs metrics (e.g., latency, token count, attack success rate)."""
        if not self.active_run_id:
            return
        try:
            mlflow.log_metrics(metrics)
        except Exception as e:
            logger.warning(f"Failed to log MLflow metrics: {e}")
            
    def log_artifact(self, file_path: str, artifact_path: Optional[str] = None):
        """Logs a file artifact (like traces.jsonl) to the current run."""
        if not self.active_run_id:
            return
        try:
            if os.path.exists(file_path):
                mlflow.log_artifact(file_path, artifact_path)
        except Exception as e:
            logger.warning(f"Failed to log MLflow artifact: {e}")

    def end_run(self, status: str = "FINISHED"):
        """Ends the active MLflow run."""
        if not self.active_run_id:
            return
        try:
            mlflow.end_run(status=status)
            self.active_run_id = None
        except Exception as e:
            logger.warning(f"Failed to end MLflow run: {e}")
