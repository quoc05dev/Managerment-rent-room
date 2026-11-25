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

## P3 — stack clone & PSO

```bash
gh workflow run experiments.yml -f mode=slice-create
gh workflow run experiments.yml -f mode=up -f isolate=1
gh workflow run experiments.yml -f mode=seed
gh workflow run experiments.yml -f mode=smoke
gh workflow run experiments.yml -f mode=run -f max_evals=4   # smoke
gh workflow run experiments.yml -f mode=run -f max_evals=80  # full
gh workflow run experiments.yml -f mode=results
```

> Lưu ý thời gian: mỗi evaluation ≈ 3,3 phút nên `max_evals=80` ≈ 4,5 giờ vượt
> giới hạn 120 phút của workflow và sẽ bị dừng giữa chừng. Chạy 80 eval trực
> tiếp trên VPS (tmux/nohup) hoặc tăng `timeout-minutes`/`command_timeout`.

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
