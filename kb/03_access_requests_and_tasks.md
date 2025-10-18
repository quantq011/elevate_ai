# Access Requests & Provisioning Tasks (Mock)

> Dùng để test function-calling/các workflow cấp quyền, phụ thuộc phê duyệt, checklist thiết bị.

## 1) Access Matrix theo vai trò
```json
{
  "roles": {
    "Software Engineer I": {
      "systems": [
        {"name": "Email (SSO)", "group": "Employees", "requires": ["HRIS_created", "NDA_signed"]},
        {"name": "Slack", "workspace": "company", "requires": ["SSO"]},
        {"name": "GitHub", "org": "contoso", "teams": ["backend"], "requires": ["Security101_passed"]},
        {"name": "Jira", "project": "Core Platform", "role": "Developer"},
        {"name": "VPN", "requires": ["Security101_passed"]},
        {"name": "Azure AD", "groups": ["ENG-Readers", "ENG-Contrib"]}
      ]
    },
    "Product Designer": {
      "systems": [
        {"name": "Email (SSO)", "group": "Contractors"},
        {"name": "Slack", "workspace": "company"},
        {"name": "Figma", "team": "Product Design"},
        {"name": "Jira", "project": "Design System", "role": "Contributor"}
      ],
      "constraints": ["Không cấp GitHub mặc định cho Contractor"]
    },
    "HR Intern": {
      "systems": [
        {"name": "Email (SSO)", "group": "Interns"},
        {"name": "Slack", "workspace": "company"},
        {"name": "HRIS", "role": "ReadOnly"}
      ],
      "constraints": ["Không cấp VPN nếu không có lý do công việc"]
    }
  }
}
```

## 2) Checklist cấp phát thiết bị
```json
{
  "default_kit": ["Laptop", "Charger", "Monitor 24/27", "Docking", "Keyboard", "Mouse"],
  "optional": ["Headset ANC", "Webcam", "External SSD"],
  "mdm_required": true,
  "stock": {"Laptop": 5, "Monitor 24/27": 2, "Docking": 0}
}
```

## 3) Khoá học & tuân thủ
```json
{
  "trainings": [
    {"code": "SEC101", "title": "Security 101", "due_days": 7},
    {"code": "PRIV", "title": "Privacy & Data Handling", "due_days": 14},
    {"code": "COC", "title": "Code of Conduct", "due_days": 14}
  ],
  "must_complete_before": {
    "VPN": ["SEC101"],
    "GitHub": ["SEC101"]
  }
}
```

## 4) Quy trình phê duyệt
```json
{
  "approvals": [
    {"item": "Extra Monitor", "required_by": ["Manager", "IT"]},
    {"item": "Permanent WFH (probation)", "required_by": ["Manager", "HR"]},
    {"item": "VPN for Contractors", "required_by": ["Manager", "Security"]}
  ]
}
```
