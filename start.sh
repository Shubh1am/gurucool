#!/usr/bin/env bash
set -euo pipefail

echo "Starting container for SERVICE=${SERVICE}"

if [ "${SERVICE:-backend}" = "backend" ]; then
  exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload
else
  # default to UI
  exec streamlit run ui.py --server.port 8501 --server.address 0.0.0.0
fi
