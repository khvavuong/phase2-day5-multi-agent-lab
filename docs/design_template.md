# Design Template

## Problem

Xây dựng research assistant nhận query dài, thu thập nguồn tin, phân tích điểm đồng thuận/mâu thuẫn, và viết câu trả lời cuối có citation để giảm hallucination.

## Why multi-agent?

Single-agent thường trộn lẫn tìm kiếm, phân tích và viết trong một lần gọi nên khó debug và khó kiểm soát chất lượng từng bước. Multi-agent giúp tách nhiệm vụ theo role, tăng khả năng trace/fallback, và benchmark được chi phí-chất lượng rõ ràng.

## Agent roles

| Agent | Responsibility | Input | Output | Failure mode |
|---|---|---|---|---|
| Supervisor | Quyết định agent tiếp theo và điều kiện dừng | `ResearchState` | Route (`researcher/analyst/writer/critic/done`) | Loop quá nhiều vòng nếu policy kém |
| Researcher | Gọi search API, lọc nguồn, tạo research notes | Query, max_sources | `sources`, `research_notes` | Không có nguồn hoặc nguồn nhiễu |
| Analyst | Biến notes thành claim/điểm yếu bằng chứng | Query + research_notes | `analysis_notes` | Tóm tắt sai trọng tâm |
| Writer | Tổng hợp câu trả lời cuối có nguồn tham chiếu | Query + research + analysis | `final_answer` | Thiếu citation hoặc trả lời mơ hồ |
| Critic | Chấm citation coverage và cảnh báo chất lượng | final_answer + sources | Critic note trong `agent_results` | Cảnh báo heuristic chưa đủ sâu |

## Shared state

Các field chính: `request`, `iteration`, `route_history`, `sources`, `research_notes`, `analysis_notes`, `final_answer`, `agent_results`, `trace`, `errors`.

Lý do: đủ để handoff giữa agent, replay luồng chạy, debug failure, và tính benchmark metrics.

## Routing policy

`supervisor -> researcher -> analyst -> writer -> critic -> done`

Điều kiện:
- Nếu chưa có `research_notes` hoặc `sources` trống: đi `researcher`.
- Nếu chưa có `analysis_notes`: đi `analyst`.
- Nếu chưa có `final_answer`: đi `writer`.
- Nếu chưa chạy critic: đi `critic`.
- Nếu đạt `max_iterations` hoặc timeout: dừng/fallback.

## Guardrails

- Max iterations: dùng `MAX_ITERATIONS` từ settings.
- Timeout: dùng `TIMEOUT_SECONDS` cho workflow và API calls.
- Retry: retry exponential cho LLM/Search API (3 attempts).
- Fallback: khi lỗi nhiều, supervisor ưu tiên route writer hoặc done để tránh loop.
- Validation: dùng Pydantic schemas cho request/source/metrics.

## Benchmark plan

Query đề xuất:
1. "Research GraphRAG state-of-the-art and write a 500-word summary"
2. "Compare RAG vs long-context models for enterprise QA"
3. "What are current failure modes of tool-using AI agents?"

Metrics:
- Latency (seconds)
- Estimated cost (USD)
- Quality score (0-10, heuristic + peer review)
- Citation coverage (0-1)
- Failure rate (0-1)

Expected outcome:
- Multi-agent có citation coverage và quality ổn định hơn baseline.
- Baseline thường nhanh hơn nhưng dễ thiếu traceability và citation discipline.
