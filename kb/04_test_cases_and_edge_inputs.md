# Test Cases & Edge Inputs

> Dùng để kiểm thử đa dạng tình huống (happy path, thiếu dữ liệu, vi phạm chính sách, quốc tế hoá, lỗi hệ thống).

## Danh sách trường hợp kiểm thử
```json
[
  {
    "id": "TC01",
    "title": "Happy path — FTE Engineer tại VN",
    "given": "Hồ sơ đầy đủ, start_date sắp tới, manager xác nhận",
    "input": {"employee_id": "E1001"},
    "expected": "Tạo email/SSO, cấp Slack/Jira/GitHub/VPN theo ma trận; đẩy Security 101; thiết bị default đủ stock."
  },
  {
    "id": "TC02",
    "title": "Thiếu manager_id",
    "given": "Hồ sơ E1003 thiếu manager",
    "input": {"employee_id": "E1003"},
    "expected": "Assistant yêu cầu bổ sung manager; chặn cấp quyền nhạy cảm cho đến khi có phê duyệt."
  },
  {
    "id": "TC03",
    "title": "Trùng email/phone",
    "given": "E1004 trùng email/phone với E1001",
    "input": {"employee_id": "E1004"},
    "expected": "Phát hiện duplicate; đề xuất hợp nhất hồ sơ hoặc yêu cầu sửa dữ liệu trước khi tiếp tục."
  },
  {
    "id": "TC04",
    "title": "Tên có dấu & ký tự đặc biệt",
    "given": "Le Thi Bich-Ngoc (Contractor)",
    "input": {"employee_id": "E1002"},
    "expected": "Xử lý chuẩn hoá slug/username; không cấp GitHub theo ràng buộc Contractor."
  },
  {
    "id": "TC05",
    "title": "Ngày bắt đầu sai định dạng",
    "given": "Input start_date = "15/12/2025"",
    "input": {"employee_patch": {"employee_id": "E1005", "start_date": "15/12/2025"}},
    "expected": "Assistant nhắc dùng ISO 8601 (YYYY-MM-DD); từ chối thao tác cho đến khi hợp lệ."
  },
  {
    "id": "TC06",
    "title": "Timezone khác quốc gia",
    "given": "E1003 location SG nhưng timezone VN",
    "input": {"employee_patch": {"employee_id": "E1003", "location.timezone": "Asia/Ho_Chi_Minh"}},
    "expected": "Cảnh báo sai timezone; đề xuất Asia/Singapore."
  },
  {
    "id": "TC07",
    "title": "WFH full-time trong thử việc",
    "given": "Chính sách giới hạn WFH ở probation",
    "input": {"request": {"type": "WFH", "employee_id": "E1001", "mode": "permanent"}},
    "expected": "Assistant giải thích chính sách; yêu cầu manager + HR phê duyệt nếu muốn ngoại lệ."
  },
  {
    "id": "TC08",
    "title": "Contractor xin VPN",
    "given": "Ràng buộc: VPN chỉ khi cần thiết",
    "input": {"request": {"type": "access", "employee_id": "E1002", "item": "VPN"}},
    "expected": "Yêu cầu mô tả nhu cầu; chuyển Security/Manager duyệt."
  },
  {
    "id": "TC09",
    "title": "Rehire — còn tài khoản cũ",
    "given": "Email cũ vẫn active",
    "input": {"employee_id": "E0909"},
    "expected": "Đề xuất re-enable & rotate credentials thay vì tạo mới; kiểm tra quyền cũ còn phù hợp."
  },
  {
    "id": "TC10",
    "title": "Intern pre-boarding",
    "given": "Start_date xa (E1005)",
    "input": {"employee_id": "E1005"},
    "expected": "Chỉ chuẩn bị tài liệu/đào tạo; chưa cấp VPN/hệ thống nhạy cảm đến sát ngày bắt đầu."
  },
  {
    "id": "TC11",
    "title": "Hết hàng thiết bị",
    "given": "Docking stock = 0",
    "input": {"request": {"type": "device", "employee_id": "E1001", "item": "Docking"}},
    "expected": "Đưa ETA hoặc phương án tạm thời; vẫn gán laptop/monitor."
  },
  {
    "id": "TC12",
    "title": "Thiếu NDA/Security101",
    "given": "Chưa hoàn tất điều kiện account_prereqs",
    "input": {"request": {"type": "access", "employee_id": "E1001", "item": "GitHub"}},
    "expected": "Chặn cấp GitHub; nhắc học SEC101 và ký NDA."
  },
  {
    "id": "TC13",
    "title": "Chuyển phòng ban sau khi đã cấp quyền",
    "given": "Từ Design sang Engineering",
    "input": {"employee_move": {"employee_id": "E1002", "to_department": "Engineering", "new_role": "UI Engineer"}},
    "expected": "Thu hồi quyền Figma Design-only; cấp GitHub/Jira tương ứng vai trò mới."
  },
  {
    "id": "TC14",
    "title": "Yêu cầu tuân thủ theo quốc gia",
    "given": "SG yêu cầu bổ sung form thuế",
    "input": {"employee_id": "E1003"},
    "expected": "Assistant thêm checklist tài liệu SG; lộ trình ký số trước cấp quyền tài chính."
  },
  {
    "id": "TC15",
    "title": "Trễ hạn đào tạo",
    "given": "SEC101 quá hạn 10 ngày",
    "input": {"employee_id": "E1001"},
    "expected": "Cảnh báo & escalations; tạm khoá GitHub/VPN cho đến khi hoàn thành."
  },
  {
    "id": "TC16",
    "title": "Thay đổi manager giữa chừng",
    "given": "Manager mới M2010",
    "input": {"employee_patch": {"employee_id": "E1001", "manager_id": "M2010"}},
    "expected": "Chuyển tất cả approval đang mở sang manager mới; log audit."
  },
  {
    "id": "TC17",
    "title": "Va chạm username/Slack handle",
    "given": "minh.anh đã tồn tại",
    "input": {"employee_id": "E1004"},
    "expected": "Đề xuất biến thể: minh.anh2 hoặc m.anh; thông báo cho người dùng."
  },
  {
    "id": "TC18",
    "title": "Giới hạn nhóm Azure AD vượt mức",
    "given": "User xin thêm nhiều nhóm ENG-*",
    "input": {"request": {"type": "access", "employee_id": "E1001", "item": "AzureAD", "groups": ["ENG-Readers","ENG-Contrib","ENG-Admin"]}},
    "expected": "Chặn ENG-Admin; yêu cầu justification + approval Security."
  },
  {
    "id": "TC19",
    "title": "Sự cố HRIS API",
    "given": "HRIS tạm thời lỗi 500",
    "input": {"action": "create_email", "employee_id": "E1001"},
    "expected": "Retry với backoff; fallback tạo ticket ITSM; thông báo trạng thái cho HR."
  },
  {
    "id": "TC20",
    "title": "Yêu cầu xoá PII theo GDPR",
    "given": "Cựu nhân viên gửi yêu cầu",
    "input": {"request": {"type": "privacy", "employee_id": "E0001", "action": "erase_PII"}},
    "expected": "Xác minh danh tính; thực thi quy trình xoá dữ liệu, ghi log kiểm toán."
  }
]
```
