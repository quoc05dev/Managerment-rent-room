# Phân tích Workflow CI/CD — Management Rent Room

> Phạm vi: `.github/workflows/deploy.yml`, `docker-compose.yml`,
> `rental-management/Dockerfile`, `rent-manager-app/Dockerfile`,
> `deploy/quock6.click.conf`, `rent-manager-app/nginx.conf`

---

## 1. Mô tả luồng triển khai

Kiến trúc triển khai là **self-hosted VPS**: mỗi lần code được `push` vào nhánh
`main`, GitHub Actions dựng Docker image để kiểm tra tính build được, chạy vài
bước "test" (về bản chất gần như không chặn gì), rồi SSH sang VPS để
`git pull` + `docker compose up -d --build`. **Image đã build trong CI không
được dùng** — VPS tự build lại từ source.

Kiến trúc runtime sau khi deploy (2 tầng reverse proxy):

```
Internet ──▶ Host nginx (:80)                 deploy/quock6.click.conf
              ├── /                ──▶ 127.0.0.1:3100  (container frontend, nginx:alpine)
              ├── /auth/ /oauth2/
              ├── /api/ /room/ /user/ /account/ /contract/ /maintenance/
              ├── /request/ /follow/ /statistical/ /blog-store/ /customer/
              ├── /image/ /document/ /ws/ ...  ──▶ 127.0.0.1:8081 (container backend)
              └── /health             ──▶ 127.0.0.1:8081

container backend (eclipse-temurin:11-jre, :8080 → host :8081)
   ├── mysql      (mysql:8.0,  :3306 → host :3316)
   └── activemq   (rmohr/activemq:5.15.9, :61616 → host :61617, webconsole :8162)
```

Các điểm đáng chú ý về mặt thiết kế:

- **Double proxy**: request `/` đi qua host nginx → frontend nginx → (nếu là API
  path) → backend. Các block `location` bị lặp lại ở cả hai tầng và phải được
  đồng bộ thủ công (có comment cảnh báo drift ở cả hai file).
- **Nginx host chỉ `listen 80`, không có TLS**. `docker-compose.yml:55` và
  `application.yml:70` lại khai báo `https://quock6.click` trong danh sách CORS
  → TLS phải được terminate ở tầng ngoài (Cloudflare / load balancer). Nếu
  không có tầng đó, mọi request `https://` sẽ fail và OAuth2 không hoạt động.
- **Dữ liệu lâu dài** nằm trong 4 named volume: `mysql-data`, `activemq-data`,
  `activemq-log`, `upload-data` (mount vào `/hdd/data/photographer`).
- **Đường đi của OAuth2**: `nginx.conf` và host nginx đều có `location /oauth2/`
  trỏ thẳng vào backend, còn `Connect.js` sinh URL
  `/oauth2/redirect` dựa trên `window.location.origin` → tức là URL được
  tính lại ở browser nhưng request lại do backend xử lý.

---

## 2. Các bước chính của workflow

File: `.github/workflows/deploy.yml` (130 dòng), trigger `push` vào `main`.

### Job `build` (không phụ thuộc gì)

| # | Step | Nội dung |
|---|------|----------|
| 1 | `actions/checkout@v4` | Lấy code tại commit vừa push. |
| 2 | Build backend | `cd rental-management && docker build -t rental-backend:test .` — multi-stage `maven:3.8-eclipse-temurin-11` → `mvn dependency:go-offline` → `mvn package -DskipTests` → `eclipse-temurin:11-jre` + `libreoffice-core`. **Đây là bước duy nhất thật sự chứng minh backend compile được.** |
| 3 | Build frontend | `cd rent-manager-app && docker build -t rental-frontend:test .` — `node:18-alpine` → `npm ci` → `npm run build` (CRA 5) → `nginx:alpine`. |
| 4 | Save images | `docker save ... | gzip > /tmp/{backend,frontend}.tar.gz`. |
| 5 | Upload artifacts | `actions/upload-artifact@v4`, tên `docker-images`, `retention-days: 1`, path `/tmp/*.tar.gz`. |

### Job `test` (`needs: build`)

