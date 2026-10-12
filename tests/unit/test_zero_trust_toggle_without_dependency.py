"""The zero_trust: toggle's error path when the optional dependency genuinely
isn't installed -- this file deliberately does NOT importorskip zt_backplane,
so it runs (and matters) precisely in the stock environment where the other
zero_trust tests are skipped."""
from pathlib import Path

from mantis.cli.main import validate_config
from mantis.core.registry import plugin_registry

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_enabled_toggle_gives_an_actionable_error_when_the_plugin_is_unregistered(tmp_path):
    if "zero_trust_enforcement" in plugin_registry.all():
        import pytest
        pytest.skip("zero_trust optional dependency is installed in this environment")

    cfg = tmp_path / "zt_toggle.yaml"
    cfg.write_text(
        "experiment:\n  name: zt_toggle_missing_dep_test\n  domain: front_office\n"
        "  workflow: front_office_monitoring\n  scenario: front_office_monitoring\n"
        "zero_trust:\n  enabled: true\n"
    )
    assert validate_config(str(cfg)) is False
