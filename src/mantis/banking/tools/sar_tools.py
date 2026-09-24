import json

from mantis.banking.infra.repository import repo


def get_exception_case(exception_id: str) -> str:
    """Look up an existing end-of-day reconciliation exception case by id."""
    return json.dumps(repo.get_exception(exception_id) or {"error": f"exception {exception_id} not found"}, indent=2)


def file_sar_report(exception_id: str, reason: str, filed_by: str = "") -> str:
    """File a formal Suspicious Activity Report escalating an existing reconciliation
    exception case, and return the assigned SAR id. The exception case must exist."""
    if not repo.get_exception(exception_id):
        return json.dumps({"error": f"exception {exception_id} not found; a SAR can only escalate an existing exception case"}, indent=2)
    return json.dumps(repo.create_sar(exception_id, reason, filed_by), indent=2)


def get_sar_status(sar_id: str) -> str:
    """Look up the current status of a previously filed SAR case."""
    return json.dumps(repo.get_sar(sar_id) or {"error": f"SAR {sar_id} not found"}, indent=2)
