# Employee Profiles (Mock Seed)

> Bộ dữ liệu nhân sự đầu vào để test các luồng: tạo tài khoản, cấp thiết bị, phân quyền, tính SLA.

## JSON
```json
[
  {
    "employee_id": "E1001",
    "full_name": "Nguyễn Thị Minh Anh",
    "preferred_name": "Minh Anh",
    "email": "minh.anh@contoso.example",
    "phone": "+84901234567",
    "department": "Engineering",
    "role": "Software Engineer I",
    "employment_type": "FTE",
    "manager_id": "M2001",
    "start_date": "2025-11-03",
    "location": {"city": "TP.HCM", "country": "VN", "timezone": "Asia/Ho_Chi_Minh"},
    "device_preferences": {"laptop": "MacBook Pro 14 M3", "monitor": "27inch"},
    "shirt_size": "M"
  },
  {
    "employee_id": "E1002",
    "full_name": "Le Thi Bich-Ngoc",
    "preferred_name": "Ngoc",
    "email": "ngoc.le@contoso.example",
    "phone": "+84345556666",
    "department": "Design",
    "role": "Product Designer",
    "employment_type": "Contractor",
    "manager_id": "M2002",
    "start_date": "2025-10-28",
    "location": {"city": "Ha Noi", "country": "VN", "timezone": "Asia/Ho_Chi_Minh"},
    "device_preferences": {"laptop": "ThinkPad T14", "monitor": "24inch"},
    "shirt_size": "S"
  },
  {
    "employee_id": "E1003",
    "full_name": "Tran Van A",
    "preferred_name": "A Tran",
    "email": "tran.va@contoso.example",
    "phone": "+12025550123",
    "department": "Data",
    "role": "Data Analyst",
    "employment_type": "FTE",
    "manager_id": null,
    "start_date": "2025-10-20",
    "location": {"city": "Singapore", "country": "SG", "timezone": "Asia/Singapore"},
    "device_preferences": {"laptop": "MacBook Air 13 M3"},
    "shirt_size": "L"
  },
  {
    "employee_id": "E1004",
    "full_name": "Nguyen Thi Minh Anh",
    "preferred_name": "Minh A.",
    "email": "minh.anh@contoso.example",
    "phone": "+84901234567",
    "department": "Engineering",
    "role": "Software Engineer I",
    "employment_type": "FTE",
    "manager_id": "M2001",
    "start_date": "2025-11-03",
    "location": {"city": "TP.HCM", "country": "VN", "timezone": "Asia/Ho_Chi_Minh"},
    "device_preferences": {},
    "shirt_size": "M"
  },
  {
    "employee_id": "E1005",
    "full_name": "Lê Trần Thùy Dương",
    "preferred_name": "Dương",
    "email": "le.duong@contoso.example",
    "phone": "0901234567",
    "department": "People Ops",
    "role": "HR Intern",
    "employment_type": "Intern",
    "manager_id": "M2003",
    "start_date": "2025-12-15",
    "location": {"city": "TP.HCM", "country": "VN", "timezone": "Asia/Ho_Chi_Minh"},
    "device_preferences": {"laptop": "MacBook Air 13 M2"},
    "shirt_size": "XS"
  }
]
```
### Ghi chú edge-cases
- **E1003:** thiếu `manager_id` (thiếu thông tin bắt buộc).
- **E1004:** email & phone trùng với E1001 (trùng lặp/duplicate), tên có biến thể.
- **E1005:** thực tập sinh, ngày bắt đầu xa (kích hoạt pre-boarding).
