import json

from mantis.banking.infra.repository import repo


def submit_loan_application(customer_id: str, amount: float, purpose: str) -> str:
    """Submit a new loan/credit-line application for a customer and receive a
    real, computed pre-approval decision based on the customer's account
    balances and risk tier (not an informal opinion)."""
    try:
        result = repo.create_loan_application(customer_id, amount, purpose)
    except ValueError as e:
        return json.dumps({"error": str(e)})
    return json.dumps(result, indent=2)


def get_loan_application_status(application_id: str) -> str:
    """Look up the current status of a previously submitted loan application."""
    return json.dumps(
        repo.get_loan_application(application_id) or {"error": f"application {application_id} not found"},
        indent=2,
    )
