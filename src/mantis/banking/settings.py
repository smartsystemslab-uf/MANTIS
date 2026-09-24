from __future__ import annotations
import os
from dataclasses import dataclass
from pathlib import Path

_PACKAGE_DIR = Path(__file__).resolve().parent

@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("BANKING_ADK_APP_NAME", "citi_banking_adk")
    user_id: str = os.getenv("BANKING_ADK_USER_ID", "demo_user")
    session_id: str = os.getenv("BANKING_ADK_SESSION_ID", "demo_session")
    api_key: str = os.getenv("UF_NAVIGATOR_API_KEY", "")
    base_url: str = os.getenv("UF_NAVIGATOR_BASE_URL", "https://api.ai.it.ufl.edu")
    model_name: str = os.getenv("UF_NAVIGATOR_MODEL", "gpt-oss-20b")
    package_dir: Path = _PACKAGE_DIR
    data_dir: Path = Path(os.getenv("BANKING_ADK_DATA_DIR", str(_PACKAGE_DIR / "data"))).expanduser()
    runtime_dir: Path = Path(os.getenv("BANKING_ADK_RUNTIME_DIR", str(_PACKAGE_DIR / ".runtime"))).expanduser()
    banking_backend_base_url: str = os.getenv("BANKING_BACKEND_BASE_URL", "http://127.0.0.1:8000")
    use_external_banking_api: bool = os.getenv("BANKING_USE_EXTERNAL_API", "true").lower() in {"1", "true", "yes", "on"}
    # Post-Paper Extension (coding plan §11 "Additional banking workloads and
    # deployment variants"): which seeded institution profile this process
    # runs against -- set from experiment.institution by cli/main.py's
    # run_experiment(), via os.environ, *before* this module (or
    # mantis.banking.infra.repository, which imports it) is first imported.
    # Read once at process-start like UF_NAVIGATOR_API_KEY above, for the
    # same reason: mantis.core.registry's own plugin imports must never
    # trigger this module's import before that env var is set, or the
    # institution silently reverts to "default" for the whole process.
    institution: str = os.getenv("MANTIS_INSTITUTION", "default")

    @property
    def api_base(self) -> str:
        normalized = self.base_url.rstrip("/")
        return normalized if normalized.endswith("/v1") else f"{normalized}/v1"

    @property
    def sqlite_path(self) -> Path:
        # The default institution keeps the original, unsuffixed filename
        # so every existing run/test/seeded-data assumption is unaffected;
        # any other institution gets its own isolated database file, same
        # schema, different seed data.
        if self.institution == "default":
            return self.runtime_dir / "banking.db"
        return self.runtime_dir / f"banking_{self.institution}.db"

settings = Settings()
