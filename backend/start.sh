#!/bin/bash
echo "Starting PPF Backend..."
echo "Environment: $ENVIRONMENT"
echo "Database: $DATABASE_URL"
uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 2
