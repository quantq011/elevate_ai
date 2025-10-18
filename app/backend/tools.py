# backend/tools.py
from datetime import date, datetime, timedelta
from typing import Dict, Any, List
from collections import defaultdict

# Giả lập kho dữ liệu onboarding
POLICIES = {
    "leave": "New hires accrue 1.5 days/month. Submit on HR portal.",
    "it_access": "Submit Access Request Form; manager approval needed.",
    "security": "Complete Security 101 within 7 days."
}

# status: pending | in_progress | blocked | done
# priority: low | medium | high
TASKS: Dict[str, Dict[str, Any]] = {
    "NH-0001": {
        "title": "Submit I-9 / ID verification",
        "status": "pending",
        "owner": "hr.ops@corp.com",          # team chịu trách nhiệm giao việc
        "assignee": "new.hire@corp.com",     # người thực hiện (bạn)
        "due_date": "2025-10-25",            # YYYY-MM-DD
        "notes": "Bring passport to office or notary",
        "priority": "high",
        "tags": ["onboarding", "compliance"]
    },
    "NH-0002": {
        "title": "Request IT access (Email & VPN)",
        "status": "in_progress",
        "owner": "it.helpdesk@corp.com",
        "assignee": "new.hire@corp.com",
        "due_date": "2025-10-20",
        "notes": "Waiting for manager approval",
        "priority": "medium",
        "tags": ["it_access"]
    },
    "NH-0003": {
        "title": "Complete Security 101",
        "status": "pending",
        "owner": "security.team@corp.com",
        "assignee": "new.hire@corp.com",
        "due_date": "2025-10-22",
        "notes": "",
        "priority": "medium",
        "tags": ["training","security"]
    },
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

def _parse_date(s: str) -> date | None:
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None

def list_pending_tasks() -> List[Dict[str, Any]]:
    """Trả tất cả task còn pending/blocked/in_progress (chưa done)."""
    return [
        {"id": tid, **t}
        for tid, t in TASKS.items()
        if t.get("status") in {"pending", "blocked", "in_progress"}
    ]

def list_pending_by_user(email: str) -> List[Dict[str, Any]]:
    """Task chưa hoàn thành giao cho một người (assignee)."""
    email = (email or "").lower()
    return [
        {"id": tid, **t} for tid, t in TASKS.items()
        if (t.get("status") in {"pending", "blocked", "in_progress"})
        and (t.get("assignee","").lower() == email)
    ]

def summarize_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Tóm tắt: tổng quan, theo trạng thái, ưu tiên, quá hạn, sắp đến hạn."""
    today = date.today()
    by_status = defaultdict(list)
    by_priority = defaultdict(list)
    due_soon, overdue = [], []

    for t in tasks:
        by_status[t.get("status","unknown")].append(t)
        by_priority[t.get("priority","unknown")].append(t)
        d = _parse_date(t.get("due_date",""))
        if d:
            if d < today:
                overdue.append(t)
            elif (d - today).days <= 3:  # đến hạn trong 3 ngày
                due_soon.append(t)

    def _mini(items: List[Dict[str,Any]]) -> List[Dict[str,Any]]:
        # Rút gọn mỗi task chỉ còn thông tin chính để hiển thị
        out = []
        for t in items:
            out.append({
                "id": t["id"],
                "title": t["title"],
                "assignee": t.get("assignee"),
                "owner": t.get("owner"),
                "status": t.get("status"),
                "due_date": t.get("due_date"),
                "priority": t.get("priority"),
            })
        return out

    return {
        "total": len(tasks),
        "status_counts": {k: len(v) for k,v in by_status.items()},
        "priority_counts": {k: len(v) for k,v in by_priority.items()},
        "overdue": _mini(overdue),
        "due_soon": _mini(due_soon),
        "top_5": _mini(sorted(tasks, key=lambda x: (_parse_date(x.get("due_date","")) or date.max))[:5])
    }

def pretty_summarize(summary: Dict[str,Any]) -> str:
    """Chuẩn bị đoạn text tóm tắt đẹp để bot đọc ra."""
    lines = []
    lines.append(f"- Tổng số task đang mở: **{summary['total']}**")
    if summary["status_counts"]:
        sc = ", ".join(f"{k}: {v}" for k,v in summary["status_counts"].items())
        lines.append(f"- Theo trạng thái: {sc}")
    if summary["priority_counts"]:
        pc = ", ".join(f"{k}: {v}" for k,v in summary["priority_counts"].items())
        lines.append(f"- Theo ưu tiên: {pc}")

    if summary["overdue"]:
        lines.append("\n**Quá hạn:**")
        for t in summary["overdue"]:
            lines.append(f"  • {t['id']} — {t['title']} (assignee {t['assignee']}, due {t['due_date']})")

    if summary["due_soon"]:
        lines.append("\n**Sắp đến hạn (≤3 ngày):**")
        for t in summary["due_soon"]:
            lines.append(f"  • {t['id']} — {t['title']} (due {t['due_date']})")

    if summary["top_5"]:
        lines.append("\n**Top 5 gần nhất theo due date:**")
        for t in summary["top_5"]:
            lines.append(f"  • {t['id']} — {t['title']} ({t['status']}, due {t['due_date']})")

    return "\n".join(lines)