| # | Step | Ghi chú |
|---|------|---------|
| 1 | Checkout lại code | Tốn thêm 1 runner + checkout cho việc chỉ chạy lint/compile. |
| 2 | `actions/setup-node@v4` | Node 18, `cache: npm`, `cache-dependency-path: rent-manager-app/package-lock.json`. |
| 3 | `npm ci` | — |
| 4 | `npx eslint src/ --max-warnings=999 \|\| true` | **Không bao giờ fail** (`\|\| true` + `--max-warnings=999`) → lint mang tính trang trí. |
| 5 | `npm run build` với `env: CI: false` | Cố tình tắt `CI` để CRA không coi warning là error. Cùng mục đích với step build. |
| 6 | `actions/setup-java@v4` | Java 11 (temurin), `cache: maven`. |
| 7 | `./mvnw compile -B` | `continue-on-error: true` → **không chặn deploy dù fail**. |

Không có `mvn test`, không có `npm test`, không có unit/integration/E2E test nào
thật sự chạy trong pipeline (repo có test nhưng không được CI gọi đến).

### Job `deploy` (`needs: [build, test]`)

| # | Step | Nội dung |
|---|------|----------|
| 1 | `actions/download-artifact@v4` | Tải `docker-images` về `/tmp` — **không có `docker load`**, image tải về không được sử dụng. |
| 2 | `appleboy/ssh-action@v1` | SSH vào VPS, chạy script (xem bên dưới). |

Script remote, theo thứ tự:

1. `cd ~/Quoc/Managerment-rent-room`
2. `[1/4]` `git pull origin main`
3. `[2/4]` `docker compose down --remove-orphans`  ← **gây downtime**
4. `[3/4]` `docker image prune -af` + `docker builder prune -af --filter "until=24h"`
5. `[4/4]` `docker compose up -d --build`  ← build lại từ đầu trên VPS
6. `[5/5]` Cấu hình host nginx: `apt-get install -y nginx \|\| true`, `mkdir -p`
   sites-available/enabled, copy `deploy/quock6.click.conf`, symlink, thêm
   `include /etc/nginx/sites-enabled/*;` vào `nginx.conf` nếu thiếu, `nginx -t`,
   `systemctl enable nginx`, `systemctl restart nginx`
7. `echo "=== Deploy completed at $(date) ==="`

---

## 3. Secret dùng để làm gì

| Secret | Nơi dùng | Mục đích | Đánh giá |
|--------|----------|----------|----------|
| `SERVER_HOST` | `deploy.yml:100` (`with: host`), và lặp lại vô nghĩa ở `deploy.yml:97` (`env: SERVER_HOST`) | Địa chỉ IP/domain của VPS mà `appleboy/ssh-action` sẽ kết nối tới. Giá trị trong `env:` ở dòng 96–98 **hoàn toàn không được action đọc** — dead config gây hiểu nhầm. | Cần thiết. Nên bỏ khối `env:` và dùng `environment:` nếu cần truyền cho script. |
| `SERVER_USER` | `deploy.yml:101` (`with: username`), lặp lại ở `deploy.yml:98` | Tài khoản SSH (thường `root` hoặc user có `sudo`). Job cần **cả passwordless `sudo` không cần mật khẩu** vì script chạy `sudo apt-get`, `sudo cp`, `sudo tee`, `sudo systemctl`. | Cần thiết. Nên thu hẹp: chỉ cần `sudo` cho nhóm lệnh nginx, không cần full NOPASSWD. |
| `SERVER_SSH_KEY` | `deploy.yml:102` (`with: key`) | Private key SSH dạng PEM/OpenSSH để xác thực không cần mật khẩu. Dạng multi-line nên phải lưu trong secret (không dùng được `vars`). | Cần thiết. Nếu key có passphrase, action sẽ fail (không có ô nhập `passphrase`). Nên bật `ssh-keyscan`/host-key pinning và cân nhắc dùng OIDC + key từ secret store thay vì key tĩnh. |

**Secret không dùng ở CI nhưng đang nằm hardcode trong repo** — đây là vấn đề
nghiêm trọng hơn mọi thứ ở trên:

