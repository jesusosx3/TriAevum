#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "======================================================================"
echo "    Añadiendo TriAevum a Steam / Steam Deck como Non-Steam Game"
echo "======================================================================"

python3 "$SCRIPT_DIR/scripts/agregar_a_steam.py"
