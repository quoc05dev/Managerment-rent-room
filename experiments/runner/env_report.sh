#!/usr/bin/env bash
# Thu thập thông số môi trường cho docs/research/01-environment.md.
# Chạy trên VPS: bash experiments/runner/env_report.sh
# Chỉ đọc, không thay đổi gì.
set -uo pipefail
cd "$(dirname "$0")/../.." || exit 1

section() { printf '\n## %s\n' "$1"; }
run() { printf '$ %s\n' "$*"; "$@" 2>&1 || printf '(exit %s)\n' "$?"; }

section "Thoi diem"
date -Is

section "Git"
run git rev-parse HEAD
run git log -1 --format='%h %s'

section "He dieu hanh"
run uname -a
run nproc
grep -m1 'model name' /proc/cpuinfo 2>/dev/null || true
run free -m
run df -h /
printf 'cgroup_fs=%s\n' "$(stat -fc %T /sys/fs/cgroup 2>/dev/null)"

section "Docker"
run docker version --format 'client={{.Client.Version}} server={{.Server.Version}}'
run docker compose version
docker info --format 'ncpu={{.NCPU}} mem_bytes={{.MemTotal}} driver={{.Driver}}' 2>/dev/null || true
docker info --format 'cgroup_version={{.CgroupVersion}}' 2>/dev/null || true

section "Image va digest"
docker images --digests --format '{{.Repository}}:{{.Tag}} {{.Digest}} {{.Size}}' 2>/dev/null \
  | grep -Ei 'rental|mysql|activemq|prometheus|grafana|node-exporter|cadvisor' || true

section "Container dang chay"
docker ps --format 'table {{.Names}}\t{{.Image}}\t{{.Status}}\t{{.Ports}}'

section "Gioi han tai nguyen hien tai"
for c in rental-backend rental-mysql rental-activemq rental-frontend \
         rental-prometheus rental-grafana rental-node-exporter; do
  docker inspect "$c" --format '{{.Name}} nanocpus={{.HostConfig.NanoCpus}} mem_limit={{.HostConfig.Memory}} restart_count={{.RestartCount}} oom_killed={{.State.OOMKilled}}' 2>/dev/null || true
done

section "Image ID cua container dang chay"
for c in rental-backend rental-frontend; do
  docker inspect "$c" --format '{{.Name}} image_id={{.Image}} config_image={{.Config.Image}}' 2>/dev/null || true
done

section "Phien ban runtime"
docker exec rental-backend java -version 2>&1 | head -3 || true
docker exec rental-backend sh -c 'echo JAVA_TOOL_OPTIONS=${JAVA_TOOL_OPTIONS:-<unset>}; echo JAVA_OPTS=${JAVA_OPTS:-<unset>}' 2>/dev/null || true
docker exec rental-mysql mysql --version 2>/dev/null || true
nginx -v 2>&1 || true

section "Tai nguyen tuc thoi"
docker stats --no-stream --format 'table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}\t{{.NetIO}}\t{{.BlockIO}}'

section "Dung luong volume"
docker system df
