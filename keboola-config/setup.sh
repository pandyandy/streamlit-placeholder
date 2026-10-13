#!/bin/bash
set -Eeuo pipefail

echo "==> Installing dependencies..."
cd /app && uv sync

echo "==> Setup complete."
