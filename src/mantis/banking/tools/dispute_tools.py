import json

from mantis.banking.infra.repository import repo


def file_dispute(customer_id: str, transaction_id: str, reason: str) -> str:
    """File a new transaction dispute case for a customer and return the assigned dispute id."""
    return json.dumps(repo.create_dispute(customer_id, transaction_id, reason), indent=2)


def get_dispute_status(dispute_id: str) -> str:
    """Look up the current status of a previously filed dispute case."""
    return json.dumps(repo.get_dispute(dispute_id) or {"error": f"dispute {dispute_id} not found"}, indent=2)
