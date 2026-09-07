from pathlib import Path
from mantis.cli.campaign import CampaignManager


def test_run_name_for_reads_the_real_experiment_name(tmp_path: Path):
    # A baseline-style config where the filename does not match
    # experiment.name -- e.g. configs/baselines/front_office_baseline.yaml
    # actually names itself "front_office_monitoring". Aggregation must
    # follow the real name, since that's the run_artifacts/<name>/
    # directory mantis --run actually writes to.
    config_file = tmp_path / "front_office_baseline.yaml"
    config_file.write_text(
        "experiment:\n"
        "  name: front_office_monitoring\n"
        "  seed: 42\n"
        "  domain: front_office\n"
        "  workflow: front_office_monitoring\n"
        "  scenario: front_office_monitoring\n"
    )

    assert CampaignManager._run_name_for(config_file) == "front_office_monitoring"


def test_run_name_for_falls_back_to_filename_stem_on_malformed_config(tmp_path: Path):
    config_file = tmp_path / "broken.yaml"
    config_file.write_text("not: {valid: [experiment config")

    assert CampaignManager._run_name_for(config_file) == "broken"
