# Thư mục thực nghiệm PSO.
#
# Xem `config.yaml` cho biến/SLO/ngân sách, `docs/research/00-rq.md` cho khung
# nghiên cứu. Raw data nằm trong `results/raw/` (không commit).

## Cấu trúc

```
experiments/
  config.yaml          # nguồn sự thật cho mọi tham số
  load/smoke.js        # P0: 5 rps, 30s, kiểm tra harness
  load/capacity.js     # P2: tìm RPS bền vững (chạy trên stack clone)
  runner/env_report.sh # P0: thu thập môi trường
  runner/smoke_baseline.sh
  results/raw/         # JSONL/JSON thô, bị gitignore
```

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
