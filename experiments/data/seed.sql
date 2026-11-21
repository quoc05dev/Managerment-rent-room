-- Seed dữ liệu thực nghiệm cho rental_home (P2).
-- Idempotent: xoá dải id seed rồi nạp lại. Marker: id 1xxxxxx/2xxxxxx + created_by='seed'.
-- Chạy: mysql --default-character-set=utf8mb4 rental_home < seed.sql
-- Gỡ:   clean_seed.sql

SET NAMES utf8mb4;
SET SESSION cte_max_recursion_depth = 100000;

START TRANSACTION;

-- 1. Xoá seed cũ (con -> cha)
DELETE FROM comment      WHERE room_id BETWEEN 2000001 AND 2005000 OR user_id BETWEEN 1000001 AND 1000300;
DELETE FROM rate         WHERE room_id BETWEEN 2000001 AND 2005000 OR user_id BETWEEN 1000001 AND 1000300;
DELETE FROM follow       WHERE rentaler_id BETWEEN 1000001 AND 1000300 OR customer_id BETWEEN 1000001 AND 1000300;
DELETE FROM request      WHERE room_id BETWEEN 2000001 AND 2005000;
DELETE FROM maintenance  WHERE room_id BETWEEN 2000001 AND 2005000;
DELETE FROM contract     WHERE room_id BETWEEN 2000001 AND 2005000;
DELETE FROM asset        WHERE room_id BETWEEN 2000001 AND 2005000;
DELETE FROM room_media   WHERE room_id BETWEEN 2000001 AND 2005000;
DELETE FROM blog_store   WHERE room_id BETWEEN 2000001 AND 2005000 OR user_id BETWEEN 1000001 AND 1000300;
DELETE FROM message_chat WHERE message_id IN (SELECT id FROM message WHERE user1 BETWEEN 1000001 AND 1000300 OR user2 BETWEEN 1000001 AND 1000300);
DELETE FROM message      WHERE user1 BETWEEN 1000001 AND 1000300 OR user2 BETWEEN 1000001 AND 1000300;
DELETE FROM room         WHERE id BETWEEN 2000001 AND 2005000;
DELETE FROM user_roles   WHERE user_id BETWEEN 1000001 AND 1000300;
DELETE FROM users        WHERE id BETWEEN 1000001 AND 1000300;

-- 2. Users: 20 rentaler (1000001-1000020) + 200 customer (1000021-1000220)
INSERT INTO users (id, created_at, updated_at, address, email, email_verified, is_confirmed, is_locked, name, password, phone, provider)
WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 220)
SELECT 1000000 + n,
       NOW() - INTERVAL (n % 200) DAY, NOW(), 'Hà Nội',
       CONCAT('seed.', n, '@example.com'), 1, 1, 0,
       CONCAT(ELT(1 + (n % 10), 'Nguyễn','Trần','Lê','Phạm','Hoàng','Vũ','Đặng','Bùi','Đỗ','Ngô'),
              ' Văn ',
              ELT(1 + (n % 10), 'An','Bình','Cường','Dũng','Hải','Hùng','Khanh','Long','Minh','Nam'),
              ' ', n),
       NULL,
       CONCAT('09', LPAD(n, 8, '0')),
       'local'
FROM seq;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON r.name = 'ROLE_RENTALER'
WHERE u.id BETWEEN 1000001 AND 1000020;

INSERT INTO user_roles (user_id, role_id)
SELECT u.id, r.id FROM users u JOIN roles r ON r.name = 'ROLE_USER'
WHERE u.id BETWEEN 1000021 AND 1000220;

-- 3. Rooms: 5000 (2000001-2005000)
INSERT INTO room (id, created_at, updated_at, address, created_by, description, is_approve,
                  is_locked, is_remove, latitude, longitude, price, status, title, updated_by,
                  category_id, location_id, user_id)
WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 5000)
SELECT 2000000 + n,
       NOW() - INTERVAL (n % 365) DAY, NOW() - INTERVAL (n % 30) DAY,
       CONCAT(ELT(1 + (n % 6), 'Số ','Ngõ ','Ngách ','Hẻm ','Tổ ','Phố '), 1 + (n % 200), ' ',
              ELT(1 + (n % 8), 'Cầu Giấy','Đống Đa','Hai Bà Trưng','Thanh Xuân','Ba Đình','Hoàng Mai','Tây Hồ','Nam Từ Liêm'),
              ', Hà Nội'),
       'seed',
       CONCAT('Phòng cho thuê #', n, ', đầy đủ tiện nghi, an ninh tốt, giờ giấc tự do.'),
       IF(n % 10 = 0, 0, 1),
       IF(n % 20 = 0, 'DISABLE', 'ENABLE'),
       IF(n % 25 = 0, 1, 0),
       21.0 + (n % 100) / 1000.0,
       105.8 + (n % 100) / 1000.0,
       1500000 + (n % 40) * 250000,
       ELT(1 + (n % 10), 'ROOM_RENT','ROOM_RENT','ROOM_RENT','ROOM_RENT','ROOM_RENT',
                         'ROOM_RENT','ROOM_RENT','HIRED','CHECKED_OUT','ROOM_RENT'),
       CONCAT(ELT(1 + (n % 6), 'Phòng trọ','Căn hộ mini','Nhà nguyên căn','Phòng trọ','Chung cư mini','Phòng trọ'),
              ' ', ELT(1 + (n % 8), 'Cầu Giấy','Đống Đa','Hai Bà Trưng','Thanh Xuân','Ba Đình','Hoàng Mai','Tây Hồ','Nam Từ Liêm'),
              ' - ', n),
       'seed',
       1 + (n % 3),
       1,
       1000001 + (n % 20)
