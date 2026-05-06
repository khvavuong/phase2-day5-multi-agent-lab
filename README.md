# Lab 20: Multi-Agent Research System

Repo bài lab **Multi-Agent Systems**: hệ thống nghiên cứu gồm **Supervisor + Researcher + Analyst + Writer + Critic**, benchmark với single-agent baseline, và tracing qua LangSmith.

> Trạng thái hiện tại: đã implement end-to-end workflow, benchmark command, và report markdown.

## Learning outcomes

Sau 2 giờ lab, học viên cần có thể:

1. Thiết kế role rõ ràng cho nhiều agent.
2. Xây dựng shared state đủ thông tin cho handoff.
3. Thêm guardrail tối thiểu: max iterations, timeout, retry/fallback, validation.
4. Trace được luồng chạy và giải thích agent nào làm gì.
5. Benchmark single-agent vs multi-agent theo quality, latency, cost.

## Architecture mục tiêu

```text
User Query
   |
   v
Supervisor / Router
   |------> Researcher Agent  -> research_notes
   |------> Analyst Agent     -> analysis_notes
   |------> Writer Agent      -> final_answer
   |
   v
Trace + Benchmark Report
```

## Cấu trúc repo

```text
.
├── src/multi_agent_research_lab/
│   ├── agents/              # Agent interfaces + skeletons
│   ├── core/                # Config, state, schemas, errors
│   ├── graph/               # LangGraph workflow skeleton
│   ├── services/            # LLM, search, storage clients
│   ├── evaluation/          # Benchmark/evaluation skeleton
│   ├── observability/       # Logging/tracing hooks
│   └── cli.py               # CLI entrypoint
├── configs/                 # YAML configs for lab variants
├── docs/                    # Lab guide, rubric, design notes
├── tests/                   # Unit tests for skeleton behavior
├── notebooks/               # Optional notebook entrypoint
├── scripts/                 # Helper scripts
├── .env.example             # Environment variables template
├── pyproject.toml           # Python project config
├── Dockerfile               # Containerized dev/runtime
└── Makefile                 # Common commands
```

## Quickstart

### 1. Tạo môi trường (Python 3.11)

```bash
python3.11 -m venv .venv
source .venv/bin/activate  # Windows: .venv\\Scripts\\activate
python -m pip install --upgrade pip setuptools wheel
python -m pip install -e ".[dev,llm]"
cp .env.example .env
```

### 2. Cấu hình API keys

Mở `.env` và điền key cần thiết:

```bash
OPENAI_API_KEY=...
TAVILY_API_KEY=...
LANGSMITH_TRACING=true
LANGSMITH_ENDPOINT=https://api.smith.langchain.com
LANGSMITH_API_KEY=...
LANGSMITH_PROJECT=Lab-Assignment-Phase2
```

### 3. Chạy smoke test

```bash
make test
python -m multi_agent_research_lab.cli --help
```

### 4. Chạy baseline

```bash
python -m multi_agent_research_lab.cli baseline \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

### 5. Chạy multi-agent

```bash
python -m multi_agent_research_lab.cli multi-agent \
  --query "Research GraphRAG state-of-the-art and write a 500-word summary"
```

### 6. Chạy benchmark và sinh report

```bash
python -m multi_agent_research_lab.cli benchmark
```

Hoặc custom query:

```bash
python -m multi_agent_research_lab.cli benchmark \
  -q "Research GraphRAG state-of-the-art and write a 300-word summary" \
  -q "Compare RAG and long-context models for enterprise QA" \
  -q "List top failure modes of tool-using AI agents and mitigations" \
  -o reports/benchmark_report.md
```

## Những phần đã làm

- Implement `LLMClient.complete` (OpenAI API, timeout, retry, token/cost capture).
- Implement `SearchClient.search` (Tavily API, retry, source mapping).
- Implement agents: `Supervisor`, `Researcher`, `Analyst`, `Writer`, `Critic`.
- Implement workflow run loop với guardrails (`max_iterations`, timeout, fallback khi lỗi).
- Tích hợp tracing local + LangSmith trong `observability/tracing.py`.
- Thêm benchmark command và markdown report renderer.
- Cập nhật tests để phản ánh behavior mới.

## Milestones lab (tham chiếu)

| Thời lượng | Milestone                         | File gợi ý                                            |
| ---------: | --------------------------------- | ----------------------------------------------------- |
|      0-15' | Setup, chạy baseline skeleton     | `cli.py`, `services/llm_client.py`                    |
|     15-45' | Build Supervisor / router         | `agents/supervisor.py`, `graph/workflow.py`           |
|     45-75' | Thêm Researcher, Analyst, Writer  | `agents/*.py`, `core/state.py`                        |
|     75-95' | Trace + benchmark single vs multi | `observability/tracing.py`, `evaluation/benchmark.py` |
|    95-115' | Peer review theo rubric           | `docs/peer_review_rubric.md`                          |
|   115-120' | Exit ticket                       | `docs/lab_guide.md`                                   |

## Quy ước production trong repo

- Tách rõ `agents`, `services`, `core`, `graph`, `evaluation`, `observability`.
- Không hard-code API key trong code.
- Tất cả input/output chính dùng Pydantic schema.
- Có type hints, linting, formatting, unit test tối thiểu.
- Có logging/tracing hook ngay từ đầu.
- Không để agent chạy vô hạn: dùng `max_iterations`, `timeout_seconds`.
- Có benchmark report thay vì chỉ demo output đẹp.

## TODO chính cho học viên (để tự rà soát)

Tìm trong code các marker:

```bash
grep -R "TODO(student)" -n src tests docs
```

Các phần cốt lõi đã được implement trong repo hiện tại:

1. LLM client.
2. Web/search client.
3. Routing decision trong Supervisor.
4. Worker agents.
5. Workflow orchestration.
6. LangSmith tracing hooks.
7. Benchmark report generation.

## Deliverables

Học viên nộp:

1. GitHub repo cá nhân.
2. Screenshot trace hoặc link trace.
3. Report benchmark: `reports/benchmark_report.md` (so sánh single vs multi-agent).
4. Design note: `docs/design_template.md`.
5. Failure mode và cách fix: trong phần `Failure Analysis` của `reports/benchmark_report.md`.

## References

- Anthropic: Building effective agents — https://www.anthropic.com/engineering/building-effective-agents
- OpenAI Agents SDK orchestration/handoffs — https://developers.openai.com/api/docs/guides/agents/orchestration
- LangGraph concepts — https://langchain-ai.github.io/langgraph/concepts/
- LangSmith tracing — https://docs.smith.langchain.com/
- Langfuse tracing — https://langfuse.com/docs
