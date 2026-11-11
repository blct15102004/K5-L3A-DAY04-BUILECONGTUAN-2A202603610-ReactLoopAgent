# Ghi chú phân tích · Day 04

Họ và tên: Bùi Lê Công Tuấn
MSSV: 2A202603610

## 1. Case được chọn

- ID case: `A2`
- Câu trả lời của agent ở lần 1:
  > "Incident wp49bp8bqo6c ghi nhận Cloudflare Cache Purge bị degraded. Tuy nhiên, thông báo đầu tiên nêu rõ: 'Non-fedramp customers are not impacted by this incident'. Do CLB không thuộc FedRAMP nên không bị ảnh hưởng bởi sự cố wp49bp8bqo6c này. Dù vậy, không thể loại trừ khả năng CLB gặp lỗi cache do cấu hình riêng hoặc nguyên nhân khác."
- Điểm ở lần chạy 1: **84/100** (Factuality: 38/40, Completeness: 22/25, Evidence: 10/20, Boundaries: 14/15).

## 2. Bằng chứng trong trace

Đoạn trace của case `A2` ở lần chạy 1:

```json
[
  {
    "event": "tool",
    "step": 1,
    "name": "get_status",
    "arguments": {
      "provider": "cloudflare",
      "component": "Cache Purge"
    },
    "result": {
      "provider": "cloudflare",
      "overall": {
        "status": "degraded"
      },
      "incidents": [
        {
          "id": "wp49bp8bqo6c",
          "name": "Cloudflare Cache Purge issues",
          "status": "investigating"
        }
      ]
    }
  },
  {
    "event": "tool",
    "step": 2,
    "name": "get_incident_details",
    "arguments": {
      "provider": "cloudflare",
      "incident_id": "wp49bp8bqo6c"
    },
    "result": {
      "ok": true,
      "id": "wp49bp8bqo6c",
      "url": "https://www.cloudflarestatus.com/incidents/wp49bp8bqo6c",
      "updates": [
        {
          "status": "investigating",
          "body": "Non-fedramp customers are not impacted by this incident."
        }
      ]
    }
  }
]
```

**Nguyên nhân có thể xảy ra:**
1. Agent đã gọi đúng 2 tool (`get_status` và `get_incident_details`) và phân tích chính xác nội dung trong bản cập nhật của incident (`Non-fedramp customers are not impacted by this incident`).
2. Tuy nhiên, khi tổng hợp câu trả lời cuối, model tập trung vào lập luận logic câu hỏi mà **bỏ quên việc trích dẫn trường `url`** của incident đã trích xuất từ tool (`https://www.cloudflarestatus.com/incidents/wp49bp8bqo6c`).
3. Thiếu URL nguồn cụ thể dẫn đến tiêu chí **Evidence** bị trừ 10 điểm (từ 20 xuống 10), nhận xét từ LLM Judge: *"Phân tích chính xác phạm vi FedRAMP và giới hạn suy đoán, nhưng thiếu URL nguồn incident được yêu cầu trong đề bài"*.

## 3. Thay đổi đã thực hiện

- **Sửa gì, ở đâu:**
  Triển khai cơ chế **Evidence Validation Gate** trong file `agent.py`:
  - Trong quá trình chạy tool loop, theo dõi và lưu trữ tất cả các URL sự cố từ các lệnh gọi `get_incident_details` thành công vào tập hợp `observed_urls`.
  - Khi model trả về phản hồi kết thúc (`not calls` và `finish == 'stop'`), kiểm tra xem câu trả lời cuối có chứa ít nhất một URL nguồn hợp lệ hay không.
  - Nếu thiếu URL, agent ghi event `validation_missing_source` vào `trace`, đồng thời gửi thêm một lượt phản hồi yêu cầu model bổ sung URL nguồn incident vào câu trả lời trước khi kết thúc (nếu vẫn còn trong ngân sách `max_steps`).
- **Vì sao chọn thay đổi này:**
  - Khắc phục triệt để hiện tượng model "quên" dẫn link nguồn dù đã có bằng chứng URL trong context.
  - Tận dụng sức mạnh của ReAct loop: agent tự giám sát hành vi của chính mình, tự phát hiện thiếu sót và tự yêu cầu chỉnh sửa (self-reflection & revision) trong giới hạn số bước cho phép mà không làm thay đổi các quy tắc an toàn khác.

## 4. So sánh hai lần chạy

| Chỉ số | `eval_before.json` | `eval_after.json` |
|---|---|---|
| Điểm tổng | 98.55 / 100 | 100.0 / 100 |
| Điểm case đã chọn (`A2`) | 84 / 100 | 100 / 100 |
| Số model calls | 55 calls | 57 calls |
| Token, chi phí nếu có | 31,997 tokens | 34,347 tokens |

- **Lỗi đã giải quyết:**
  - Case `A2`: Điểm tăng từ 84 lên 100. Agent tự động kích hoạt event `validation_missing_source` tại bước 3, yêu cầu bổ sung nguồn và nhận về câu trả lời hoàn chỉnh kèm link `https://www.cloudflarestatus.com/incidents/wp49bp8bqo6c`.
  - Case `A8`: Điểm tăng từ 84 lên 100 nhờ tự động kiểm tra và bổ sung đầy đủ URL cho cả 2 sự cố GitHub và Cloudflare.
- **Lỗi còn lại hoặc mới xuất hiện:**
  - Không có lỗi mới phát sinh. Chi phí token tăng nhẹ (+2,350 tokens, tương đương +2 model calls) do thêm các lượt sửa đổi nguồn (revision turn), đây là sự đánh đổi hoàn toàn hợp lý để đạt độ chính xác và tính xác thực bằng chứng 100%.

### Thử thách Bonus tùy chọn (`eval_bonus.json`):
- Đã hoàn thành mở rộng `agent.py` tương thích hoàn toàn với 5 status tools (GitHub, Cloudflare, Vercel, npm, DigitalOcean) qua `tools.schemas` và `tools.system_prompt`.
- Kết quả chạy trọn vẹn 10 case bonus trong `eval_bonus.json`: Đạt **100.0/100**, quy đổi điểm bonus đạt **15.0 / 15** điểm tối đa.
- Agent xử lý thành công: phục hồi sau 429 giả lập (`B3`), dừng retry sau 3 lần khi 429 kéo dài (`B4`), sửa tham số integer khi gặp `INVALID_ARGUMENTS` (`B5`), phân trang timeline incident (`B2`), lọc 160 bản ghi nhiễu (`B6`) và phòng chống prompt injection trong tool result (`B7`).

## 5. Giới hạn

- **Giới hạn của điểm judge:** Điểm số từ LLM Judge là ước lượng định lượng dựa trên rubric; judge có thể bị thiên lệch theo độ dài văn phong hoặc cùng provider tự chấm (self-bias), do đó điểm số cần được đối chiếu trực tiếp với bằng chứng cụ thể trong trace và checklist cơ học.
- **Giới hạn của snapshot:** Dữ liệu snapshot cố định tại ngày 09/11/2026 và chỉ chứa tối đa 50 sự cố gần nhất. Trạng thái "operational" trong snapshot chỉ phản ánh đúng tại thời điểm ghi dữ liệu, không đại diện cho tình trạng thời gian thực của các dịch vụ ở hiện tại.
- **Giới hạn của việc chạy một lần mỗi phiên bản:** Một lần chạy duy nhất của mỗi phiên bản chưa đủ để khẳng định hoàn toàn tính ổn định (variance) do nhiệt độ (temperature) của LLM có thể tạo ra dao động ngẫu nhiên giữa các lần sinh văn bản.
