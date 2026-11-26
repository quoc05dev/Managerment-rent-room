# Management Rent Room

Hệ thống quản lý nhà trọ (Spring Boot + React), kèm thực nghiệm tối ưu CPU/RAM
cho Docker container bằng Particle Swarm Optimization (PSO).

## Thành phần

| Thành phần | Công nghệ | Cổng (localhost) |
|---|---|---|
| Backend | Java 11, Spring Boot 2.7, Spring Security, JPA, ActiveMQ, WebSocket | `8083` → `8080` |
| Frontend | React 18 (CRA), MUI, Ant Design, Chart.js | `3100` → `80` |
| Database | MySQL 8.0 | `3316` → `3306` |
| Message broker | ActiveMQ 5.15 | `61617`, `8162` |
| Giám sát | Prometheus + Grafana + node-exporter | `9090`, `3004` |

Tất cả cổng chỉ bind `127.0.0.1` — dùng SSH tunnel khi cần truy cập từ xa.

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

- Frontend: <http://localhost:3100>
- Backend health: <http://localhost:8083/health>
- Grafana: <http://localhost:3004> (đăng nhập bằng `GRAFANA_ADMIN_PASSWORD` trong `.env`)

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
