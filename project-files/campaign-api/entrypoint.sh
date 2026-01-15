#!/bin/bash
set -e

echo "=============================================="
echo "  USB Drop Campaign Manager - Starting"
echo "=============================================="

# Run startup checks
echo ""
echo "Running pre-flight checks..."
python startup_check.py

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "❌ Pre-flight checks failed. Exiting."
    exit 1
fi

echo ""
echo "Starting API server..."
echo ""

# Start uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
