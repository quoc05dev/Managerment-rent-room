# Thư mục thực nghiệm PSO.
#
# Xem `config.yaml` cho biến/SLO/ngân sách, `docs/research/00-rq.md` cho khung
# nghiên cứu. Raw data nằm trong `results/raw/` (không commit).

## Cấu trúc

```
experiments/
  config.yaml              # nguồn sự thật cho mọi tham số
  data/seed.sql            # P2: dữ liệu thực tế (idempotent, marker created_by='seed')
  load/smoke.js            # P0: 5 rps, 30s, kiểm tra harness
  load/capacity.js         # P2: tìm RPS bền vững (chạy trên stack clone)
  load/steady.js           # P3: warmup + steady cho từng evaluation PSO
  runner/env_report.sh     # P0: thu thập môi trường
  runner/smoke_baseline.sh
  stack/docker-compose.exp.yml  # clone rental-exp: mysql 3317, backend 18085
  stack/docker-compose.slice.yml# overlay gắn cgroup_parent
  stack/isolate.sh         # tạo/xoá/kiểm tra rental-exp.slice
  stack/stack.sh           # probe|up|seed|smoke|status|results|slice-*|down
  pso/runner.py            # PSO 6 bước, --dry-run/--max-evals
  results/raw/             # JSONL/JSON thô, bị gitignore
```

## P3 — quy trình thử nghiệm (theo thứ tự)

Mỗi dòng là một lần `workflow_dispatch` trên GitHub Actions (hoặc gọi
`stack.sh`/`runner.py` tương ứng khi chạy trực tiếp trên VPS). PSO phải chạy
**trước** `validate` vì `validate` đọc file `gbest-*.json` mới nhất.

```bash
# 0) kiểm tra môi trường, tạo slice cgroup
gh workflow run experiments.yml -f mode=probe
gh workflow run experiments.yml -f mode=slice-create
# 1) dựng stack clone trong slice (không đụng production)
gh workflow run experiments.yml -f mode=up -f isolate=1
# 2) nạp dữ liệu + smoke harness
gh workflow run experiments.yml -f mode=seed
gh workflow run experiments.yml -f mode=smoke
# 3) kiểm tra cấu hình PSO (không gọi Docker)
gh workflow run experiments.yml -f mode=dry
# 4) tối ưu PSO — 24 eval ≈ 80 phút
gh workflow run experiments.yml -f mode=run -f method=pso -f max_evals=24
# 5) đối chứng, mỗi phương án n=10
gh workflow run experiments.yml -f mode=run -f method=fixed -f runs=10
gh workflow run experiments.yml -f mode=run -f method=rule  -f runs=10
# 6) validate dùng gbest của PSO ở bước 4
gh workflow run experiments.yml -f mode=run -f method=validate -f runs=10
# 7) xuất kết quả (summary + JSONL thô) rồi dọn stack
gh workflow run experiments.yml -f mode=results
gh workflow run experiments.yml -f mode=raw
gh workflow run experiments.yml -f mode=down
```

- `mode=dry` chỉ dùng cho PSO (`--dry-run` bị chặn với `validate`).
- `isolate=1` chỉ có tác dụng ở bước `up`; slice mặc định `CPUQuota=500%`.
- Mỗi evaluation ≈ 3,3 phút nên `max_evals=80` ≈ 4,5 giờ, **vượt**
  `timeout-minutes: 120` / `command_timeout: 115m` → chạy trực tiếp trên VPS
  (tmux/nohup) hoặc tăng timeout (GitHub tối đa 6 giờ).
- `results` in summary JSON; `raw` in JSONL từng run; dữ liệu gốc ở
  `results/raw/` (gitignore), tổng hợp bằng `docs/research/analyze_results.py`.
- Sau reboot phải làm lại `slice-create` + `up`.

Chi tiết cô lập và bằng chứng: `docs/research/03-isolation.md`.

## P0 — chạy trên VPS

```bash
cd ~/Quoc/Managerment-rent-room
bash experiments/runner/env_report.sh
RPS=5 DURATION=30s bash experiments/runner/smoke_baseline.sh
```

Hoặc bấm chạy workflow **P0 Baseline** (workflow_dispatch) trên GitHub Actions.

## Nguyên tắc

- Baseline P0 chỉ dùng RPS thấp để không ảnh hưởng production.
- Capacity test và thí nghiệm PSO phải chạy trên stack clone `rental-exp`.
- Mọi con số dùng trong báo cáo phải sinh từ `results/raw/` bằng script, không vẽ tay.
