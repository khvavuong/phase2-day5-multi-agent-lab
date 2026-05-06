# Benchmark Report

| Run            | Latency (s) | Cost (USD) | Quality | Citation Coverage | Failure Rate | Notes                                                                  |
| -------------- | ----------: | ---------: | ------: | ----------------: | -----------: | ---------------------------------------------------------------------- |
| baseline_q1    |        5.94 |     0.0002 |     6.0 |                   |         0.00 | errors=0, routes=[]                                                    |
| multi_agent_q1 |       11.75 |     0.0011 |    10.0 |              1.00 |         0.00 | errors=0, routes=['researcher', 'analyst', 'writer', 'critic', 'done'] |
| baseline_q2    |        9.74 |     0.0004 |     6.0 |                   |         0.00 | errors=0, routes=[]                                                    |
| multi_agent_q2 |       19.24 |     0.0012 |    10.0 |              1.00 |         0.00 | errors=0, routes=['researcher', 'analyst', 'writer', 'critic', 'done'] |
| baseline_q3    |       14.85 |     0.0004 |     6.0 |                   |         0.00 | errors=0, routes=[]                                                    |
| multi_agent_q3 |       16.48 |     0.0014 |    10.0 |              1.00 |         0.00 | errors=0, routes=['researcher', 'analyst', 'writer', 'critic', 'done'] |

## Failure Analysis

Một failure mode quan trọng là khi `Researcher` thu thập nguồn chất lượng thấp hoặc không liên quan, `Analyst` và `Writer` vẫn có thể tạo ra câu trả lời trông hợp lý nhưng nền tảng bằng chứng yếu, dẫn tới rủi ro hallucination ở mức "nghe có vẻ đúng". Cách fix thực tế là thêm lớp lọc nguồn ngay sau bước search (lọc theo domain uy tín, score tối thiểu, và loại trùng lặp), đồng thời bắt buộc `Critic` kiểm citation coverage và cảnh báo claim không có nguồn; nếu coverage thấp hơn ngưỡng thì workflow nên fallback về route `researcher` để thu thập lại nguồn trước khi chốt `final_answer`.
