"""Workflow -> domain mapping.

Workflow ids are identical to scenario ids in this codebase (every shipped
config sets experiment.workflow == experiment.scenario), so the workflow
list is derived from mantis.banking.scenarios rather than kept as a second,
independently-maintained list that could drift out of sync.
"""

from mantis.banking.scenarios import SCENARIOS


def _domain_for(workflow_id: str) -> str:
    return "_".join(workflow_id.split("_")[:2])  # front_office / mid_office / back_office


WORKFLOW_DOMAINS: dict[str, str] = {
    workflow_id: _domain_for(workflow_id) for workflow_id in SCENARIOS
}
