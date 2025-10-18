# backend/tools.py
from typing import Dict, Any

# Giả lập kho dữ liệu onboarding
POLICIES = {
    "leave": "New hires accrue 1.5 days/month. Submit on HR portal.",
    "it_access": "Submit Access Request Form; manager approval needed.",
    "security": "Complete Security 101 within 7 days."
}
TASKS = {
    "NH-0001": {"status": "pending", "title": "Submit I-9 / ID verification"},
}

def get_policy(topic: str) -> Dict[str, Any]:
    """Trả chính sách theo chủ đề."""
    text = POLICIES.get(topic.lower(), "No policy found for this topic.")
    return {"topic": topic, "policy": text}

def create_it_ticket(email: str, system: str, justification: str) -> Dict[str, Any]:
    """Tạo ticket IT truy cập hệ thống (giả lập)."""
    return {"ticket_id": "IT-" + email.split("@")[0].upper(), "system": system, "status": "OPEN"}

def check_task(task_id: str) -> Dict[str, Any]:
    """Kiểm tra tiến độ tác vụ onboarding."""
    return TASKS.get(task_id, {"status": "not_found"})
