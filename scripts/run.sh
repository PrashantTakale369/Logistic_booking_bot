#!/bin/bash
set -e

cd "$(dirname "$0")/.."

echo "=== Seeding database ==="
python scripts/seed_db.py

echo "=== Starting Streamlit app ==="
streamlit run ui/app.py --server.port 8501