FROM seq;

-- 4. Ảnh + tiện ích: 2/room
INSERT INTO room_media (files, room_id)
WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 10000)
SELECT CONCAT('https://picsum.photos/seed/room', 2000000 + 1 + FLOOR((n - 1) / 2), '/800/600'),
       2000000 + 1 + FLOOR((n - 1) / 2)
FROM seq;

INSERT INTO asset (name, number, room_id)
WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 10000)
SELECT ELT(1 + (n % 6), 'Điều hoà','Nóng lạnh','Tủ lạnh','Máy giặt','Giường','Tủ quần áo'),
       1 + (n % 2),
       2000000 + 1 + FLOOR((n - 1) / 2)
FROM seq;

-- 5. Đánh giá + bình luận: 1/room
INSERT INTO rate (created_at, updated_at, rating, room_id, user_id)
WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 5000)
SELECT NOW() - INTERVAL (n % 180) DAY, NOW(), 3 + (n % 3), 2000000 + n, 1000021 + (n % 200)
FROM seq;

INSERT INTO comment (created_at, updated_at, content, rate_id, room_id, user_id)
SELECT r.created_at, r.updated_at, CONCAT('Phòng ổn, đúng mô tả (seed #', r.id, ')'),
       r.id, r.room_id, r.user_id
FROM rate r
WHERE r.room_id BETWEEN 2000001 AND 2005000;

-- 6. Hợp đồng / bảo trì / yêu cầu: 1/5 room
INSERT INTO contract (created_at, updated_at, created_by, deadline_contract, name, name_of_rent,
                      num_of_people, phone, updated_by, room_id)
WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 1000)
SELECT NOW() - INTERVAL (n % 300) DAY, NOW(), 'seed', NOW() + INTERVAL (n % 12) MONTH,
       CONCAT('Hợp đồng thuê phòng #', n), CONCAT('Khách thuê seed #', n),
       1 + (n % 4), CONCAT('08', LPAD(n, 8, '0')), 'seed', 2000000 + n * 5
FROM seq;

INSERT INTO maintenance (created_at, updated_at, created_by, maintenance_date, price, updated_by, room_id)
WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 1000)
SELECT NOW() - INTERVAL (n % 120) DAY, NOW(), 'seed', NOW() - INTERVAL (n % 90) DAY,
       100000 + (n % 20) * 50000, 'seed', 2000000 + n * 5
FROM seq;

INSERT INTO request (description, is_answer, name, phone_number, room_id)
WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 1000)
SELECT CONCAT('Yêu cầu xem phòng #', n), IF(n % 2 = 0, 1, 0),
       CONCAT('Khách seed #', n), CONCAT('07', LPAD(n, 8, '0')), 2000000 + n * 5
FROM seq;

-- 7. Follow + lưu phòng: 100 dòng
INSERT INTO follow (created_at, updated_at, customer_id, rentaler_id)
WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 100)
SELECT NOW() - INTERVAL (n % 60) DAY, NOW(), 1000021 + (n % 200), 1000001 + (n % 20)
FROM seq;

INSERT INTO blog_store (created_at, updated_at, room_id, user_id)
WITH RECURSIVE seq(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM seq WHERE n < 100)
SELECT NOW() - INTERVAL (n % 60) DAY, NOW(), 2000000 + n * 7, 1000021 + (n % 200)
FROM seq;

COMMIT;

SELECT 'users' t, COUNT(*) n FROM users
UNION ALL SELECT 'room', COUNT(*) FROM room
UNION ALL SELECT 'room_media', COUNT(*) FROM room_media
UNION ALL SELECT 'asset', COUNT(*) FROM asset
UNION ALL SELECT 'rate', COUNT(*) FROM rate
UNION ALL SELECT 'comment', COUNT(*) FROM comment
UNION ALL SELECT 'contract', COUNT(*) FROM contract
UNION ALL SELECT 'maintenance', COUNT(*) FROM maintenance
UNION ALL SELECT 'request', COUNT(*) FROM request
UNION ALL SELECT 'follow', COUNT(*) FROM follow
UNION ALL SELECT 'blog_store', COUNT(*) FROM blog_store;
