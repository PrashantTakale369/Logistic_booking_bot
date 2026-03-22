"""Entry point to seed the database with rate card data."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from db.seed_rate_cards import seed

if __name__ == "__main__":
    seed()
