# P3 — Cô lập tài nguyên & stack thực nghiệm

> Số liệu ngày 2026-11-21 (UTC+7), commit `80667c7`, VPS `techbyte`.
> Đây là artifact của P3: quyết định cô lập, cách dựng stack clone và bằng chứng
> harness PSO chạy được.

## 1. Quyết định cô lập

Ba lựa chọn đã cân nhắc:

| Cách | Kết luận |
|---|---|
| Docker Compose project riêng | **Dùng** — tách container/volume/network khỏi production |
| cgroup v2 slice (`rental-exp.slice`) | **Dùng** — chặn trần CPU/RAM cho cả cụm, đọc được `cpu.stat`/`memory.peak` |
| VM (KVM) | **Không** — VPS không có `/dev/kvm` |
| Docker-in-Docker | **Không** — thêm một tầng ảo hoá, sai số đo |

Hệ quả:

- Giới hạn **từng container** (`cpus`, `memory`) do Docker đặt, đây là biến PSO.
- Giới hạn **cả cụm** do slice đặt: `CPUQuota=400%` (4 core), `MemoryMax=6G`.
  Trần này rộng hơn ngân sách thực nghiệm (ΣCPU ≤ 4.0, ΣRAM ≤ 4096 MB) nên không
  cắt mất candidate hợp lệ, nhưng chặn trường hợp một container vượt xa.
- Load generator (k6) chạy **ngoài** slice để không bị chặn bởi ngân sách của hệ
  thống cần đo.

## 2. Cách dựng và vận hành

```bash
# 1. Tạo slice (một lần sau reboot)
gh workflow run experiments.yml -f mode=slice-create

# 2. Dựng stack và gắn vào slice
gh workflow run experiments.yml -f mode=up -f isolate=1

# 3. Nạp dữ liệu + kiểm tra
gh workflow run experiments.yml -f mode=seed
gh workflow run experiments.yml -f mode=smoke
gh workflow run experiments.yml -f mode=status

# 4. Chạy PSO (mặc định 4 eval để smoke; full = 80)
gh workflow run experiments.yml -f mode=run -f max_evals=80
gh workflow run experiments.yml -f mode=results

# 5. Dọn
gh workflow run experiments.yml -f mode=slice-remove
gh workflow run experiments.yml -f mode=down
```

Lưu ý: `up` **không** tự bật slice. Nếu chạy `up` không có `isolate=1`, Compose
recreate container và bỏ `cgroup_parent`; phải chạy lại `up -f isolate=1`.

## 3. Bằng chứng cô lập

`docker inspect` sau `up -f isolate=1`:

```
rental-exp-backend -> rental-exp.slice
rental-exp-mysql   -> rental-exp.slice
```

`systemctl show rental-exp.slice`:

```
ActiveState=active
ControlGroup=/rental.slice/rental-exp.slice
```

systemd đặt tên lồng nhau: `rental-exp.slice` là con của `rental.slice`, nên
đường dẫn thật là `/sys/fs/cgroup/rental.slice/rental-exp.slice`. Các script
resolve path bằng `systemctl show -p ControlGroup` thay vì hard-code.

Giới hạn đọc từ cgroup:

```
cpu.max:    400000 100000      # 4 core
memory.max: 6442450944         # 6 GiB
```

`systemctl status` lúc 3 container đang chạy: `Memory: 1.0G (max: 6.0G, peak:
1.1G)`, `Tasks: 151` — slice đang thực sự chứa cả cụm.

## 4. Stack clone `rental-exp`

| Thành phần | Giá trị |
|---|---|
| Compose project | `rental-exp` |
| MySQL | `127.0.0.1:3317`, database **`rental_home`** (bắt buộc: native query hard-code schema) |
| Backend | `127.0.0.1:18085` → 8080 (8085 bị service khác chiếm trên host) |
| ActiveMQ | chỉ trong network nội bộ |
| JVM | `JAVA_TOOL_OPTIONS=-XX:MaxRAMPercentage=70` (heap theo `mem_limit`) |
| SQL log | `SPRING_JPA_SHOW_SQL=false` |

Seed trên clone khớp production: 221 users, 5.000 room, 10.000 room_media,
10.000 asset, 5.000 rate, 5.000 comment, 1.000 contract/maintenance/request,
100 follow, 100 blog_store.

Smoke (cold):

```
/health                                       200   0.019 s
/room/rent-home                               200   1.079 s  (93 KB)
/room/1000001/rentaler?pageNo=0&pageSize=10   200   0.040 s
```

`/room/rent-home` cold chậm hơn production vì stack vừa khởi động và bị giới hạn
tài nguyên; sau warmup 60 s, P95 ở 20 rps ổn định ~165–178 ms.

## 5. Smoke PSO 2 evaluation

Chạy `mode=run -f max_evals=2`, mỗi eval gồm: áp `cpus`/`memory`, restart
backend, warmup 60 s + steady 120 s tại 20 rps, lấy mẫu cgroup mỗi 2 s.

| # | backend | mysql | P95 (ms) | throughput (rps) | CPU backend | CPU mysql | RAM peak backend | RAM peak mysql | throttle backend | OOM | F |
|---|---|---|---|---|---|---|---|---|---|---|---|
| p0 | 2.50c / 768 MB | 1.25c / 1408 MB | 178.00 | 20.01 | 0.804 | 0.498 | 312.1 MB | 550.9 MB | 9.4% | 0 | 0.5452 |
| p1 | 1.75c / 1792 MB | 2.00c / 768 MB | 165.30 | 20.00 | 0.788 | 0.464 | 522.0 MB | 555.4 MB | 29.8% | 0 | 0.5559 |

Thời gian mỗi eval: 195–201 s → 80 eval ước tính **4,5–5 h**, nằm trong ngân sách
10 h.

Hai điểm cần ghi rõ trong báo cáo:

1. `throughput_rps` = `requests / steady_seconds` (2400/120 = 20 rps). Trường
   `rps` của k6 chia cho toàn bộ thời lượng test (180 s) nên chỉ ~13,3; runner
   lưu riêng `throughput_rps` để không nhầm.
2. Cấu hình 768 MB **không OOM** dù RSS production không giới hạn là 1,17 GiB:
   heap bị chặn ở 70% × 768 MB ≈ 537 MB, JVM GC nhiều hơn nhưng vẫn sống. Vì vậy
   `mem_mb.min = 768` là khả thi, không cần nâng lên.

## 6. Giới hạn & threats to validity

- **Host dùng chung rất nặng**: 64 container (51 running, có minikube ~63% CPU
  tổng). Slice không bảo vệ khỏi tải bên ngoài; `host_load1` được ghi lại mỗi
  eval (lần smoke: 1,43 → 6,23). Phải chạy giờ thấp điểm và không dùng số liệu
  host làm fitness.
- `CPUQuota` là **trần**, không phải đặt trước; container vẫn tranh CPU với
  phần còn lại của host khi slice chưa chạm trần.
- Không ghim CPU (`AllowedCPUs`); nếu cần giảm nhiễu có thể bật thêm, nhưng sẽ
  giảm tính đại diện.
- k6 ngoài slice chịu tranh chấp host — đúng với điều kiện vận hành thật, nhưng
  làm tăng phương sai; vì vậy mỗi cấu hình cần lặp và kiểm định phi tham số.
- Slice không `enable` lúc boot; sau reboot phải `slice-create` + `up -f isolate=1`.
- Volume MySQL giữ dữ liệu qua `down`; chỉ `down -v` mới xoá (không dùng trong
  quy trình).
