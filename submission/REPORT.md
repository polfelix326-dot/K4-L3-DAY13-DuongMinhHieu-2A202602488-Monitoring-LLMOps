# Báo cáo cá nhân — K4-L3A Day 13 Monitoring & LLMOps

> Mỗi học viên hoàn thiện một file duy nhất này. Khi dẫn evidence, dùng đường dẫn tương đối, ví dụ `evidence/07-trace-waterfall.png`.

## 1. Thông tin học viên

- **Họ và tên:**
- **MSSV:**
- **Lớp:** K4-L3A
- **Repository URL:**
- **Commit SHA cuối:**
- **Challenge ID:**
- **Tên project Langfuse cá nhân:** `day13-k4-l3a-2A202602488`

## 2. Evidence index

Điền đúng đường dẫn tới evidence thực tế. Có thể đổi tên hoặc dùng nhiều ảnh nếu cần.

| Evidence | Đường dẫn |
|---|---|
| Pytest cuối | `evidence/01-pytest.png` |
| Log validator | `evidence/02-log-validator.png` |
| Dashboard validator | `evidence/03-dashboard-validator.png` |
| Structured log | `evidence/04-structured-log.png` |
| PII redaction | `evidence/05-pii-redaction.png` |
| Trace list | `evidence/06-trace-list.png` |
| Trace waterfall | `evidence/07-trace-waterfall.png` |
| Trace metadata | `evidence/08-trace-metadata.png` |
| Prompt versions | `evidence/09-prompt-versions.png` |
| Prompt rollback | `evidence/10-prompt-rollback.png` |
| Dashboard runtime | `evidence/11-dashboard-overview.png` |
| Incident metric | `evidence/12-incident-metric.png` |
| Incident log | `evidence/13-incident-log.png` |
| Incident trace | `evidence/14-incident-trace.png` |

## 3. Kết quả kỹ thuật

| Nội dung | Baseline | Kết quả cuối | Nhận xét |
|---|---|---|---|
| `validate_logs.py` | 30/100 | | Thiếu correlation ID và enrichment; bình thường ở CP0. |
| `validate_dashboard.py` | 6/6 | | Contract hợp lệ; chưa xác minh dashboard runtime. |
| `pytest` | 22 passed in 3.08s | | |
| Số traces hợp lệ | 10 trace mới có root observation | | Đã xác minh đúng project; chưa có child spans CP2. |
| Số PII leak | 0 do validator phát hiện | | Chỉ trên workload mẫu; chưa chứng minh scrubber hoàn chỉnh. |
| Latency P95 / TTFT P95 | 1098 ms / 50 ms | | Theo `/metrics` sau 10 request baseline. |
| Retrieval success rate | 100% (10/10 request thành công) | | Suy ra từ luồng retrieve và response_sent; chưa có span retrieval riêng. |

### Baseline CP0 — 29/09/2026

- **Trạng thái:** đạt CP0: health OK, có log và 10 trace mới trong project cá nhân.
- **Môi trường:** Windows, Python 3.11 trong `.venv`, thư viện cài theo `requirements.txt`; không sửa source ứng dụng trước khi đo.
- **API:** chạy `.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --env-file .env`. Sandbox Windows gặp `WinError 5` ở multiprocessing; chạy lại ngoài sandbox sau khi được cấp quyền.
- **Health:** `GET http://127.0.0.1:8000/health` trả HTTP 200, `ok: true`, `tracing_enabled: true`; cả ba incident đều `false`.
- **Workload:** `.\.venv\Scripts\python.exe scripts/load_test.py` dùng `data/sample_queries.jsonl`, concurrency mặc định 1; 10/10 HTTP 200, correlation ID đều `MISSING`. Root observations bắt đầu trong khoảng `2026-09-29T07:59:23.475Z`–`2026-09-29T07:59:27.830Z` (14:59:23–14:59:27 UTC+7).
- **Log:** `data/logs.jsonl` có 22 record khi validator chạy: 1 record cũ (07:50:44 UTC), 1 app_started mới và 20 record của 10 request. Validator chấm toàn bộ file: 20 record thiếu trường bắt buộc, 20 thiếu enrichment, 0 correlation ID hợp lệ, 0 PII leak phát hiện; điểm 30/100. Script vẫn trả exit code 0 dù score chưa đạt.
- **Các lệnh tiếp theo:** chạy lần lượt `python scripts/validate_logs.py`, `python scripts/validate_dashboard.py`, `python -m pytest -q` bằng Python trong `.venv`; kết quả ở bảng trên.
- **Metrics:** traffic 10; latency P50/P95/P99 = 399/1098/1098 ms; TTFT P95 = 50 ms; tokens in/out = 338/1141; tổng cost mô phỏng 0.0181 USD; quality trung bình 0.88; error breakdown rỗng.
- **Langfuse:** API projects xác nhận tên `day13-k4-l3a-2A202602488`, project ID `cmumd1s2900l9ad0dz0eloqz9`. `GET /api/public/v2/observations` trả HTTP 200 và 10 observations `lab-agent-run`, loại `AGENT`, cùng project ID và 10 trace IDs riêng biệt. Endpoint traces cũ trả 410 nên dùng observations v2 để xác minh. Đây là xác minh qua API, chưa phải ảnh dashboard/waterfall.
- **Bảo mật:** `.env`, `.venv/` và `data/logs.jsonl` được Git ignore và không được track. Không ghi API key hoặc nội dung request vào báo cáo; không commit trong bước baseline.

