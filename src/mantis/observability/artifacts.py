import json
import hashlib
from datetime import datetime
from pathlib import Path
from mantis.config.models import ExperimentConfig

def create_run_manifest(config: ExperimentConfig, output_dir: Path) -> Path:
    config_dict = config.model_dump(exclude_none=True)
    config_str = json.dumps(config_dict, sort_keys=True)
    config_hash = hashlib.sha256(config_str.encode()).hexdigest()
    
    manifest = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "config_hash": config_hash,
        "seed": config.experiment.seed,
        "config": config_dict
    }
    
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = output_dir / "run_manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
        
    return manifest_path
