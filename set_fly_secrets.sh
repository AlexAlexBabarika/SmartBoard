#!/usr/bin/env bash
# Set Fly.io secrets from a local .env-style file.

set -euo pipefail

ENV_FILE="${1:-.env}"

if ! command -v fly >/dev/null 2>&1; then
  echo "flyctl is not installed. Install from https://fly.io/docs/hands-on/install-flyctl/."
  exit 1
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "Env file not found: $ENV_FILE"
  exit 1
fi

# Read non-comment, non-empty lines and trim whitespace (portable across old macOS bash).
SECRETS=()
while IFS= read -r line; do
  # Trim leading/trailing whitespace
  clean_line="$(printf '%s' "$line" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
  # Skip empty or comment
  [[ -z "$clean_line" || "$clean_line" =~ ^# ]] && continue
  SECRETS+=("$clean_line")
done < "$ENV_FILE"

if [[ ${#SECRETS[@]} -eq 0 ]]; then
  echo "No secrets found in $ENV_FILE"
  exit 1
fi

echo "Setting ${#SECRETS[@]} secrets from $ENV_FILE ..."
fly secrets set "${SECRETS[@]}"

