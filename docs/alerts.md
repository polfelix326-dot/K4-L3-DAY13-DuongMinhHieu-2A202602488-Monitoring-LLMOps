# Template Alert và Runbook

Mỗi alert phải dựa trên triệu chứng người dùng hoặc SLO, không dựa trực tiếp vào tên implementation nội bộ.

## Alert 1

- Tên: HighErrorRate
- Severity: critical
- Duration: 5m
- Kênh thông báo: Slack (#alerts-llmops)
- SLI/SLO liên quan: Guardrail `error_rate_pct_max: 2` & availability SLI
- Điều kiện và thời gian duy trì: `error_rate_pct > 2` kéo dài liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng nhận mã lỗi HTTP 500 khi gọi `/chat`, hội thoại bị gián đoạn
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel Error rate & breakdown trên dashboard để xác định tỷ lệ lỗi và danh sách `error_type`.
  2. Tra cứu log `request_failed` trong `data/logs.jsonl` để lấy `correlation_id` và thông điệp lỗi trong `payload.detail`.
  3. Mở trace trên Langfuse theo `correlation_id` để xác định chính xác span bị throw exception (retrieval timeout hay LLM failure).
- Mitigation tạm thời: Kích hoạt circuit breaker / fallback answer cho API `/chat`; nếu do incident injection thì gọi endpoint `/incidents/{name}/disable` để phục hồi.
- Owner: oncall-engineer

## Alert 2

- Tên: HighLatencyP95
- Severity: warning
- Duration: 5m
- Kênh thông báo: Slack (#alerts-llmops)
- SLI/SLO liên quan: Primary SLO `fast_successful_requests` (latency P95 <= 3000ms trong window 28 ngày)
- Điều kiện và thời gian duy trì: `latency_p95_ms > 3000` kéo dài liên tục trong 5 phút
- Ảnh hưởng tới người dùng: Người dùng phải chờ đợi lâu để nhận được câu trả lời, có nguy cơ client timeout
- Ba bước kiểm tra đầu tiên:
  1. Kiểm tra panel Latency percentiles & TTFT trên dashboard để so sánh P50/P95/P99 và TTFT P95.
  2. Lọc log trong `data/logs.jsonl` tìm request có `latency_ms > 3000` để lấy `correlation_id`.
  3. Mở waterfall trace trên Langfuse để xem span nào chiếm phần lớn thời gian (span `retrieval` hay span `fake-llm-generation`).
- Mitigation tạm thời: Bật cache context retrieval, giảm timeout của vector retrieval hoặc scale thêm worker/thread pool xử lý.
- Owner: backend-team

## Alert 3

- Tên: DegradedRetrieval
- Severity: warning
- Duration: 10m
- Kênh thông báo: Slack (#alerts-llmops)
- SLI/SLO liên quan: Guardrail `retrieval_success_rate_pct_min: 90` & Quality score proxy
- Điều kiện và thời gian duy trì: `retrieval_success_rate_pct < 90` kéo dài liên tục trong 10 phút
- Ảnh hưởng tới người dùng: Mô hình không truy xuất được tài liệu phù hợp, câu trả lời bị chuyển sang fallback tổng quát, điểm chất lượng (`quality_score`) suy giảm
- Ba bước kiểm tra đầu tiên:
  1. Xem panel `errors` (đồ thị retrieval success rate) và panel `quality` trên dashboard.
  2. Tìm trong `data/logs.jsonl` các sự kiện `response_sent` có `tool_success == false` hoặc log `request_failed` có `tool_name == "retrieval"`.
  3. Kiểm tra trace Langfuse tìm span `retrieval` bị rỗng hoặc lỗi kết nối vector store.
- Mitigation tạm thời: Chuyển sang chế độ tìm kiếm keyword fallback trong `CORPUS`; restart vector search service hoặc vô hiệu hóa incident `tool_fail`.
- Owner: rag-team
