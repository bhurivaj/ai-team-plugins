#!/usr/bin/env bash
# Fails if anything credential-shaped or company data is tracked. Run from the repo root.
set -euo pipefail
fail=0
tracked=$(git ls-files)
if echo "$tracked" | grep -E '(^|/)(\.secret/|company\.json$|client\.json$|.*\.local\.json$)'; then
  echo "ERROR: company data or secrets are tracked"; fail=1
fi
pattern='AccountKey=[A-Za-z0-9+/=]{20,}|[?&]sig=[A-Za-z0-9%+/=]{20,}|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|"PASS"[[:space:]]*:[[:space:]]*"[^"]+"|xox[baprs]-[A-Za-z0-9-]{10,}'
if git grep -nIE "$pattern" -- . ':!tests/secret_scan.sh'; then
  echo "ERROR: credential-shaped string found"; fail=1
fi
exit $fail
