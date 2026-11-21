# P2 - Dataset thực nghiệm

> Sinh ngày 2026-11-21, commit `71d17ca`. Tái lập bằng workflow **DB Seed**
> (`workflow_dispatch`, mode `seed`, confirm `yes`).

## 1. Vì sao phải seed

Baseline P0 chạy trên DB gần rỗng (1 user, 3 role, 0 phòng) cho P95 = 12.89 ms.
Sau khi nạp dataset, cùng tải 5 rps cho P95 = **174.76 ms** (xem
`01-environment.md` §6). Không có dữ liệu thì P95 và fitness của PSO vô nghĩa.

## 2. Ràng buộc schema (quan trọng cho stack clone)

Các native query trong `RoomRepositoryCustomImpl` hard-code schema:

```sql
from rental_home.room r ...
```

Hệ quả: **không thể** tạo DB tên khác (vd `rental_home_exp`) cho stack clone —
app vẫn đọc `rental_home.room`. Stack clone `rental-exp` phải chạy **MySQL riêng
với database tên `rental_home`** (container/volume riêng), không dùng chung
instance production.

Vì vậy dataset hiện nạp vào production `rental_home`; mọi bản ghi seed đều nằm
trong dải id riêng và có `created_by='seed'`, gỡ được bằng một lệnh.

## 3. Nội dung dataset

| Bảng | Số dòng seed | Dải id | Ghi chú |
|---|---|---|---|
| `users` | 220 | 1000001–1000220 | 20 rentaler (role `ROLE_RENTALER`), 200 customer (`ROLE_USER`); password NULL (không đăng nhập được) |
| `room` | 5.000 | 2000001–2005000 | 3 category, 1 location (Hà Nội), 20 rentaler |
| `room_media` | 10.000 | auto | 2 ảnh/phòng |
| `asset` | 10.000 | auto | 2 tiện ích/phòng |
| `rate` | 5.000 | auto | 1/phòng, rating 3–5 |
| `comment` | 5.000 | auto | 1/rate |
| `contract` | 1.000 | auto | 1/5 phòng |
| `maintenance` | 1.000 | auto | 1/5 phòng |
| `request` | 1.000 | auto | 1/5 phòng |
| `follow` | 100 | auto | customer theo dõi rentaler |
| `blog_store` | 100 | auto | customer lưu phòng |

Phân bố `room` cố ý có nhiễu để query lọc có ý nghĩa:

- `is_approve`: 10% = false (chờ duyệt).
- `is_locked`: 5% = `DISABLE`.
- `is_remove`: 4% = true.
- `status`: 80% `ROOM_RENT`, 10% `HIRED`, 10% `CHECKED_OUT`.
- `price`: 1.5–11.25 triệu VND; `created_at` rải trong 365 ngày.

`/room/rent-home` trả ~76% số phòng (status ∈ {ROOM_RENT, CHECKED_OUT} và
`is_locked='ENABLE'`), nên response luôn đầy 100 phần tử.

## 4. Cách chạy / gỡ

```bash
# Nạp (idempotent: xoá dải seed rồi nạp lại)
gh workflow run db-seed.yml -f mode=seed -f confirm=yes

# Gỡ sạch, giữ dữ liệu thật
gh workflow run db-seed.yml -f mode=clean -f confirm=yes

# Kiểm tra nóng endpoint (5 lần/endpoint)
gh workflow run db-seed.yml -f mode=check
```

SQL nguồn: `experiments/data/seed.sql`, `experiments/data/clean_seed.sql`.
Dùng recursive CTE (`cte_max_recursion_depth=100000`) nên không có file dump lớn;
`NOW()` tính theo thời điểm chạy.

## 5. Đo nóng sau seed (1 request, chưa tối ưu)

| Endpoint | Thời gian | Payload |
|---|---|---|
| `/health` | 6–10 ms | nhỏ |
| `/room/rent-home` | **185–352 ms** | 100 phòng + nested |
| `/room/1000001/rentaler?pageNo=0&pageSize=10` | 9–12 ms | 10 phòng |
| `/room/1000002/rentaler?pageNo=0&pageSize=10` | 32–36 ms | 10 phòng |

`/room/rent-home` chậm vì `getRentOfHome()` hard-code `PageRequest.of(0, 100)` và
ModelMapper kéo lazy từng phòng (N+1 ~600 query). Đây là mục tiêu tối ưu hiển
nhiên và là lý do chính khiến P95 tăng 13,6 lần so với DB rỗng.

## 6. Việc còn lại của P2

- Dựng stack clone `rental-exp` (compose riêng, MySQL riêng cùng tên DB
  `rental_home`, port 8085) và nạp cùng seed.sql.
- Chạy `experiments/load/capacity.js` trên clone để chốt `target_rps` thật thay
  cho giá trị provisional 20.
- Tắt `spring.jpa.show-sql` khi đo (hiện `true`, log SQL làm nhiễu I/O).
- Cân nhắc sửa `GET /room` anonymous 500 (bug production, không chặn P2).
