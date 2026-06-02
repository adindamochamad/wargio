/**
 * Uji beban ringan — 10 VU, 30 detik.
 * Jalankan: k6 run -e BASE_URL=https://domain-anda.com deploy/k6/smoke_10_users.js
 */
import http from "k6/http";
import { check, sleep } from "k6";

export const options = {
  vus: 10,
  duration: "30s",
  thresholds: {
    http_req_duration: ["p(95)<5000"],
    checks: ["rate>0.9"],
  },
};

const base = __ENV.BASE_URL?.replace(/\/$/, "") || "http://127.0.0.1:8000";

export default function () {
  const health = http.get(`${base}/api/health`);
  check(health, { "health 200": (r) => r.status === 200 });

  const chat = http.post(
    `${base}/api/chat`,
    JSON.stringify({ pesan: "stok indomie goreng berapa?" }),
    {
      headers: {
        "Content-Type": "application/json",
        "X-Session-Id": `k6-${__VU}`,
      },
    },
  );
  check(chat, { "chat 200": (r) => r.status === 200 });
  sleep(1);
}
