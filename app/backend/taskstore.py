import re, os
from typing import Dict, Any

TASKS: Dict[str, Dict[str, Any]] = {
}

def load_tasks_from_markdown(path: str):
    """
    Parse dạng block đơn giản:
      - TASK: ...
        OWNER: ...
        ASSIGNEE: ...
        DUE: 2025-10-25
        STATUS: pending
        PRIORITY: high
    """
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    blocks = re.split(r"(?m)^\s*-\s*TASK:\s*", text)[1:]  # tách theo đầu dòng '- TASK:'
    for i, b in enumerate(blocks, start=1):
        lines = ["TASK: " + b.strip()]
        chunk = "\n".join(lines)

        def _field(key):
            m = re.search(rf"(?m)^{key}:\s*(.+)$", chunk)
            return m.group(1).strip() if m else ""

        tid = f"EXT-{i:04d}"
        TASKS[tid] = {
            "title": _field("TASK"),
            "status": (_field("STATUS") or "pending").lower(),
            "owner": _field("OWNER"),
            "assignee": _field("ASSIGNEE"),
            "due_date": _field("DUE"),
            "notes": _field("REASONS") or "",
            "priority": (_field("PRIORITY") or "medium").lower(),
            "tags": []
        }

# ví dụ sử dụng (khởi động app):
# load_tasks_from_markdown("documents/tasks/pending-tasks.md")
