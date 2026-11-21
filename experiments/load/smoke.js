import http from 'k6/http';
import { check } from 'k6';

// Smoke/steady-state ngắn để xác nhận harness và lấy P95 phía client.
// Dùng cho P0 (baseline nhanh); thí nghiệm chính dùng capacity.js rồi scenario cố định RPS.
const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8083';
const RPS = Number(__ENV.RPS || 5);
const DURATION = __ENV.DURATION || '30s';
const PATHS = (__ENV.PATHS ||
  '/health,/room?title=&pageNo=0&pageSize=10,/room/rent-home').split(',');

export const options = {
  scenarios: {
    steady: {
      executor: 'constant-arrival-rate',
      rate: RPS,
      timeUnit: '1s',
      duration: DURATION,
      preAllocatedVUs: Math.max(2, RPS),
      maxVUs: Math.max(10, RPS * 4),
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const path = PATHS[Math.floor(Math.random() * PATHS.length)];
  const res = http.get(`${BASE_URL}${path}`);
  check(res, { 'status 2xx/3xx': (r) => r.status >= 200 && r.status < 400 });
}

// Runner mount thư mục kết quả vào /out; file này là dữ liệu thô cho P0.
export function handleSummary(data) {
  return {
    '/out/summary.json': JSON.stringify(data, null, 2),
    stdout: `p95_ms=${data.metrics.http_req_duration.values['p(95)']} ` +
      `rps=${data.metrics.http_reqs.values.rate} ` +
      `failed=${data.metrics.http_req_failed.values.rate}\n`,
  };
}
