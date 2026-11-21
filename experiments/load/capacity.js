import http from 'k6/http';
import { check } from 'k6';

// Capacity test: tăng dần RPS để tìm ngưỡng bền vững của baseline.
// Chỉ chạy trên stack clone (P2), KHÔNG chạy trên production.
const BASE_URL = __ENV.BASE_URL || 'http://127.0.0.1:8085';
const MAX_RPS = Number(__ENV.MAX_RPS || 100);
const RAMP = __ENV.RAMP || '5m';
const HOLD = __ENV.HOLD || '2m';
const PATHS = (__ENV.PATHS ||
  '/health,/room/rent-home,/room/1000001/rentaler?pageNo=0&pageSize=10').split(',');

export const options = {
  scenarios: {
    capacity: {
      executor: 'ramping-arrival-rate',
      startRate: 1,
      timeUnit: '1s',
      preAllocatedVUs: Math.max(10, Math.ceil(MAX_RPS / 2)),
      maxVUs: Math.max(50, MAX_RPS * 2),
      stages: [
        { target: MAX_RPS, duration: RAMP },
        { target: MAX_RPS, duration: HOLD },
      ],
    },
  },
};

export default function () {
  const path = PATHS[Math.floor(Math.random() * PATHS.length)];
  const res = http.get(`${BASE_URL}${path}`);
  check(res, { 'status 2xx/3xx': (r) => r.status >= 200 && r.status < 400 });
}

export function handleSummary(data) {
  return {
    '/out/capacity.json': JSON.stringify(data, null, 2),
    stdout: `p95_ms=${data.metrics.http_req_duration.values['p(95)']} ` +
      `max_rps=${MAX_RPS} failed=${data.metrics.http_req_failed.values.rate}\n`,
  };
}
