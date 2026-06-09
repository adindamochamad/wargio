# Hari 5 — Load Test k6

| Field | Nilai |
|-------|-------|
| Waktu (UTC) | 2026-06-07T15:54:43Z |
| URL | https://wargio.adindamochamad.com |
| Skrip | deploy/k6/smoke_10_users.js |
| VU | 10 |
| Durasi | 30s |
| Threshold | p95 < 5000ms, checks > 90% |

## Hasil

```
    http_req_duration..............: avg=1.36s min=20.21ms med=1.38s max=4.66s p(90)=2.21s p(95)=2.84s
```

## Log lengkap

```

  █ THRESHOLDS 

    checks
    ✓ 'rate>0.9' rate=100.00%

    http_req_duration
    ✓ 'p(95)<5000' p(95)=2.84s


  █ TOTAL RESULTS 

    checks_total.......: 172     5.09865/s
    checks_succeeded...: 100.00% 172 out of 172
    checks_failed......: 0.00%   0 out of 172

    ✓ health 200
    ✓ chat 200

    HTTP
    http_req_duration..............: avg=1.36s min=20.21ms med=1.38s max=4.66s p(90)=2.21s p(95)=2.84s
      { expected_response:true }...: avg=1.36s min=20.21ms med=1.38s max=4.66s p(90)=2.21s p(95)=2.84s
    http_req_failed................: 0.00%  0 out of 172
    http_reqs......................: 172    5.09865/s

    EXECUTION
    iteration_duration.............: avg=3.74s min=2.21s   med=3.5s  max=7.21s p(90)=5.12s p(95)=5.83s
    iterations.....................: 86     2.549325/s
    vus............................: 1      min=1        max=10
    vus_max........................: 10     min=10       max=10

    NETWORK
    data_received..................: 155 kB 4.6 kB/s
    data_sent......................: 31 kB  908 B/s




running (0m33.7s), 00/10 VUs, 86 complete and 0 interrupted iterations
default ✓ [ 100% ] 10 VUs  30s
```

DoD: p95 response < 5 detik untuk 10 concurrent users.
