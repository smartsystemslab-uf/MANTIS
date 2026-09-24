"""Consistency tests over every shipped experiment config.

Nothing here runs an experiment (no LLM, no backend). It guards the
failure class this repo has hit repeatedly: a config that *looks* fine but
silently does the wrong thing -- an attack target the validator rejects
though `--run` accepts it, a payload_file that does not exist (so the
plugin quietly injects its generic fallback string), an expected_tools
typo that turns a ground-truth check into a permanent, meaningless score
of 0.0, or two configs sharing an experiment name and overwriting each
other's run_artifacts.
"""
from pathlib import Path

import pytest
import yaml

from mantis.banking.tool_semantics import TERMINAL_TOOL_OUTCOMES
from mantis.cli.main import validate_config
from mantis.config.models import ExperimentConfig
from mantis.core.registry import plugin_registry, workflow_registry
from mantis.runtime.adapter import NativeBankingAdapter

REPO_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIRS = ["attacks", "baselines", "extensions", "scenarios", "extended"]


def _shipped_configs():
    paths = []
    for d in CONFIG_DIRS:
        paths.extend(sorted((REPO_ROOT / "configs" / d).rglob("*.yaml")))
    return paths


SHIPPED = _shipped_configs()
IDS = [str(p.relative_to(REPO_ROOT)) for p in SHIPPED]
INVENTORY = NativeBankingAdapter().inventory()
KNOWN_TOOLS = set(INVENTORY.tools)


def _load(path: Path) -> ExperimentConfig:
    return ExperimentConfig(**yaml.safe_load(path.read_text()))


def test_the_extended_library_is_present():
    """Paper 1's original configs plus the extended baselines and attacks."""
    extended = [p for p in SHIPPED if "extended" in p.parts]
    assert len([p for p in extended if "baselines" in p.parts]) >= 19
    assert len([p for p in extended if "attacks" in p.parts]) >= 26
    assert len(SHIPPED) >= 80


@pytest.mark.parametrize("path", SHIPPED, ids=IDS)
def test_every_shipped_config_validates(path):
    assert validate_config(str(path)), f"{path} is a shipped config but `mantis --validate` rejects it"


@pytest.mark.parametrize("path", sorted((REPO_ROOT / "configs" / "invalid").glob("*.yaml")), ids=lambda p: p.name)
def test_every_invalid_config_is_rejected(path):
    assert not validate_config(str(path))


@pytest.mark.parametrize("path", SHIPPED, ids=IDS)
def test_config_domain_matches_its_workflow_domain(path):
    cfg = _load(path)
    assert cfg.experiment.workflow == cfg.experiment.scenario, "every shipped config uses one id for both"
    assert workflow_registry.get(cfg.experiment.workflow) == cfg.experiment.domain


@pytest.mark.parametrize("path", SHIPPED, ids=IDS)
def test_payload_files_exist_and_are_non_empty(path, monkeypatch):
    cfg = _load(path)
    if not cfg.attack or "payload_file" not in cfg.attack.parameters:
        pytest.skip("no payload_file")
    payload = REPO_ROOT / cfg.attack.parameters["payload_file"]
    assert payload.is_file(), f"{payload} missing: prompt_injection would silently inject its built-in fallback"
    assert payload.read_text().strip()


@pytest.mark.parametrize("path", SHIPPED, ids=IDS)
def test_ground_truth_names_only_real_tools_and_reachable_states(path):
    cfg = _load(path)
    ev = cfg.evaluation
    if not ev:
        pytest.skip("no evaluation block")
    for tool in list(ev.expected_tools or []) + list(ev.forbidden_tools or []):
        assert tool in KNOWN_TOOLS, f"{tool!r} is not a real tool; this check could never pass/fail meaningfully"
    if ev.expected_terminal_state:
        assert ev.expected_terminal_state in set(TERMINAL_TOOL_OUTCOMES.values()) | {"completed"}


@pytest.mark.parametrize("path", SHIPPED, ids=IDS)
def test_plugins_construct_with_their_configured_parameters(path, monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    cfg = _load(path)
    if cfg.attack and cfg.attack.plugin:
        plugin_registry.get(cfg.attack.plugin)(**cfg.attack.parameters)
    for policy in cfg.policies or []:
        plugin_registry.get(policy.plugin)(**policy.parameters)


@pytest.mark.parametrize("path", SHIPPED, ids=IDS)
def test_attack_control_point_is_one_the_plugin_supports(path, monkeypatch):
    monkeypatch.chdir(REPO_ROOT)
    cfg = _load(path)
    if not (cfg.attack and cfg.attack.plugin):
        pytest.skip("no attack")
    plugin = plugin_registry.get(cfg.attack.plugin)(**cfg.attack.parameters)
    assert cfg.attack.control_point in plugin.supported_stages, (
        f"{cfg.attack.plugin} only acts at {sorted(plugin.supported_stages)}, "
        f"but this config registers it at {cfg.attack.control_point!r}: it would never fire"
    )


def test_experiment_names_are_unique_within_each_config_group():
    """Two configs sharing experiment.name write to the same
    run_artifacts/<name>/ directory and clobber each other's evidence."""
    for group in ("attacks", "extensions", "extended"):
        names = {}
        for path in sorted((REPO_ROOT / "configs" / group).rglob("*.yaml")):
            name = _load(path).experiment.name
            assert name not in names, f"{path} and {names[name]} both write run_artifacts/{name}/"
            names[name] = path


def test_experiment_names_do_not_collide_across_groups():
    seen = {}
    for path in SHIPPED:
        rel = path.relative_to(REPO_ROOT / "configs")
        if rel.parts[0] in ("baselines", "scenarios"):
            continue  # baselines deliberately share names with the workflow they exercise
        name = _load(path).experiment.name
        assert name not in seen, f"{rel} and {seen[name]} both write run_artifacts/{name}/"
        seen[name] = rel
