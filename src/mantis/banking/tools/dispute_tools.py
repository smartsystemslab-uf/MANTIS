import json

from mantis.banking.infra.repository import repo


def _transaction_exists(transaction_id: str) -> bool:
    """True if the transaction is in the local repository or, when the external
    banking backend is enabled, in the backend (some seeded transactions, e.g.
    TXN-1003, live only there)."""
    if repo.get_transaction(transaction_id):
        return True
    # Lazy import: mantis.banking.infra.api_client pulls in settings, which
    # this module's import must not force before .env is loaded.
    from mantis.banking.settings import settings
    if not settings.use_external_banking_api:
        return False
    from mantis.banking.infra.api_client import api_client, BankingApiError
    try:
        api_client.get_transaction(transaction_id)
        return True
    except BankingApiError:
        return False


def file_dispute(customer_id: str, transaction_id: str, reason: str) -> str:
    """File a new transaction dispute case for a customer and return the assigned dispute id.

    Requires a real customer id and a real transaction id; a request that
    cannot name them (for example a general question about how disputes work)
    is rejected rather than recorded as a case."""
    # A live baseline run of the FAQ scenario found this tool being called with
    # customer_id, transaction_id and reason all set to "unknown" and persisting
    # a real dispute row from what was only an informational question.
    if not repo.get_customer(customer_id):
        return json.dumps({"error": f"customer {customer_id} not found; a dispute requires a real customer id and transaction id"}, indent=2)
    if not _transaction_exists(transaction_id):
        return json.dumps({"error": f"transaction {transaction_id} not found; a dispute requires a real customer id and transaction id"}, indent=2)
    return json.dumps(repo.create_dispute(customer_id, transaction_id, reason), indent=2)


def get_dispute_status(dispute_id: str) -> str:
    """Look up the current status of a previously filed dispute case."""
    return json.dumps(repo.get_dispute(dispute_id) or {"error": f"dispute {dispute_id} not found"}, indent=2)