Trace IDs của lượt baseline:

```text
2a4c365f4f03636940c0d3d0bce31d59
ece364177e445902b866bd4060c8341c
639b8cb93171447b3c762503aa6ae146
dbcbafd3a4ce82950449c118d8ec4dfa
cf7efc3897ec599a4605b2629ddaf59e
9e4f837fe73d836658e444460265c1cc
4cf2bc377d7225cfd5a09420dad32cbc
416cede5b99ddac631f694facbd6498d
1d21f1d64ab7d175972cd7eba7370d13
172b4654c7e5dd9de30e32241b4ed71e
```

## 4. Logging và PII

- **Cách tạo/nhận và truyền correlation ID:**
- **Các metadata được ghi vào structured log:**
- **Cách bảo đảm PII được scrub trước khi ghi:**
- **Cách kiểm chứng kết quả:**

## 5. Tracing và prompt versioning

- **Cách xác nhận traces do chính tôi tạo trong project cá nhân:**
- **Cấu trúc root/retrieval/generation observations:**
- **Cách nối trace với log:**
- **Prompt name:**
- **Version/label baseline:**
- **Version/label candidate:**
- **Trace ID của mỗi version:**
- **Cách promote và rollback `production`:**

## 6. Dashboard, SLO và alerts

- **Dashboard và sáu panel:**
- **SLO và lý do chọn:**
- **Cách tính error budget:**
- **Ba alert và runbook tương ứng:**

## 7. Điều tra challenge

- **Challenge ID:**
- **Khoảng thời gian điều tra:**
- **Triệu chứng từ metrics:**
- **Log line và correlation ID liên quan:**
- **Trace ID và span gây ảnh hưởng:**
- **Root cause:**
- **Fix action:**
- **Preventive measure:**

## 8. Giải thích và tự đánh giá

- **Một quyết định kỹ thuật quan trọng và lý do:**
- **Một lỗi/blocker đã gặp:**
- **Cách tìm nguyên nhân và xử lý:**
- **Cách hiểu luồng Metrics → Logs → Traces:**
- **Vai trò của prompt version, token/cost, SLO hoặc rollback trong vận hành LLM:**
- **Điều quan trọng nhất đã học:**
- **Hạn chế hoặc phần chưa hoàn thành, nếu có:**

## 9. Checklist trước khi nộp

- [ ] Kết quả và evidence thuộc commit SHA cuối.
- [ ] Tất cả ảnh/output mở được bằng đường dẫn tương đối.
- [ ] Incident evidence nối đúng metric → log → trace.
- [ ] Trace/prompt evidence thuộc project Langfuse cá nhân và ảnh không lộ key/secret.
- [ ] Repository chạy lại được theo README.
- [ ] Không có secret, API key, PII thô hoặc evidence của người khác/lớp khác.
- [ ] URL repo và commit SHA cuối đã được nộp trên LMS/Codelabs.
