#!/usr/bin/env bash

# Append a timestamped entry to docs/FISHCLAIM_SESSION_LOG.md.
# Usage: bash scripts/append_session_log.sh "summary of work"

set -euo pipefail

SUMMARY="${1:-}"
if [ -z "$SUMMARY" ]; then
  read -rp "Summary: " SUMMARY
fi

LOG_FILE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/docs/FISHCLAIM_SESSION_LOG.md"
STAMP=$(date -Iseconds)
AUTHOR=${USER:-Conor}

{
  echo ""
  echo "## ${STAMP} (${AUTHOR})"
  echo "- ${SUMMARY}"
} >> "${LOG_FILE}"

echo "Appended entry to ${LOG_FILE}"
