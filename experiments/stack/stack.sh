#!/usr/bin/env bash
# Quản lý stack clone thực nghiệm (project rental-exp, cổng 18085/3317).
#   bash experiments/stack/stack.sh probe|up|seed|smoke|status|results|slice-*|down
#   EXP_ISOLATE=1 ... up  -> gắn cgroup_parent rental-exp.slice (xem isolate.sh)
set -euo pipefail
cd "$(dirname "$0")/../.." || exit 1

MODE="${1:-status}"
COMPOSE_FILES=(-f experiments/stack/docker-compose.exp.yml)
[ "${EXP_ISOLATE:-0}" = "1" ] && COMPOSE_FILES+=(-f experiments/stack/docker-compose.slice.yml)
COMPOSE=(docker compose -p rental-exp "${COMPOSE_FILES[@]}")
EXP_MYSQL_PASSWORD="${EXP_MYSQL_PASSWORD:-exp_password}"
BACKEND_URL="${BACKEND_URL:-http://127.0.0.1:18085}"
export EXP_MYSQL_PASSWORD

mysql_exp() {
  docker exec -e MYSQL_PWD="$EXP_MYSQL_PASSWORD" -i rental-exp-mysql \
    mysql -uroot --default-character-set=utf8mb4 "$@"
}

wait_health() {
  for i in $(seq 1 90); do
    if curl -fsS --max-time 2 "$BACKEND_URL/health" >/dev/null 2>&1; then
      echo "backend healthy sau ${i}s"
      return 0
    fi
    sleep 2
  done
  echo "backend KHONG healthy"
  docker logs --tail=80 rental-exp-backend || true
  return 1
}

case "$MODE" in
  probe)
    echo "== python =="; python3 --version
    python3 -c 'import yaml; print("pyyaml", yaml.__version__)' 2>&1 || echo "pyyaml: KHONG CO"
    echo "== docker =="; docker version --format '{{.Server.Version}}'
    docker info --format 'cgroup_driver={{.CgroupDriver}} cgroup_version={{.CgroupVersion}}'
    echo "== kvm =="; ls -l /dev/kvm 2>&1 || echo "khong co /dev/kvm"
    echo "== systemd =="; systemctl --version | head -1
    echo "== images =="; docker images --format '{{.Repository}}:{{.Tag}} {{.ID}}' | grep -Ei 'rent|k6|cadvisor' || true
    echo "== cgroup controllers =="; cat /sys/fs/cgroup/cgroup.controllers
    echo "== cgroup subtree =="; cat /sys/fs/cgroup/cgroup.subtree_control
    echo "== cgroup parent =="
    for c in rental-backend rental-exp-backend rental-exp-mysql; do
      echo "$c -> $(docker inspect "$c" --format '{{.HostConfig.CgroupParent}}' 2>/dev/null || echo 'khong co')"
    done
    echo "== slice rental-exp =="; cat /sys/fs/cgroup/rental-exp.slice/cpu.max 2>/dev/null || echo "chua tao slice"
    echo "== ports dang dung =="; ss -ltn | grep -E ':(18085|3317|8083|8085)\b' || true
    ;;
  up)
    "${COMPOSE[@]}" up -d --remove-orphans
    "${COMPOSE[@]}" ps
    wait_health
    ;;
  seed)
    mysql_exp rental_home < experiments/data/seed.sql
    ;;
  smoke)
    wait_health
    for u in /health "/room/rent-home" "/room/1000001/rentaler?pageNo=0&pageSize=10"; do
      printf '%s -> ' "$u"
      curl -s -o /dev/null -w '%{http_code} %{time_total}s %{size_download}B\n' "$BACKEND_URL$u"
    done
    ;;
  status)
    "${COMPOSE[@]}" ps
    docker stats --no-stream --format '{{.Name}} {{.CPUPerc}} {{.MemUsage}}' | grep rental-exp- || true
    ;;
  results)
    latest=$(ls -t experiments/results/raw/pso-*.jsonl 2>/dev/null | head -1 || true)
    [ -n "$latest" ] || { echo "chua co ket qua"; exit 1; }
    echo "== $latest =="; tail -n 5 "$latest"
    echo "== gbest gan nhat =="
    cat "$(ls -t experiments/results/raw/gbest-*.json 2>/dev/null | head -1)"
    ;;
  slice-create|slice-status|slice-remove)
    bash experiments/stack/isolate.sh "${MODE#slice-}"
    ;;
  down)
    "${COMPOSE[@]}" down
    ;;
  *)
    echo "mode khong hop le: $MODE"; exit 1
    ;;
esac
