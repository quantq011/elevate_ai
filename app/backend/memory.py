# backend/memory.py
from collections import deque
from typing import Deque, List, Dict, Any

class ChatMemory:
    """Bộ nhớ hội thoại per-session, giới hạn token thô theo số turns."""
    def __init__(self, max_turns: int = 20):
        self.max_turns = max_turns
        self.messages: Deque[Dict[str, Any]] = deque()

    def add(self, role: str, content: Any, **kwargs):
        self.messages.append({"role": role, "content": content, **kwargs})
        while len(self.messages) > self.max_turns:
            self.messages.popleft()

    def history(self) -> List[Dict[str, Any]]:
        return list(self.messages)
