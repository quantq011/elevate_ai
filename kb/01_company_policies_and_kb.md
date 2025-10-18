# Company Policies (VN) — Bản rút gọn cho Onboarding Assistant

> Tài liệu dùng để seed nội dung cho trợ lý Onboarding (KB). Mọi dữ liệu bên dưới là **giả lập** phục vụ demo/test.

## 1) Mục đích & Phạm vi
- Chuẩn hoá các chính sách cốt lõi cho nhân viên mới (pre‑boarding → 90 ngày).
- Cung cấp đầu vào cho chatbot/assistant để trả lời **nhất quán** và **có nguồn**.
- Áp dụng cho nhân viên toàn thời gian (FTE), thực tập (Intern) và nhà thầu (Contractor).

## 2) Chính sách chung (rút gọn)
- **Thử việc:** 60 ngày.
- **Giờ làm việc:** 09:00–18:00, Thứ 2–Thứ 6; linh hoạt ±1 giờ theo quy định đội ngũ.
- **WFH trong thử việc:** tối đa **2 ngày/tuần**, cần quản lý duyệt trước.
- **Nghỉ phép năm (FTE):** 12 ngày/năm, tính prorate theo thời gian làm việc.
- **Bảo mật:** Hoàn thành khoá **Security 101** trong **7 ngày đầu**; ký **NDA** trước khi cấp quyền nhạy cảm.
- **Thiết bị:** Công ty cấp **01 laptop + 01 màn hình**. Thiết bị bổ sung cần quản lý + IT phê duyệt.
- **Tài khoản:** Email/SSO được cấp **sau khi HR tạo hồ sơ HRIS**. GitHub/VPN chỉ mở sau khi hoàn tất **SEC101**.
- **Kênh yêu cầu quyền:** gửi qua cổng ITSM: */access-requests* (mẫu chuẩn).

## 3) Quy tắc cấp quyền (prerequisites rút gọn)
- **Email/SSO:** yêu cầu *HRIS_created* + *NDA_signed*.
- **Slack/Jira:** mở sau khi có SSO; gán dự án/nhóm theo vai trò.
- **GitHub/VPN:** chỉ cấp sau khi hoàn tất **Security 101**.
- **Azure AD nhóm đặc biệt:** cần justification + phê duyệt của Security.

## 4) Quy trình & Kỷ luật (tóm tắt)
- **Vi phạm bảo mật** (chia sẻ mật khẩu, dữ liệu khách hàng…): khoá tài khoản tạm thời; yêu cầu học lại **SEC101**; xử lý theo nội quy.
- **Thiết bị hư hỏng/mất:** báo ngay IT (ticket) trong 24h; thực hiện quy trình bồi hoàn nếu do lỗi chủ quan.
- **Thay đổi thông tin cá nhân:** cập nhật qua HRIS; các hệ thống khác sẽ đồng bộ theo chu kỳ.

## 5) Câu hỏi thường gặp (FAQ rút gọn)
- **Đổi tên hiển thị email được không?** → Được, cần quản lý xác nhận; IT cập nhật trong 1 ngày.
- **WFH toàn thời gian trong thử việc?** → Không; chỉ tối đa 2 ngày/tuần và cần duyệt.
- **GitHub/VPN cấp khi nào?** → Sau khi bạn hoàn tất **Security 101**.
- **Nộp đơn nghỉ phép ở đâu?** → HRIS → Mục Leave; SLA phê duyệt 24 giờ làm việc.
- **Báo hỏng thiết bị thế nào?** → Tạo ticket ITSM → *hardware*; đính kèm hình ảnh/số serial.

## 6) Kênh liên hệ
- **HR Onboarding:** hr-onboarding@contoso.example · +84‑28‑9999‑0001
- **IT Helpdesk:** itsm@contoso.example · +84‑28‑9999‑0002
- **Security:** security@contoso.example
- **Facilities:** facilities@contoso.example

## 7) JSON seed (để Assistant/RAG dùng trực tiếp)
```json
{
  "policies": {
    "probation_days": 60,
    "wfh_probation_limit_days_per_week": 2,
    "annual_leave_days_fte": 12,
    "security_training_due_days": 7,
    "device_defaults": ["laptop", "monitor"],
    "account_prereqs": ["HRIS_created", "NDA_signed", "Security101_passed"]
  },
  "faq_snippets": [
    "WFH trong thử việc tối đa 2 ngày/tuần, cần quản lý duyệt.",
    "Email/SSO được cấp sau khi HRIS tạo hồ sơ.",
    "GitHub/VPN mở sau khi hoàn tất Security 101.",
    "Thiết bị mặc định: 1 laptop + 1 màn hình."
  ],
  "contacts": {
    "hr_onboarding": {"email": "hr-onboarding@contoso.example", "phone": "+842899990001"},
    "it_helpdesk": {"email": "itsm@contoso.example", "phone": "+842899990002"},
    "security": {"email": "security@contoso.example"},
    "facilities": {"email": "facilities@contoso.example"}
  }
}
```
