#!/usr/bin/env bash
# Baseline nhanh: xác nhận harness hoạt động và lấy P95 phía client.
# Không phải capacity test; dùng RPS thấp để không ảnh hưởng production.
#   RPS=5 DURATION=30s bash experiments/runner/smoke_baseline.sh
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1

BASE_URL="${BASE_URL:-http://127.0.0.1:8083}"
RPS="${RPS:-5}"
DURATION="${DURATION:-30s}"
STAMP="$(date +%Y%m%dT%H%M%S)"
OUT_DIR="experiments/results/raw"
OUT="$OUT_DIR/smoke-$STAMP"
mkdir -p "$OUT_DIR"

echo "== Kiem tra backend =="
if ! curl -fsS --max-time 10 "$BASE_URL/health"; then
  echo
  echo "Backend khong phan hoi tai $BASE_URL/health"
  exit 1
fi
echo

echo "== Lay mau docker stats moi 2s =="
(
  while true; do
    printf '%s,' "$(date -Is)"
    docker stats --no-stream --format '{{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.MemPerc}}' | tr '\n' ';'
    echo
    sleep 2
  done
) > "${OUT}.stats.csv" 2>&1 &
SAMPLER=$!

echo "== k6: ${RPS} rps trong ${DURATION} =="
docker run --rm --network host -i \
  -e BASE_URL="$BASE_URL" -e RPS="$RPS" -e DURATION="$DURATION" \
  -v "$(pwd)/${OUT_DIR}:/out" \
  grafana/k6 run - < experiments/load/smoke.js 2>&1 | tee "${OUT}.k6.log"
K6_EXIT=${PIPESTATUS[0]}

kill "$SAMPLER" 2>/dev/null
wait "$SAMPLER" 2>/dev/null

echo
echo "== Tom tat =="
if [ -f "${OUT_DIR}/summary.json" ]; then
  mv "${OUT_DIR}/summary.json" "${OUT}.summary.json"
fi
python3 - "${OUT}.summary.json" <<'PY' 2>/dev/null || echo "(khong doc duoc summary.json)"
import json, sys
d = json.load(open(sys.argv[1]))
m = d.get("metrics", {})
def v(name, key):
    return m.get(name, {}).get("values", {}).get(key)
print("p95_ms      =", v("http_req_duration", "p(95)"))
print("avg_ms      =", v("http_req_duration", "avg"))
print("http_reqs   =", v("http_reqs", "count"))
print("failed_rate =", v("http_req_failed", "rate"))
PY

echo "Ket qua tho: ${OUT}.summary.json ${OUT}.k6.log ${OUT}.stats.csv"
exit "$K6_EXIT"
