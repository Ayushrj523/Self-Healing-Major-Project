/**
 * SENTINELS v2.0 — k6 HTTP Flood Script
 * Simulates traffic floods against Netflix API Gateway to test SENTINELS detection.
 *
 * Usage:
 *   k6 run --vus 50 --duration 60s chaos/k6-scripts/http-flood.js
 *
 * Environment Variables:
 *   K6_TARGET_URL  - Base URL (default: http://localhost:8001)
 *   K6_VUS         - Virtual users override
 */

import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// ─── Custom Metrics ─────────────────────────────────────────
const errorRate = new Rate('error_rate');
const responseTime = new Trend('response_time_ms');

// ─── Configuration ──────────────────────────────────────────
const BASE_URL = __ENV.K6_TARGET_URL || 'http://localhost:8001';

export const options = {
  scenarios: {
    // Ramp up gradually to simulate realistic traffic spike
    traffic_spike: {
      executor: 'ramping-vus',
      startVUs: 1,
      stages: [
        { duration: '10s', target: 10 },   // Warm up
        { duration: '20s', target: 50 },   // Ramp to moderate load
        { duration: '30s', target: 100 },  // Spike to high load
        { duration: '20s', target: 100 },  // Sustain peak
        { duration: '10s', target: 0 },    // Cool down
      ],
    },
    // Constant high load for steady-state testing
    steady_flood: {
      executor: 'constant-vus',
      vus: 50,
      duration: '60s',
      startTime: '100s',
    },
  },
  thresholds: {
    http_req_duration: ['p(95)<2000'],
    error_rate: ['rate<0.5'],
  },
};

// ─── Endpoints ──────────────────────────────────────────────
const ENDPOINTS = [
  { path: '/api/content/browse', method: 'GET', weight: 40 },
  { path: '/api/content/1', method: 'GET', weight: 20 },
  { path: '/api/search?q=action', method: 'GET', weight: 15 },
  { path: '/api/recommend/user/1', method: 'GET', weight: 10 },
  { path: '/api/health', method: 'GET', weight: 10 },
  { path: '/api/stream/play', method: 'POST', weight: 5 },
];

function selectEndpoint() {
  const total = ENDPOINTS.reduce((sum, e) => sum + e.weight, 0);
  let rand = Math.random() * total;
  for (const ep of ENDPOINTS) {
    rand -= ep.weight;
    if (rand <= 0) return ep;
  }
  return ENDPOINTS[0];
}

// ─── Main Test Function ─────────────────────────────────────
export default function () {
  const endpoint = selectEndpoint();
  const url = `${BASE_URL}${endpoint.path}`;

  let res;
  if (endpoint.method === 'POST') {
    res = http.post(url, JSON.stringify({ content_id: 1, user_id: 1 }), {
      headers: { 'Content-Type': 'application/json' },
    });
  } else {
    res = http.get(url);
  }

  // Record metrics
  responseTime.add(res.timings.duration);
  const isError = res.status >= 400 || res.status === 0;
  errorRate.add(isError);

  check(res, {
    'status is 2xx': (r) => r.status >= 200 && r.status < 300,
    'response time < 1s': (r) => r.timings.duration < 1000,
  });

  // Minimal sleep to maximize load
  sleep(0.1 + Math.random() * 0.2);
}

// ─── Summary Handler ────────────────────────────────────────
export function handleSummary(data) {
  const summary = {
    timestamp: new Date().toISOString(),
    total_requests: data.metrics.http_reqs.values.count,
    avg_response_ms: data.metrics.http_req_duration.values.avg.toFixed(2),
    p95_response_ms: data.metrics.http_req_duration.values['p(95)'].toFixed(2),
    error_rate: (data.metrics.error_rate?.values?.rate || 0).toFixed(4),
    vus_max: data.metrics.vus_max?.values?.value || 0,
  };

  return {
    stdout: JSON.stringify(summary, null, 2) + '\n',
    'evaluation_results.jsonl': JSON.stringify(summary) + '\n',
  };
}
