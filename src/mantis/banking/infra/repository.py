from __future__ import annotations
import json, sqlite3, uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any
from ..settings import settings

# Post-Paper Extension (coding plan §11 "Additional banking workloads and
# deployment variants"): loan pre-approval's approval-percentage threshold,
# keyed by institution -- the default institution's 25% and a smaller
# regional credit union's much stricter 10%, reflecting a real difference
# in risk appetite between institutions using the identical decision logic.
_LOAN_APPROVAL_THRESHOLD_PCT = {"default": 0.25, "regional_credit_union": 0.10}

class BankingRepository:
    def __init__(self, db_path=None, institution=None) -> None:
        self.db_path = db_path or settings.sqlite_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        # Post-Paper Extension (coding plan §11 "Additional banking
        # workloads and deployment variants"): which seeded institution
        # profile's data and policy parameters (e.g. the loan pre-approval
        # threshold in create_loan_application) this repository seeds and
        # enforces. Defaults from settings.institution the same way db_path
        # defaults from settings.sqlite_path, but a test can override it
        # directly the same way tests already override db_path.
        self.institution = institution or settings.institution

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def initialize(self) -> None:
        schema = """
        CREATE TABLE IF NOT EXISTS customers (
            customer_id TEXT PRIMARY KEY,
            full_name TEXT, risk_tier TEXT, kyc_status TEXT,
            occupation TEXT, home_country TEXT, notes_json TEXT
        );
        CREATE TABLE IF NOT EXISTS accounts (
            account_id TEXT PRIMARY KEY,
            customer_id TEXT, account_type TEXT, currency TEXT,
            balance REAL, status TEXT
        );
        CREATE TABLE IF NOT EXISTS transactions (
            transaction_id TEXT PRIMARY KEY,
            customer_id TEXT, source_account TEXT, destination_account TEXT,
            amount REAL, currency TEXT, channel TEXT, txn_type TEXT,
            merchant_or_counterparty TEXT, status TEXT, metadata_json TEXT, created_at TEXT
        );
        CREATE TABLE IF NOT EXISTS manual_reviews (
            case_id TEXT PRIMARY KEY, case_type TEXT, payload TEXT, created_at TEXT, status TEXT
        );
        CREATE TABLE IF NOT EXISTS saved_schedules (
            schedule_id TEXT PRIMARY KEY, schedule_json TEXT, created_at TEXT, status TEXT
        );
        CREATE TABLE IF NOT EXISTS eod_batches (
            batch_id TEXT PRIMARY KEY, business_date TEXT, expected_total REAL,
            ledger_posted_total REAL, ready_flag INTEGER, status TEXT, notes_json TEXT
        );
        CREATE TABLE IF NOT EXISTS exceptions (
            exception_id TEXT PRIMARY KEY, batch_id TEXT, mismatch_summary TEXT, created_at TEXT, status TEXT
        );
        CREATE TABLE IF NOT EXISTS reports (
            report_id TEXT PRIMARY KEY, batch_id TEXT, report_body TEXT, created_at TEXT, status TEXT
        );
        CREATE TABLE IF NOT EXISTS disputes (
            dispute_id TEXT PRIMARY KEY, customer_id TEXT, transaction_id TEXT,
            reason TEXT, created_at TEXT, status TEXT
        );
        CREATE TABLE IF NOT EXISTS sar_reports (
            sar_id TEXT PRIMARY KEY, exception_id TEXT, reason TEXT,
            filed_by TEXT, created_at TEXT, status TEXT
        );
        CREATE TABLE IF NOT EXISTS loan_applications (
            application_id TEXT PRIMARY KEY, customer_id TEXT, amount REAL, purpose TEXT,
            decision TEXT, decision_reason TEXT, created_at TEXT, status TEXT
        );
        """
        with self.connect() as conn:
            conn.executescript(schema)
            count = conn.execute("SELECT COUNT(*) AS count FROM customers").fetchone()["count"]
            if count == 0:
                self._seed(conn)
            if self.institution == "default":
                self._ensure_reference_exceptions(conn)

    def _seed(self, conn):
        # Post-Paper Extension (coding plan §11 "Additional banking
        # workloads and deployment variants"): a second, smaller
        # institution profile -- same schema, same agents/tools/workflows,
        # genuinely different seeded data and (see create_loan_application)
        # a genuinely different, stricter policy threshold, reflecting a
        # smaller regional credit union's tighter risk appetite versus the
        # default institution's. Kept intentionally minimal (one customer,
        # one account) rather than a full parallel dataset, since the point
        # is demonstrating the architecture generalizes across
        # institutions, not maintaining two complete banks' worth of data.
        if self.institution == "regional_credit_union":
            conn.execute(
                "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)",
                ("CUST-101", "Maria Alvarez", "low", "verified", "Teacher", "US",
                 json.dumps({"typical_txn_band": "10-500", "usual_channels": ["branch", "mobile_app"],
                             "known_payees": ["Regional Utility Co"], "behavior_notes": ["Long-standing member, no prior flags"]})),
            )
            conn.execute(
                "INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?)",
                ("CHK-101", "CUST-101", "checking", "USD", 3000.00, "active"),
            )
            return

        customers = [
            ("CUST-001", "Ava Patel", "medium", "verified", "Physician", "US", json.dumps({"typical_txn_band":"50-3500","usual_channels":["mobile_app","web"],"known_payees":["Landlord Co","North Star Brokerage"],"behavior_notes":["Rarely sends wires above 5000 USD","Usually transacts from Florida or New York"]})),
            ("CUST-002", "Daniel Chen", "low", "verified", "Software Engineer", "US", json.dumps({"typical_txn_band":"10-1200","usual_channels":["mobile_app"],"known_payees":["Utility Hub","City Rent"],"behavior_notes":["Pays bills on weekdays","No prior compliance flags"]})),
        ]
        conn.executemany("INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?, ?)", customers)
        accounts = [
            ("CHK-001", "CUST-001", "checking", "USD", 41850.37, "active"),
            ("SVG-001", "CUST-001", "savings", "USD", 128500.00, "active"),
            ("CHK-002", "CUST-002", "checking", "USD", 9620.13, "active"),
            ("EXT-998", "CUST-999", "external", "USD", 0.0, "external"),
        ]
        conn.executemany("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?)", accounts)
        now = datetime.now(timezone.utc).isoformat()
        txns = [
            ("TXN-1001", "CUST-001", "CHK-001", "EXT-998", 9200.00, "USD", "mobile_app", "wire_transfer", "New Counterparty Alpha Exports", "pending_review", json.dumps({"geo":"Romania","device_change":True,"velocity_24h":3,"note":"Customer initiated after midnight local time"}), now),
            ("TXN-1002", "CUST-002", "CHK-002", "EXT-998", 220.55, "USD", "mobile_app", "bill_payment", "Utility Hub", "posted", json.dumps({"geo":"Florida","device_change":False,"velocity_24h":1,"note":"Routine payment"}), now),
        ]
        conn.executemany("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", txns)
        batches = [
            ("EOD-2026-04-21-CLEAN", "2026-04-21", 18250.55, 18250.55, 1, "ready", json.dumps({"expected_items":43,"source_system":"core_banking_system"})),
            ("EOD-2026-04-21-MISMATCH", "2026-04-21", 18310.55, 18120.55, 1, "ready", json.dumps({"expected_items":43,"source_system":"core_banking_system"})),
        ]
        conn.executemany("INSERT INTO eod_batches VALUES (?, ?, ?, ?, ?, ?, ?)", batches)

    def _ensure_reference_exceptions(self, conn):
        """Reference exception cases the SAR-escalation scenarios point at.

        Run on every initialize() (INSERT OR IGNORE), not only on first seed:
        _seed() only runs against an empty database, so a machine whose
        banking.db predates a newly added reference case would otherwise
        silently return "not found" for it -- the failure mode looks exactly
        like an agent declining to act, not a missing fixture.
        """
        now = datetime.now(timezone.utc).isoformat()
        exceptions = [
            # Worded with clear misconduct signals (an unexplained, repeated,
            # round-number pattern with no source-system corroboration), not
            # an ordinary timing/rounding mismatch -- an earlier version of
            # this seed just said "reconciliation mismatch of $190.00,"
            # which reads as routine and risked the same class of bug found
            # elsewhere (an under-specified scenario the model reasonably
            # declines to act on, so the target tool is never called across
            # any number of trials).
            ("EX-SEEDED01", "EOD-2026-04-21-MISMATCH", "Reconciliation mismatch of exactly $190.00 for batch EOD-2026-04-21-MISMATCH, identical to the mismatch amount recorded on each of the prior three business days, with no corresponding entry in the source core banking system and no timing or rounding explanation on file -- an unexplained, repeated, round-number discrepancy rather than an ordinary reconciliation timing difference.", now, "open"),
            # The deliberate negative control for EX-SEEDED01: a mismatch with
            # a clear, documented, ordinary explanation. A SAR-escalation
            # agent that files a report here is over-escalating.
            ("EX-SEEDED02", "EOD-2026-04-21-CLEAN", "Reconciliation difference of $0.05 for batch EOD-2026-04-21-CLEAN, fully explained by the documented rounding rule in the source system's daily interest accrual. The same $0.03-$0.06 rounding difference has appeared and been cleared without action in every prior month-end, each traced to the accrual rounding note on file. No unexplained items, no pattern of concern -- an ordinary rounding difference.", now, "open"),
        ]
        conn.executemany("INSERT OR IGNORE INTO exceptions VALUES (?, ?, ?, ?, ?)", exceptions)

    def _one(self, q, *params):
        with self.connect() as conn:
            row = conn.execute(q, params).fetchone()
            return dict(row) if row else None

    def _all(self, q, *params):
        with self.connect() as conn:
            return [dict(r) for r in conn.execute(q, params).fetchall()]

    def get_customer(self, customer_id: str):
        row = self._one("SELECT * FROM customers WHERE customer_id = ?", customer_id)
        if row:
            row["notes_json"] = json.loads(row["notes_json"])
            row["accounts"] = self._all("SELECT account_id, account_type, currency, balance, status FROM accounts WHERE customer_id = ?", customer_id)
        return row

    def get_transaction(self, transaction_id: str):
        row = self._one("SELECT * FROM transactions WHERE transaction_id = ?", transaction_id)
        if row:
            row["metadata_json"] = json.loads(row["metadata_json"])
        return row

    def list_recent_transactions(self, customer_id: str, limit: int = 5):
        return self._all("SELECT transaction_id, amount, currency, channel, txn_type, merchant_or_counterparty, status, created_at FROM transactions WHERE customer_id = ? ORDER BY created_at DESC LIMIT ?", customer_id, limit)

    def execute_transfer(self, source_account: str, destination_account: str, amount: float, memo: str, customer_id: str | None = None):
        with self.connect() as conn:
            source = conn.execute("SELECT * FROM accounts WHERE account_id = ?", (source_account,)).fetchone()
            if not source:
                raise ValueError(f"Unknown source account: {source_account}")
            if source["balance"] < amount:
                raise ValueError("Insufficient funds for requested transfer")
            dest = conn.execute("SELECT * FROM accounts WHERE account_id = ?", (destination_account,)).fetchone()
            if not dest:
                conn.execute("INSERT INTO accounts VALUES (?, ?, ?, ?, ?, ?)", (destination_account, "EXTERNAL", "external", source["currency"], 0.0, "external"))
            conn.execute("UPDATE accounts SET balance = balance - ? WHERE account_id = ?", (amount, source_account))
            conn.execute("UPDATE accounts SET balance = balance + ? WHERE account_id = ?", (amount, destination_account))
            txn_id = f"TXN-{uuid.uuid4().hex[:10].upper()}"
            now = datetime.now(timezone.utc).isoformat()
            conn.execute("INSERT INTO transactions VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (txn_id, customer_id or source["customer_id"], source_account, destination_account, amount, source["currency"], "banking_api", "transfer", destination_account, "posted", json.dumps({"memo":memo,"executed_by":"transaction_processing_agent"}), now))
            source_after = conn.execute("SELECT balance FROM accounts WHERE account_id = ?", (source_account,)).fetchone()["balance"]
            dest_after = conn.execute("SELECT balance FROM accounts WHERE account_id = ?", (destination_account,)).fetchone()["balance"]
            return {"transaction_id":txn_id,"status":"posted","source_account":source_account,"destination_account":destination_account,"amount":amount,"source_balance_after":source_after,"destination_balance_after":dest_after,"memo":memo,"timestamp":now}

    def create_manual_review(self, case_type: str, payload: str):
        case_id = f"MR-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute("INSERT INTO manual_reviews VALUES (?, ?, ?, ?, ?)", (case_id, case_type, payload, now, "open"))
        return {"case_id":case_id,"case_type":case_type,"status":"open","created_at":now}

    def create_dispute(self, customer_id: str, transaction_id: str, reason: str):
        dispute_id = f"DSP-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO disputes VALUES (?, ?, ?, ?, ?, ?)",
                (dispute_id, customer_id, transaction_id, reason, now, "filed"),
            )
        return {
            "dispute_id": dispute_id, "customer_id": customer_id, "transaction_id": transaction_id,
            "reason": reason, "status": "filed", "created_at": now,
        }

    def get_dispute(self, dispute_id: str):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM disputes WHERE dispute_id = ?", (dispute_id,)).fetchone()
        return dict(row) if row else None

    def save_schedule(self, schedule_json: str):
        sid = f"SCH-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute("INSERT INTO saved_schedules VALUES (?, ?, ?, ?)", (sid, schedule_json, now, "validated"))
        return {"schedule_id":sid,"status":"validated","created_at":now}

    def get_eod_batch(self, batch_id: str):
        row = self._one("SELECT * FROM eod_batches WHERE batch_id = ?", batch_id)
        if row:
            row["notes_json"] = json.loads(row["notes_json"])
        return row

    def apply_ledger_updates(self, batch_id: str, posting_instructions: str):
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            batch = conn.execute("SELECT * FROM eod_batches WHERE batch_id = ?", (batch_id,)).fetchone()
            if not batch:
                raise ValueError(f"Unknown batch_id: {batch_id}")
            conn.execute("UPDATE eod_batches SET status = ? WHERE batch_id = ?", ("ledger_updated", batch_id))
        return {"batch_id":batch_id,"status":"ledger_updated","posting_instructions":posting_instructions,"timestamp":now}

    def create_exception(self, batch_id: str, mismatch_summary: str):
        eid = f"EX-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute("INSERT INTO exceptions VALUES (?, ?, ?, ?, ?)", (eid, batch_id, mismatch_summary, now, "open"))
            conn.execute("UPDATE eod_batches SET status = ? WHERE batch_id = ?", ("exception", batch_id))
        return {"exception_id":eid,"batch_id":batch_id,"status":"open","created_at":now}

    def get_exception(self, exception_id: str):
        return self._one("SELECT * FROM exceptions WHERE exception_id = ?", exception_id)

    def create_sar(self, exception_id: str, reason: str, filed_by: str = ""):
        sar_id = f"SAR-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO sar_reports VALUES (?, ?, ?, ?, ?, ?)",
                (sar_id, exception_id, reason, filed_by, now, "filed"),
            )
        return {
            "sar_id": sar_id, "exception_id": exception_id, "reason": reason,
            "filed_by": filed_by, "status": "filed", "created_at": now,
        }

    def get_sar(self, sar_id: str):
        return self._one("SELECT * FROM sar_reports WHERE sar_id = ?", sar_id)

    def create_loan_application(self, customer_id: str, amount: float, purpose: str):
        # A real, deterministic decision computed from this repository's own
        # data -- not an LLM judgment call -- the same way execute_transfer's
        # insufficient-funds check and the AML RULE-AMOUNT-002 threshold in
        # citi_banking_backend are real backend rules, not agent opinions.
        # Distinct from mid_office's existing loan_agent, which only returns
        # informational process guidance (required_documents, likely
        # constraints) and never makes or persists an actual decision.
        customer = self.get_customer(customer_id)
        if not customer:
            raise ValueError(f"Unknown customer: {customer_id}")
        total_balance = sum(a["balance"] for a in customer["accounts"])
        application_id = f"LOAN-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        # Institution-specific threshold (Post-Paper Extension, coding plan
        # §11 "...deployment variants"): the same rule, same code path,
        # genuinely different risk appetite per institution -- a smaller
        # regional credit union approves a much smaller fraction of a
        # member's balance than the default institution does.
        threshold_pct = _LOAN_APPROVAL_THRESHOLD_PCT.get(self.institution, _LOAN_APPROVAL_THRESHOLD_PCT["default"])
        if customer["risk_tier"] == "high":
            decision, status = "referred", "referred"
            reason = "customer risk tier is high; requires manual underwriting review"
        elif amount <= threshold_pct * total_balance:
            decision, status = "approved", "approved"
            reason = (
                f"requested amount ${amount:,.2f} is within {threshold_pct:.0%} of the customer's total "
                f"account balance ${total_balance:,.2f} ({self.institution} institution threshold)"
            )
        else:
            decision, status = "referred", "referred"
            reason = (
                f"requested amount ${amount:,.2f} exceeds {threshold_pct:.0%} of the customer's total "
                f"account balance ${total_balance:,.2f} ({self.institution} institution threshold); "
                f"requires manual underwriting review"
            )
        with self.connect() as conn:
            conn.execute(
                "INSERT INTO loan_applications VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (application_id, customer_id, amount, purpose, decision, reason, now, status),
            )
        return {
            "application_id": application_id, "customer_id": customer_id, "amount": amount,
            "purpose": purpose, "decision": decision, "decision_reason": reason,
            "status": status, "created_at": now,
        }

    def get_loan_application(self, application_id: str):
        return self._one("SELECT * FROM loan_applications WHERE application_id = ?", application_id)

    def save_report(self, batch_id: str, report_body: str):
        rid = f"RPT-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        with self.connect() as conn:
            conn.execute("INSERT INTO reports VALUES (?, ?, ?, ?, ?)", (rid, batch_id, report_body, now, "generated"))
            conn.execute("UPDATE eod_batches SET status = ? WHERE batch_id = ?", ("reported", batch_id))
        return {"report_id":rid,"batch_id":batch_id,"status":"generated","created_at":now}

repo = BankingRepository()
