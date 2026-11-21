import http from 'k6/http';
import { check } from 'k6';

// Một lần chạy = warmup + steady, tách bằng scenario tag `phase`.
// Runner đọc P95/error của riêng phase=steady từ /out/steady.json.
const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8085';
const RPS = Number(__ENV.RPS || 20);
const WARMUP = __ENV.WARMUP || '60s';
const STEADY = __ENV.STEADY || '120s';
const PATHS = (__ENV.PATHS ||
  '/health,/room/rent-home,/room/1000001/rentaler?pageNo=0&pageSize=10').split(',');

const VUS = Math.max(4, RPS);

export const options = {
  scenarios: {
    warmup: {
      executor: 'constant-arrival-rate',
      rate: RPS,
      timeUnit: '1s',
      duration: WARMUP,
      startTime: '0s',
      tags: { phase: 'warmup' },
      preAllocatedVUs: VUS,
      maxVUs: VUS * 4,
    },
    steady: {
      executor: 'constant-arrival-rate',
      rate: RPS,
      timeUnit: '1s',
      duration: STEADY,
      startTime: WARMUP,
      tags: { phase: 'steady' },
      preAllocatedVUs: VUS,
      maxVUs: VUS * 4,
    },
  },
  // Ngưỡng rất rộng: chỉ để k6 sinh submetric theo tag, không dùng làm pass/fail.
  thresholds: {
    'http_req_duration{phase:steady}': ['p(95)<600000'],
    'http_req_failed{phase:steady}': ['rate<1.1'],
    'http_reqs{phase:steady}': ['count>0'],
  },
};

export default function () {
  const path = PATHS[Math.floor(Math.random() * PATHS.length)];
  const res = http.get(`${BASE_URL}${path}`);
  check(res, { 'status 2xx/3xx': (r) => r.status >= 200 && r.status < 400 });
}

export function handleSummary(data) {
  const m = data.metrics;
  const d = m['http_req_duration{phase:steady}']?.values || {};
  const f = m['http_req_failed{phase:steady}']?.values || {};
  const r = m['http_reqs{phase:steady}']?.values || {};
  const out = {
    p95_ms: d['p(95)'] ?? null,
    avg_ms: d.avg ?? null,
    error_rate: f.rate ?? null,
    requests: r.count ?? null,
    rps: r.rate ?? null,
  };
  return {
    '/out/steady.json': JSON.stringify(out, null, 2),
    stdout: `steady p95=${out.p95_ms}ms err=${out.error_rate} rps=${out.rps}\n`,
  };
}
