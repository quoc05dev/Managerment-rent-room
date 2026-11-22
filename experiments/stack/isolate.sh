#!/usr/bin/env bash
# (Tuỳ chọn) Cô lập tài nguyên cho stack thực nghiệm bằng cgroup v2 slice.
#   bash experiments/stack/isolate.sh create|status|remove
# Sau khi create, chạy stack với EXP_ISOLATE=1 để gắn cgroup_parent:
#   EXP_ISOLATE=1 bash experiments/stack/stack.sh up
set -euo pipefail

SLICE="rental-exp.slice"
UNIT="/etc/systemd/system/$SLICE"
CPU_QUOTA="${EXP_SLICE_CPU_QUOTA:-400%}"   # 4 core
MEM_MAX="${EXP_SLICE_MEM_MAX:-6G}"         # rộng hơn tổng limit của container

case "${1:-status}" in
  create)
    cat > "$UNIT" <<EOF
[Unit]
Description=PSO experiment cgroup slice

[Slice]
CPUQuota=$CPU_QUOTA
MemoryMax=$MEM_MAX
Delegate=yes
EOF
    systemctl daemon-reload
    systemctl stop "$SLICE" 2>/dev/null || true
    systemctl start "$SLICE"
    echo "đã tạo $SLICE (CPUQuota=$CPU_QUOTA, MemoryMax=$MEM_MAX)"
    ;;
  remove)
    systemctl stop "$SLICE" 2>/dev/null || true
    rm -f "$UNIT"
    systemctl daemon-reload
    echo "đã xoá $SLICE"
    ;;
  status)
    systemctl status "$SLICE" --no-pager || true
    systemctl show "$SLICE" -p ActiveState -p SubState -p ControlGroup || true
    # systemd dat ten long nhau: rental-exp.slice nam duoi rental.slice
    CG="$(systemctl show "$SLICE" -p ControlGroup --value)"
    echo "cpu.max: $(cat "/sys/fs/cgroup$CG/cpu.max" 2>/dev/null || echo n/a)"
    echo "memory.max: $(cat "/sys/fs/cgroup$CG/memory.max" 2>/dev/null || echo n/a)"
    echo "cgroup path: ${CG:-none}"
    find "/sys/fs/cgroup$CG" -maxdepth 2 -type d 2>/dev/null | head -5 || true
    ;;
  *)
    echo "dùng: $0 create|status|remove"; exit 1
    ;;
esac
