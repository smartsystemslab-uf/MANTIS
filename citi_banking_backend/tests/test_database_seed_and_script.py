import importlib
import runpy
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app import database, seed
from app.database import Base
from app.models import Account, AuditLog, Customer, Policy, Rule, Transaction


def test_get_db_closes_its_session(monkeypatch):
    class FakeSession:
        closed = False

        def close(self):
            self.closed = True

    fake = FakeSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: fake)
    iterator = database.get_db()
    assert next(iterator) is fake
    iterator.close()
    assert fake.closed


def test_init_db_without_seed_and_idempotent_seed(tmp_path, monkeypatch):
    # Other tests seed a different temporary database during app startup. Reload
    # this module so this test starts with clean ORM row templates of its own.
    importlib.reload(seed)
    engine = create_engine(f"sqlite:///{tmp_path / 'seed.db'}")
    sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(seed, "engine", engine)
    monkeypatch.setattr(seed, "SessionLocal", sessions)

    seed.init_db(seed=False)
    with sessions() as db:
        assert db.query(Customer).count() == 0

    seed.init_db(seed=True)
    seed.init_db(seed=True)
    with sessions() as db:
        assert db.query(Customer).count() == len(seed.SEED_CUSTOMERS)
        assert db.query(Account).count() == len(seed.SEED_ACCOUNTS)
        assert db.query(Policy).count() == len(seed.SEED_POLICIES)
        assert db.query(Rule).count() == len(seed.SEED_RULES)
        assert db.query(Transaction).count() == 4
        assert db.query(AuditLog).filter_by(event_type="seed").count() == 1


def test_init_db_reset_drops_accumulated_rows_not_in_the_seed_set(tmp_path, monkeypatch):
    # Regression coverage for the real pollution bug this session hit live:
    # plain re-seeding is additive by primary key, so transactions created by
    # repeated test/demo runs (their own generated transaction_id, never one
    # of SEED_TRANSACTIONS') just keep accumulating across seed() calls.
    importlib.reload(seed)
    engine = create_engine(f"sqlite:///{tmp_path / 'seed.db'}")
    sessions = sessionmaker(bind=engine)
    monkeypatch.setattr(seed, "engine", engine)
    monkeypatch.setattr(seed, "SessionLocal", sessions)

    seed.init_db(seed=True)
    with sessions() as db:
        db.add(Transaction(
            transaction_id="TXN-LIVE-ACCUMULATED",
            from_account_id="CHK-002",
            to_account_id="EXT-998",
            amount=125.50,
            currency="USD",
            tx_type="transfer",
            status="completed",
            risk_score=0,
        ))
        db.commit()
    with sessions() as db:
        assert db.query(Transaction).count() == 5

    seed.init_db(seed=True)
    with sessions() as db:
        assert db.query(Transaction).count() == 5, "plain re-seed is additive and must not clear accumulated rows"

    # A real --reset always runs in a fresh process (fresh, never-persisted
    # SEED_CUSTOMERS/SEED_ACCOUNTS/... template instances); reload here to
    # match that rather than reusing objects this test already committed
    # once, which SQLAlchemy would treat as detached-persistent and silently
    # UPDATE (0 rows matched) instead of INSERT.
    importlib.reload(seed)
    monkeypatch.setattr(seed, "engine", engine)
    monkeypatch.setattr(seed, "SessionLocal", sessions)

    seed.init_db(seed=True, reset=True)
    with sessions() as db:
        assert db.query(Transaction).count() == 4
        assert db.query(Customer).count() == len(seed.SEED_CUSTOMERS)
        assert db.scalar(
            db.query(Transaction).filter_by(transaction_id="TXN-LIVE-ACCUMULATED").exists().select()
        ) is False


def test_init_db_command_invokes_seed(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(seed, "init_db", lambda seed=True, reset=False: calls.append((seed, reset)))
    monkeypatch.setattr("sys.argv", ["init_db.py"])
    script = Path(__file__).resolve().parents[1] / "scripts" / "init_db.py"
    runpy.run_path(str(script), run_name="__main__")
    assert calls == [(True, False)]
    assert "Database initialized" in capsys.readouterr().out


def test_init_db_command_reset_flag(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(seed, "init_db", lambda seed=True, reset=False: calls.append((seed, reset)))
    monkeypatch.setattr("sys.argv", ["init_db.py", "--reset"])
    script = Path(__file__).resolve().parents[1] / "scripts" / "init_db.py"
    runpy.run_path(str(script), run_name="__main__")
    assert calls == [(True, True)]
    assert "reset" in capsys.readouterr().out.lower()


def test_seed_module_main_entrypoint(capsys):
    runpy.run_module("app.seed", run_name="__main__")
    assert "Database initialized and seeded" in capsys.readouterr().out
