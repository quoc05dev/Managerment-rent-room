# P0 — Môi trường đo và baseline

> Số liệu dưới đây lấy từ workflow **P0 Baseline** (`workflow_dispatch`), chạy trên
> VPS production ngày 2026-11-21, commit `ca75188`. Lệnh tái lập:
> `bash experiments/runner/env_report.sh` và
> `RPS=5 DURATION=30s bash experiments/runner/smoke_baseline.sh`.

## 1. Máy chủ

| Thông số | Giá trị |
|---|---|
| Hostname / kernel | `techbyte`, Linux `6.8.0-149-generic` (Ubuntu), x86_64 |
| CPU | 16 vCPU, Intel Xeon Platinum 8180 @ 2.50 GHz |
| RAM | 64.301 MB (~62,8 GiB), **swap = 0** |
| Đĩa `/` | `/dev/sda1`, 290 GB, đã dùng 125 GB, còn 166 GB (43%) |
| cgroup | v2 (`cgroup2fs`) |
| Docker / Compose | 29.9.3 / v5.7.0, storage driver `overlayfs` |

## 2. Runtime ứng dụng

| Thành phần | Phiên bản |
|---|---|
| Backend | Temurin OpenJDK 11.0.33 (Java 11) |
| `JAVA_TOOL_OPTIONS` / `JAVA_OPTS` | **chưa đặt** (không có `-Xmx`, không `MaxRAMPercentage`) |
| MySQL | 8.0.46 (Community) |
| Nginx host | 1.24.0 (Ubuntu) |
| Frontend | image `managerment-rent-room-frontend` |

## 3. Image và digest

| Image | Digest / ID | Size |
|---|---|---|
| backend (build local) | `sha256:e83bf3e1e47943f8b7a982e6ecb1799921529ba6617085b919a2d9ef1fc4aa4d` | — |
| frontend (build local) | `sha256:c0412c5261698af8ecb69e9d90d826e56f38df23f081bf3c6ea31afefd8027f4` | — |
| `mysql:8.0` | `sha256:7dcddc01f13bab2f15cde676d44d01f61fc9f99fe7785e86196dfc07d358ae2b` | 1.1 GB |
| `prom/prometheus:v3.16.0` | `sha256:e04987641b57704f4e08e31f6373ba4138ecf27cb4a165d24aabb6c38fddd0f06` | 389 MB |
| `prom/node-exporter:v1.12.1` | `sha256:1b4e4438faca4d7d7e001dd445d161a4a2091b0fededa84093b3a8dfeae1f1be0` | 41 MB |
| `grafana/grafana:13.3.1` | `sha256:0615ec4fbd4072004b7d86b46ded63013a74b7d6eb1119273dd89e8fa25c13cf` | 2.02 GB |

Backend/frontend build local nên không có registry digest; dùng image ID làm định
danh tái lập, kèm commit hash của repo.

## 4. Giới hạn tài nguyên hiện tại

Tất cả container của dự án đều **không có giới hạn**:

| Container | `NanoCpus` | `Memory` | RestartCount | OOMKilled |
|---|---|---|---|---|
| `rental-backend` | 0 | 0 | 0 | false |
| `rental-mysql` | 0 | 0 | 0 | false |
| `rental-activemq` | 0 | 0 | 0 | false |
| `rental-frontend` | 0 | 0 | 0 | false |
| `rental-prometheus` | 0 | 0 | 0 | false |
| `rental-grafana` | 0 | 0 | 0 | false |
| `rental-node-exporter` | 0 | 0 | 0 | false |

Đây chính là baseline "không giới hạn" để so sánh với cấu hình PSO.

## 5. Tiêu thụ tài nguyên lúc chụp (idle, 5 rps chưa chạy)

| Container | CPU % | RAM | Ghi chú |
|---|---|---|---|
| `rental-backend` | 0.19% | 1.173 GiB | JVM mặc định, chưa có `-Xmx` |
| `rental-mysql` | 0.83% | 388.2 MiB | |
| `rental-activemq` | 0.24% | 366.8 MiB | |
| `rental-grafana` | 1.90% | 258.3 MiB | |
| `rental-prometheus` | 0.45% | 132.7 MiB | |
| `rental-node-exporter` | 0.00% | 27.8 MiB | |
| `rental-frontend` | 0.00% | 13.1 MiB | |