| Loại credential | Vị trí | Ảnh hưởng |
|-----------------|--------|------------|
| `spring.security.oauth2.client.registration.google.clientSecret` | `rental-management/src/main/resources/application.yml:26` | Định danh Google Cloud bị lộ. |
| `spring.security.oauth2.client.registration.facebook.clientSecret` | `application.yml:34` | Định danh Facebook bị lộ. |
| `app.auth.tokenSecret` (JWT signing key) | `application.yml:67` | **Nghiêm trọng** — ai đọc được key này đều tự ký được JWT admin cho hệ thống production. |
| `spring.mail.password` | `application.yml:53` | App password Gmail bị lộ → có thể gửi mail dạng người dùng. |
| `MYSQL_ROOT_PASSWORD` / `SPRING_DATASOURCE_PASSWORD` (`password`) | `docker-compose.yml:9,52` | Root password của DB production là `password`, lộ trong repo. |
| `ACTIVEMQ_ADMIN_PASSWORD` (`admin`) | `docker-compose.yml:31` | Mật khẩu mặc định, cộng thêm `ports: "8162:8161"` đang publish web console ra Internet. |

Khuyến nghị: chuyển toàn bộ sang biến môi trường / secret manager, **rotate ngay**
các credential đã commit (chúng đã nằm trong git history), và thêm
`gitleaks`/`trufflehog` vào CI để chặn tái phát.

---

## 4. Hệ thống được kiểm tra sau deploy như thế nào

**Câu trả lời ngắn: không được kiểm tra gì cả.**

Cụ thể:

