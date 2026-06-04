#!/usr/bin/env bash
# בדיקת עשן אחרי פריסה. שימוש:
#   API_URL=https://orgflow-api.onrender.com FRONTEND_URL=https://app.vercel.app ./scripts/smoke-cloud-deploy.sh

set -euo pipefail

API_URL="${API_URL:?Set API_URL (e.g. https://orgflow-api.onrender.com)}"
FRONTEND_URL="${FRONTEND_URL:-}"

API_URL="${API_URL%/}"

echo "==> Health: ${API_URL}/health"
curl -fsS "${API_URL}/health" | head -c 500
echo ""

echo "==> Readiness: ${API_URL}/readiness"
code=$(curl -sS -o /tmp/orgflow-readiness.json -w "%{http_code}" "${API_URL}/readiness" || true)
cat /tmp/orgflow-readiness.json
echo ""
echo "HTTP ${code} (200 = ready, 503 = עדיין עולה)"

if [[ -n "${FRONTEND_URL}" ]]; then
  FRONTEND_URL="${FRONTEND_URL%/}"
  echo "==> CORS preflight from frontend origin"
  curl -sS -o /dev/null -w "HTTP %{http_code}\n" \
    -X OPTIONS "${API_URL}/health" \
    -H "Origin: ${FRONTEND_URL}" \
    -H "Access-Control-Request-Method: GET" || true
fi

echo "==> Done"
