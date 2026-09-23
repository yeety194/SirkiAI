#!/usr/bin/env bash
# Start a local Hermes brain via Ollama for SirkiAI.
set -euo pipefail

MODEL="${LOCAL_BRAIN_MODEL:-hermes3:3b}"

if ! command -v ollama >/dev/null 2>&1; then
  echo "Installing Ollama..."
  curl -fsSL https://ollama.com/install.sh | sh
fi

if ! curl -fsS "http://127.0.0.1:11434/api/tags" >/dev/null 2>&1; then
  echo "Starting Ollama server..."
  nohup ollama serve >/tmp/ollama-sirkiai.log 2>&1 &
  sleep 2
fi

echo "Pulling model: ${MODEL}"
ollama pull "${MODEL}"

echo "Warming model..."
ollama run "${MODEL}" "Reply with: SirkiAI local brain ready." >/tmp/ollama-warm.txt 2>&1 || true

echo
echo "Local brain is up:"
echo "  URL:   http://127.0.0.1:11434/v1"
echo "  Model: ${MODEL}"
echo "Set BRAIN_MODE=local in .env and launch SirkiAI."
