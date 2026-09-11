#!/usr/bin/env bash

set -euo pipefail

PROJECT_ROOT="$(
    cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd
)"

cd "$PROJECT_ROOT"

if [[ ! -d ".venv" ]]; then
    echo "Criando ambiente virtual..."
    python -m venv .venv
fi

source .venv/bin/activate

REQUIREMENTS_HASH="$(
    sha256sum requirements.txt | awk '{print $1}'
)"

REQUIREMENTS_HASH_FILE=".venv/.requirements.sha256"

INSTALLED_HASH=""

if [[ -f "$REQUIREMENTS_HASH_FILE" ]]; then
    INSTALLED_HASH="$(
        cat "$REQUIREMENTS_HASH_FILE"
    )"
fi

if [[ "$REQUIREMENTS_HASH" != "$INSTALLED_HASH" ]]; then
    echo "Dependências novas ou alteradas detectadas."
    echo "Atualizando ambiente virtual..."

    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

    printf '%s' "$REQUIREMENTS_HASH" \
        > "$REQUIREMENTS_HASH_FILE"

    rm -f ".venv/.dependencies-installed"
fi

HOST="${HOST:-0.0.0.0}"
PORT="${PORT:-8000}"

echo
echo "Fácil Digital+ — Montador de Apostilas"
echo "Servidor: http://${HOST}:${PORT}"
echo

exec uvicorn app.main:app \
    --host "$HOST" \
    --port "$PORT" \
    --reload