Dung lượng Docker: 78 image / 36.43 GB, 64 container / 916.6 MB, 48 volume /
16.73 GB, **build cache 75.12 GB (65.45 GB reclaimable)**. Cần dọn cache trước khi
chạy thí nghiệm dài để tránh đầy đĩa.

## 6. Baseline smoke

Kịch bản `experiments/load/smoke.js`, chạy trực tiếp vào backend
(`http://127.0.0.1:8083`), **5 rps trong 30s**, 3 endpoint công khai:
`/health`, `/room/rent-home`, `/room/1000001/rentaler?pageNo=0&pageSize=10`.

Đo lần 1 (commit `ca75188`) khi DB **gần rỗng**:

| Chỉ số | Giá trị |
|---|---|
| Tổng request | 150 |
| RPS thực tế | 5.00 |
| P95 (client) | **12.89 ms** |
| Trung bình | 8.91 ms |
| Tỉ lệ lỗi | **0%** |

Đo lần 2 (commit `71d17ca`) sau khi nạp dataset P2 (`experiments/data/seed.sql`:
5.000 phòng, 220 user, 10.000 ảnh, 10.000 tiện ích, 5.000 đánh giá):

| Chỉ số | Giá trị |
|---|---|
| Tổng request | 151 |
| RPS thực tế | 5.03 |
| P95 (client) | **174.76 ms** |
| Trung bình | 61.70 ms |
| Tỉ lệ lỗi | **0%** |

Chênh lệch ~13,6 lần chứng minh baseline rỗng không đại diện. Nguyên nhân: `GET
/room/rent-home` hard-code `PageRequest.of(0, 100)` và mapper ModelMapper kéo lazy
`category/location/user/assets/roomMedia` cho từng phòng → N+1 (~600 query/request);
riêng endpoint này warm ~185–228 ms/request. Đây vẫn là **smoke test**, không phải
capacity test; số liệu chính thức lấy từ capacity test trên stack clone ở P2.

## 7. Phát hiện trong P0

1. **`GET /room` (không có `userId`) trả 500 khi anonymous.** Endpoint được
   `permitAll` nhưng service gọi `getUserId()` và ném exception. Không dùng endpoint
   này trong load test cho tới khi sửa; ghi nhận như bug production.
2. **DB gần rỗng** (lúc P0): `/health` báo `totalUsers=1`, `totalRoles=3`. Đã xử lý
   ở P2 bằng `experiments/data/seed.sql` (xem `02-dataset.md`).
3. **Không có giới hạn tài nguyên** và **không có `JAVA_TOOL_OPTIONS`** → baseline
   hiện tại không xác định được trần heap; P1 phải thêm biến này.
4. **VPS dùng chung rất nặng**: 64 container, 51 đang chạy, gồm `minikube`,
   `minikube-m02`, `minikube-m03`, `checkscam-*`, `team-backend`, `nghiphep`,
   `examinai-staging-postgres-1`. Lúc chụp, `minikube` chiếm 32.6% CPU và
   `minikube-m02` 31.2%. Đây là **threat to validity lớn nhất**: không được dùng
   số liệu host làm fitness; phải chạy giờ thấp điểm và ghi `node_load1`.
5. **Build cache 75 GB** (65 GB reclaimable) → cần `docker builder prune` trước
   chuỗi thí nghiệm dài.

## 8. Hệ quả cho P1/P2

- P1: thêm `cpus`/`mem_limit`/`JAVA_TOOL_OPTIONS`, cAdvisor, histogram percentile.
- P2: seeder dữ liệu, capacity test trên stack clone `rental-exp` (port riêng),
  chạy ngoài giờ cao điểm; ghi lại `node_load1` mỗi run.
- Không chạy thí nghiệm PSO trên production: vừa ảnh hưởng người dùng thật, vừa
  không tái lập được do nhiễu từ các project khác.
