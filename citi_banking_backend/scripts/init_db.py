import argparse
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR))

from app.seed import init_db

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--reset",
        action="store_true",
        help=(
            "Drop and recreate all tables first, for a true clean slate. "
            "Plain (re-)seeding is additive by primary key and will not clear "
            "transactions accumulated from live test/demo runs."
        ),
    )
    args = parser.parse_args()
    init_db(seed=True, reset=args.reset)
    print(
        "Database re-initialized (reset) in ./data/citi_banking.db"
        if args.reset
        else "Database initialized in ./data/citi_banking.db"
    )