- **Không có job `verify` / smoke test.** Commit `d81e6b9` ("chore: remove
  verify job from pipeline") đã xoá job verify từng tồn tại — hiện tại không
  còn bước xác nhận nào sau `systemctl restart nginx`.
- **Không có `curl`/`wget`/`httpie`** gọi `https://quock6.click/health` hay
  `http://127.0.0.1:3100` sau khi container lên. `deploy.yml` không chứa một
  lệnh kiểm tra sức khoẻ nào.
- **Không có `docker compose ps`, `docker ps --filter health`, `docker inspect`
  hay `docker logs`** để xem container có thực sự `Up` không.
- **Không có wait-for-ready.** `docker compose up -d --build` trả về exit code 0
  ngay khi container được tạo, chưa chắc Spring Boot đã listen 8080 hay
  Hibernate đã migrate xong. Pipeline có thể báo xanh trong khi app chưa sẵn sàng.
- **Health endpoint có sẵn nhưng không được dùng.** `HealthController.java:26-29`
  trả `status: "UP"` **cố định** và luôn trả HTTP 200, kể cả khi DB lỗi
  (chỉ đặt `database: "ERROR"` trong body). Nếu ai đó sau này thêm smoke test
  chỉ kiểm tra HTTP status thì nó sẽ luôn xanh — cần đổi thành trả 503 khi
  DB không kết nối được, hoặc thêm actuator `health` group.
- **Cờ "xanh" của job chỉ phản ánh exit code của script SSH.** Vì `sudo apt-get
  install -y nginx 2>/dev/null || true` nuốt lỗi, nhiều lỗi hậu-deploy bị
  chuyển thành *job đỏ dù app vẫn chạy*, hoặc ngược lại là *job xanh dù app
  đã chết*.

Tóm lại, đội phát triển phải tự `ssh` vào VPS và kiểm tra thủ công. Điều này
nên được coi là **ưu tiên hạng 1** khi cải thiện flow: thêm một step
`curl -fsS http://127.0.0.1:3100/health` có retry/backoff và
`curl -fsS -H "Host: quock6.click" http://127.0.0.1/health` (đi qua đúng host
nginx) sau khi deploy, và fail job nếu không đạt.

---

## 5. Các lỗi kỹ thuật có thể gặp trong flow này

Dưới đây là 12 lỗi, xếp theo mức độ ảnh hưởng. Lỗi 1–4 là lỗi **xảy ra chắc
chắn** hoặc **rất cao xác suất**, không phải rủi ro lý thuyết.

### 5.1 🔴 Deploy thất bại làm sập production, không có rollback

`deploy.yml:110` chạy `docker compose down --remove-orphans` **trước** khi
`up --build` ở dòng 117. Hai lệnh này cách nhau thêm `docker image prune -af`
và `docker builder prune -af` — tức là **toàn bộ image cũ và build cache đã bị
xoá sạch trước khi image mới được build**.

Nếu `docker compose up --build` lỗi giữa chừng (hết disk, Maven pull dependency
lỗi, OOM khi build, `mvn package` fail vì test… — dù Dockerfile có
`-DskipTests` nhưng vẫn có thể fail ở bước khác), thì:
- container cũ đã bị xoá,
- image cũ đã bị `prune -af` xoá,
- dịch vụ **nằm liệt cho tới khi có người can thiệp thủ công**.

Thêm nữa không có `healthcheck` cho service `backend` trong
`docker-compose.yml`, và nó dùng `restart: on-failure` (dòng 41) — nghĩa là
nếu backend crash-loop, container sẽ liên tục restart **âm thầm** mà
`docker compose up -d` vẫn trả exit 0, pipeline báo xanh. Đây là kiểu
"CI xanh, production chết" kinh điển.

**Cách sửa:** đổi sang `docker compose up -d --build` **không kèm `down`** (Docker
Compose tự recreate container đổi cấu hình), hoặc dùng
`docker compose up -d --no-deps --build <service>` theo lô; chỉ `down` khi cần
đổi cấu hình port/network. Thêm `healthcheck` + `depends_on: condition:
service_healthy` cho `backend` và `frontend`. Giữ lại image cũ (đừng `prune -af`
ngay trước build; hoặc tag image theo commit SHA để rollback được).

### 5.2 🔴 Code được deploy không phải code mà CI vừa kiểm tra

Job `build`/`test` build image từ **commit SHA cụ thể** mà Actions checkout.
Nhưng job `deploy` lại chạy `git pull origin main` trên VPS (`deploy.yml:107`).

Hai hệ quả:
- **Race condition**: nếu có người push commit B lên `main` sau khi commit A
  đã qua xong `test` nhưng trước khi step SSH bắt đầu, pipeline của A sẽ xanh
  và **deploy B** — B chưa từng qua test. Tệ hơn: B có thể đang lỗi.
- **Server có thể không ở nhánh `main`**: nếu VPS được cài bằng
  `git clone -b <branch>`, hoặc đang ở detached HEAD, hoặc có local commit,
  `git pull origin main` sẽ hỏng hoặc hành xử khác mong đợi.
- `git pull` **fail nếu working tree bẩn** (conflict với file đã sửa tay) →
  deploy abort ngay ở bước 1, tốt hơn là abort sớm, nhưng lỗi này rất dễ xảy
  ra sau một lần debug trực tiếp trên VPS.
- Không `git checkout main` → nếu VPS đang ở nhánh khác thì `git pull origin
  main` merge `main` vào nhánh hiện tại, tạo ra lịch sử lộn xộn.

**Cách sửa:** `git fetch origin && git checkout -f main && git reset --hard
origin/main` (hoặc tốt hơn: truyền `GITHUB_SHA` qua `script_stop`/`envs` và
`git checkout $SHA` để deploy đúng commit đã test), hoặc bỏ `git pull` hoàn
toàn và `docker load` artifact thật sự.

### 5.3 🔴 Artifact 2 tấm bị upload rồi bỏ không — build image trên CI vô nghĩa

`build` job `docker save` + `gzip` + upload (`deploy.yml:25-35`).
`deploy` job `download-artifact` về `/tmp` (`deploy.yml:88-92`).
**Không có `docker load`.** Không có `with:` nào trỏ tới image. File
`/tmp/*.tar.gz` nằm đó rồi bị runner xoá.

Hậu quả:
- Mỗi deploy tốn thêm **thời gian upload + download hàng trăm MB đến ~1-2 GB**
  trong khi **không mang lại giá trị gì** (đây là lý do cũ đã bị ghi chú
  trong lịch sử git: commit `401b238` "feat: full CI/CD pipeline" rồi
  `d81e6b9` "remove verify job").
- **Vòng lặp build không nhất quán**: image build trên `ubuntu-latest` +
  Docker mới có thể khác image build trên VPS + Docker cũ hơn. CI xanh nhưng
  production có thể lỗi build.
- Build backend lặp lại **hai lần** (`docker build` ở job `build` rồi
  `mvn package` ở job `test` rồi `docker compose up --build` trên VPS) —
  tốn 3 lần thời gian build cho cùng một artifact.

**Cách sửa:** hoặc (a) thêm `docker load -i /tmp/backend.tar.gz && docker load -i
/tmp/frontend.tar.gz` + `docker compose up -d` (không `--build`) để deploy
**bit-for-bit chính xác** thứ đã test, hoặc (b) bỏ artifact + job `build` và
chỉ để `docker compose build` chạy trên VPS (chấp nhận không có cổng chất
lượng ở CI). (a) là lựa chọn đúng.

### 5.4 🔴 Pipeline gần như không có "quality gate" nào thật sự

- `npx eslint src/ --max-warnings=999 || true` (`deploy.yml:60`) — `--max-warnings=999`
  và `|| true` cùng lúc đảm bảo **không bao giờ** fail.
- `env: CI: false` (`deploy.yml:65`) — tắt hành vi `treatWarningsAsErrors` của
  CRA. Lý do ghi trong commit `d287219`/`af2e3f1` là hợp lý về mặt kỹ thuật,
  nhưng kết hợp với `|| true` ở lint thì **cả hai job đều trở thành no-op**.
- `./mvnw compile -B` với `continue-on-error: true` (`deploy.yml:78-81`) —
  không chặn gì.
- **Không có test nào chạy**: không `npm test`, không `mvn test`, dù repo có
  test suite (commit `fc458d0` "42/42 tests passing").

Kết hợp: một commit có thể merge và deploy lên production dù **vỡ compile ở
một module khác, sai lint rule, fail test** — miễn là `docker build` ở job
`build` không vỡ. Mà `docker build` chỉ build `rental-management` và
`rent-manager-app` riêng lẻ, nên lỗi ở script `src/` không ai bắt được.

Ngoài ra còn có một lỗi kỹ thuật riêng: **`./mvnw` không có quyền execute**.
`git ls-files -s rental-management/mvnw` cho thấy mode `100644` (không phải
`100755`). Trên `ubuntu-latest`, `./mvnw compile` sẽ fail ngay với
`Permission denied`. Lỗi này bị `continue-on-error: true` che hoàn toàn —
nghĩa là step này **chưa bao giờ thực sự chạy thành công một lần nào** mà
không ai biết. (Sửa: `git update-index --chmod=+x rental-management/mvnw`,
hoặc dùng `mvn` trực tiếp từ `setup-java`.)

### 5.5 🟠 `sudo apt-get install nginx` không có `apt-get update` và bị nuốt lỗi

`deploy.yml:120`: `sudo apt-get install -y nginx 2>/dev/null || true`.

- Không chạy `apt-get update` trước → trên VPS mới hoặc sau khi cache hết hạn,
  `apt-get install` sẽ báo `E: Unable to locate package nginx`.
- `2>/dev/null` + `|| true` che mất lỗi → script đi tiếp.
- `mkdir -p /etc/nginx/sites-available /etc/nginx/sites-enabled` (dòng 121) tạo
  được thư mục dù nginx chưa cài.
- `sudo cp ... /etc/nginx/sites-available/` thành công (thư mục đã tạo).
- `sudo nginx -t` (dòng 127) **fail** vì binary không tồn tại.
- `sudo systemctl enable nginx` (dòng 128) **fail**.
- `sudo systemctl restart nginx` (dòng 129) **fail**.

Kết quả: **job deploy báo ĐỎ, nhưng toàn bộ container đã được start thành công
và app vẫn chạy** (chỉ là chưa có host nginx → không truy cập được từ
Internet). Ngược lại nếu nginx **đã** được cài, dòng 127-129 chạy thành công
và deploy xanh. Tức là trạng thái đỏ/xanh của job **không phản ánh** trạng
thái thật của hệ thống, và cả hai chiều đều gây hiểu nhẫm.

**Cách sửa:** tách phần nginx thành step riêng có `if` guard, hoặc bỏ hẳn
`apt-get install` khỏi deploy (cài nginx một lần khi provision VPS), hoặc
chấp nhận `set -euo pipefail` và xử lý idempotent có kiểm soát.

### 5.6 🟠 Hai commit liên tiếp có thể deploy chồng lên nhau

Không có `concurrency:` trong workflow. Nếu commit B push khi deploy của
commit A **đang chạy** (đặc biệt đoạn `docker compose up -d --build` mất
nhiều phút), hai SSH session chạy song song trên cùng VPS:

- B chạy `docker compose down` → A's `up -d --build` vừa start xong bị dừng
  hoặc bị recreate.
- Cả hai cùng `docker image prune -af` → xoá image mà job kia đang cần để
  `up --build` (build xong, image bị prune giữa lúc, `up` không tìm thấy).
- Hai lần `cp` + `restart nginx` lồng nhau.

**Cách sửa:**
```yaml
concurrency:
  group: deploy-${{ github.ref }}
  cancel-in-progress: false
```

### 5.7 🟠 `appleboy/ssh-action@v1` không có host-key pinning, không có port, không giới hạn thời gian

- `@v1` là **floating tag** → supply-chain risk: bất kỳ ai push commit lên tag
  `v1` của repo đó cũng thay đổi được code chạy trong job deploy (job này có
  `SERVER_SSH_KEY`). Nên **pin SHA** (`uses: appleboy/ssh-action@<40-char-sha>`).
- Không có `port` → mặc định 22. Nếu SSH chạy port khác, deploy fail với
  lỗi khó hiểu.
- Không có `fingerprint` → không chống MITM. Nên set
  `fingerprint: ${{ secrets.SERVER_SSH_FINGERPRINT }}`.
- Không có `timeout-minutes` ở job level → nếu script treo (ví dụ
  `apt-get` hỏi nhập passphrase, `docker build` bị kẹt), runner bị giữ tối đa
  6 giờ rồi mới bị kill, tốn 2.000 phút compute.
- `key:` không hỗ trợ passphrase → nếu key có mật khẩu thì chỉ có cách dùng
  `SSH_ASKPASS`, hiện chưa cấu hình.
- Nên bật OIDC (`aws-actions/configure-aws-credentials` tương tự) thay vì
  lưu key tĩnh, và cấp quyền tối thiểu (deployer không cần `root`).

### 5.8 🟠 `docker image prune -af` xoá mất rollback và phá cache, kéo dài downtime

`deploy.yml:113-114`. Chạy **trước** `up --build`:
- Xoá **toàn bộ** image không còn container nào dùng — tức là xoá luôn image
  của lần deploy trước. Mất rollback, mất khả năng `docker run` image cũ để
  debug.
- `docker builder prune -af` xoá toàn bộ layer cache → `docker compose up
  --build` phải build lại **từ số 0**: `mvn dependency:go-offline` chạy lại
  (mất nhiều phút), `npm ci` chạy lại. Downtime được kéo dài theo thời gian
  build.
- Trong khi đó image CI đã build sẵn bị bỏ không (mục 5.3).

**Cách sửa:** bỏ `prune` khỏi đường deploy (chạy cron job riêng, ví dụ
hàng đêm, `docker image prune -f --filter "until=168h"`), và tag image theo
`$GITHUB_SHA` để giữ được N phiên bản.

### 5.9 🟠 `restart: on-failure` + không healthcheck = backend crash-loop im lặng

`docker-compose.yml:36-48`:
- Service `backend` **không có `healthcheck`**, trong khi `mysql` thì có
  (dòng 15-20).
- `depends_on: activemq: condition: service_started` (dòng 46) — chỉ chờ
  container ActiveMQ *khởi động*, chưa chờ broker sẵn sàng nhận kết nối.
  ActiveMQ cần ~10-20s để boot. Backend có thể thử connect JMS quá sớm → lỗi
  lúc startup.
- `restart: on-failure` khiến container restart **vô hạn** nếu app luôn crash.
  Docker Compose không báo lỗi, `docker compose up -d` trả 0, pipeline xanh.
- Ngoài ra `depends_on` của `frontend` (`docker-compose.yml:66-67`) chỉ chờ
  backend `service_started` — nhưng frontend nginx chỉ cần config, không sao;
  vấn đề là các request proxy sang backend sẽ 502 trong vài chục giây đầu.
- `libreoffice-core` được cài trong image backend
  (`rental-management/Dockerfile:12`) nhưng
  `application.yml:64` lại trỏ `libreOfficePath` tới
  `/hdd/setup/libreoffice/opt/libreoffice6.4/program/` — path này **không tồn
  tại trong container** (apt cài vào `/usr/lib/libreoffice`). Kết hợp với việc
  chỉ cài `libreoffice-core` (không phải `libreoffice-writer`), chức năng
  xuất Excel/PDF (`/export-bill`, `/document/`) nhiều khả năng **lỗi runtime
  trên production** dù container "healthy".

**Cách sửa:** thêm `healthcheck` cho `backend` (vd `curl -f localhost:8080/health`
hoặc actuator), đổi `activemq` sang `condition: service_healthy` với healthcheck
thật, sửa `libreOfficePath` thành path thật trong container (hoặc mount
`/hdd/setup/libreoffice` từ host), đặt `restart: unless-stopped` + `deploy:
replicas` tối thiểu nếu cần HA.

### 5.10 🟡 Cấu hình nginx lặp lại ở hai tầng và đã **drift** sẵn

`deploy/quock6.click.conf` và `rent-manager-app/nginx.conf` chứa hai bản sao
của cùng một danh sách `location`. Comment ở cả hai file đều cảnh báo điều này
(`quock6.click.conf:120-122`, `nginx.conf:140-142`). So sánh:

| Path prefix | Host nginx | Frontend nginx | Hệ quả |
|---|---|---|---|
| `^~ /view-file/` | ❌ thiếu | ✅ có | Request đi host → frontend → backend. **OK nhưng là 3 hop thay vì 2**, và phụ thuộc vào việc frontend nginx vẫn được deploy đúng. |
| `^~ /document/` | `/document/` (không `^~`) | `^~ /document/` | Lệch. |
| `/authorization` | ❌ thiếu | ❌ thiếu | `setupProxy.js:24` liệt kê `/authorization` là API root. Request `/authorization/...` trên production → rơi vào `location /` → SPA fallback trả `index.html` thay vì JSON. Nếu đây là endpoint thật thì đã **hỏng trên production**. |
| `/health` | ✅ | ✅ | Trùng lặp không cần thiết. |
| regex root paths | `account\|room\|contract\|maintenance\|request\|follow\|statistical` | **giống hệt** | Cả hai đều **thiếu `customer` và `blog-store`**. `GET /customer` (đúng chuỗi, không có `/` cuối) không match `location /customer/` → match `location /` → trả `index.html`. Client parse JSON sẽ lỗi. `Connect.js` dùng `API_BASE_URL = ''` (đường dẫn tương đối) nên frontend **không có base URL cứu lỗi**. |
| WebSocket `/ws/` | ✅ | ✅ | Cả hai đều OK, nhưng phải giữ đồng bộ. |
| `X-Forwarded-Proto` | ✅ gửi `$scheme` | ✅ | Backend Spring dùng giá trị này để sinh `baseUrl` cho OAuth2 redirect. Với TLS terminate ở Cloudflare, `$scheme` trên host nginx là `http` → `baseUrl` thành `http://quock6.click` → **Google/Facebook từ chối redirect URI không phải HTTPS**. Cần `map $http_x_forwarded_proto` để ưu tiên header từ upstream. |

Mỗi lần thêm endpoint backend phải sửa **3 file** (`quock6.click.conf`,
`nginx.conf`, `setupProxy.js`) và không có test nào phát hiện nếu quên. Đây
chính là lý do tồn tại những comment giải thích chi tiết về `location ~`
— chúng là vết của các bug đã phát hiện thủ công.

**Cách sửa:** chỉ để **một** tầng nginx xử lý routing API. Có thể bỏ hẳn
tầng host nginx (trỏ DNS/Cloudflare thẳng vào `:3100`) hoặc bỏ proxy API ở
frontend nginx (chỉ serve static + SPA fallback, mọi `/api/*` do host nginx
đi thẳng vào backend). Rồi sinh ra danh sách path từ **một** nguồn duy nhất
(ví dụ script đọc từ `SecurityConfig.java`) để không bao giờ drift nữa.

### 5.11 🟡 `ddl-auto: update` không kèm backup — rủi ro mất dữ liệu

`docker-compose.yml:53` đặt `SPRING_JPA_HIBERNATE_DDL_AUTO: update`, và
`application.yml:16` cũng `ddl-auto: update`.

Deploy = `docker compose down` + `up` → app khởi động lại và **Hibernate tự
chạy DDL trên database production**. `update` chỉ add column/index, nhưng
khi entity đổi kiểu, đổi tên, thêm `NOT NULL` không default, hoặc thêm unique
constraint lên cột đã có dữ liệu trùng → lệnh ALTER **fail giữa chừng**,
schema ở trạng thái nửa vời, container crash-loop, và **không có backup nào
được tạo trước đó**.

Đây là lỗi triển khai dữ liệu kinh điển. Đặc biệt nguy hiểm ở đây vì
`docker compose down` đã xoá container → mất toàn bộ state ứng dụng, chỉ còn
volume `mysql-data` để cứu.

**Cách sửa:** đưa schema vào migration có version (Flyway/Liquibase), tắt
`ddl-auto` ở production, thêm step `mysqldump` vào artifact lưu lại trước mỗi
deploy và giữ N bản.

### 5.12 🟡 Lỗi nhỏ nhưng gây mất dữ liệu/nhầm lẫn khác

| Vấn đề | Vị trí | Tác động |
|---|---|---|
| `version: "3.8"` | `docker-compose.yml:1` | Compose v2 warning, sẽ bị loại bỏ hoàn toàn ở các bản tương lai. Bỏ dòng này. |
| `ports: "3316:3306"`, `"61617:61616"`, `"8162:8161"` | `docker-compose.yml:12,27-28` | **MySQL và ActiveMQ console đang lộ ra Internet.** Ai đó brute-force được `root/password` và `admin/admin` là chiếm được toàn bộ hệ thống. Bỏ `ports` hoặc bind `127.0.0.1:...`. |
| `MYSQL_ROOT_PASSWORD: password` | `docker-compose.yml:9` | Mật khẩu root 1 ký tự, trong repo. |
| `.dockerignore` của backend có `target/` nhưng Dockerfile build multi-stage lấy `target/*.jar` từ stage `build` | `rental-management/Dockerfile:13` | Đúng (đọc từ stage build, không phải context) — nhưng dòng `!**/src/main/**/target/` trong `.dockerignore` là dư và gây hiểu nhầm. |
| `deploy.yml:96-98` khai báo `env: SERVER_HOST/SERVER_USER` | `deploy.yml:96-98` | Dead config — action không đọc `env` này. Dễ khiến người khác sửa nhầm chỗ. Xoá. |
| Job `test` checkout lại repo chỉ để chạy lint | `deploy.yml:42` | Tốn thêm 1 runner + checkout. Có thể gộp vào job `build`. |
| Không có `permissions:` | toàn file | Mặc định `GITHUB_TOKEN` có thể rộng hơn cần thiết. Đặt `permissions: contents: read` ở top-level. |
| Không có `timeout-minutes` | toàn file | Job treo giữ 6 giờ. |
| Trigger chỉ `push: main` | `deploy.yml:3-5` | Không có `pull_request` → **PR không hề được build/test**, lỗi chỉ lộ ra sau khi merge. Chạy `npm test`/`mvn test` trên PR là nơi CI thật sự tạo giá trị. |

---

## 6. Tóm tắt & thứ tự ưu tiên đề xuất

| # | Hành động | Cấp |
|---|---|---|
| 1 | **Rotate ngay** JWT `tokenSecret`, Google/Facebook client secret, Gmail app password, MySQL root password. Chuyển sang env var. | Khẩn cấp |
| 2 | Bỏ `ports` publish MySQL/ActiveMQ console ra Internet (chỉ bind `127.0.0.1`). | Khẩn cấp |
| 3 | Thêm **smoke test sau deploy**: `curl` `/health` qua host nginx, có retry; fail job nếu không đạt. Đổi `HealthController` trả 503 khi DB lỗi. | Cao |
| 4 | Bỏ `docker compose down` trước `up --build`; thêm `healthcheck` + `condition: service_healthy`; `restart: unless-stopped`. | Cao |
| 5 | `docker load` artifact thật sự **hoặc** bỏ artifact + bỏ `image prune -af` trong đường deploy. | Cao |
| 6 | Gỡ `\|\| true` khỏi lint, `continue-on-error` khỏi compile, thêm `npm test` + `mvn test`; sửa `+x` cho `mvnw`. | Cao |
| 7 | Thêm `concurrency`, `timeout-minutes`, `permissions: contents: read`; pin action theo SHA. | Trung bình |
| 8 | Deploy theo `GITHUB_SHA` cố định thay vì `git pull origin main`. | Trung bình |
| 9 | Gộp 2 tầng nginx thành 1, sinh danh sách path từ nguồn duy nhất. | Trung bình |
| 10 | Sửa `libreOfficePath` + cài `libreoffice-writer`; thêm trigger `pull_request`; bỏ `version:`; dọn `env:` chết. | Thấp |
