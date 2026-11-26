# Management Rent Room

Hệ thống quản lý nhà trọ (Spring Boot + React), kèm thực nghiệm tối ưu CPU/RAM
cho Docker container bằng Particle Swarm Optimization (PSO).

## Thành phần

| Thành phần | Công nghệ |
|---|---|
| Backend | Java 11, Spring Boot 2.7, Spring Security, JPA, ActiveMQ, WebSocket |
| Frontend | React 18 (CRA), MUI, Ant Design, Chart.js |
| Database | MySQL 8.0 |
| Message broker | ActiveMQ 5.15 |
| Giám sát | Prometheus + Grafana + node-exporter |

Các dịch vụ nội bộ chỉ bind `127.0.0.1`; truy cập từ xa qua SSH tunnel hoặc Nginx.

## Cấu trúc

```
rental-management/   # backend Spring Boot
rent-manager-app/    # frontend React
experiments/         # stack clone + PSO (xem experiments/README.md)
docs/research/       # khung nghiên cứu, môi trường, dataset, cô lập
deploy/              # cấu hình Nginx
monitoring/          # Prometheus + Grafana
.github/workflows/   # deploy, db-seed, P0 baseline, experiments
docker-compose.yml   # stack production
```

## Chạy nhanh (Docker Compose)

```bash
cp .env.example .env      # trên server: điền mật khẩu thật, KHÔNG commit .env
docker compose up -d --build
docker compose ps
```

- Truy cập frontend/backend/Grafana qua Nginx (xem `deploy/`) hoặc SSH tunnel.
- Tài khoản Grafana lấy từ `GRAFANA_ADMIN_PASSWORD` trong `.env`.

## Thực nghiệm PSO

Chạy trên stack clone `rental-exp` (không đụng production), điều khiển qua
workflow `Experiments`:

```bash
gh workflow run experiments.yml -f mode=probe
gh workflow run experiments.yml -f mode=slice-create
gh workflow run experiments.yml -f mode=up -f isolate=1
gh workflow run experiments.yml -f mode=seed
gh workflow run experiments.yml -f mode=smoke
gh workflow run experiments.yml -f mode=run -f method=pso -f max_evals=24
gh workflow run experiments.yml -f mode=run -f method=fixed -f runs=10
gh workflow run experiments.yml -f mode=run -f method=rule  -f runs=10
gh workflow run experiments.yml -f mode=run -f method=validate -f runs=10
gh workflow run experiments.yml -f mode=results
gh workflow run experiments.yml -f mode=down
```

Quy trình đầy đủ, lưu ý timeout và ý nghĩa từng mode: **`experiments/README.md`**.
Khung nghiên cứu: `docs/research/00-rq.md`; cô lập tài nguyên: `docs/research/03-isolation.md`.

## Bảo mật

- Không commit `.env` (đã gitignore); `.env.example` chỉ là mẫu.
- MySQL/ActiveMQ/Grafana chỉ bind `127.0.0.1`; ra Internet qua Nginx + TLS.
