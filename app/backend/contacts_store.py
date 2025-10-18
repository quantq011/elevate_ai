# backend/contacts_store.py
import os, re, glob, yaml
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Person:
    name: str
    role: str
    email: str
    department: Optional[str] = None
    areas: List[str] = field(default_factory=list)
    timezone: Optional[str] = None
    languages: List[str] = field(default_factory=list)
    availability: Optional[str] = None
    source_path: Optional[str] = None

@dataclass
class Customer:
    name: str
    domain: Optional[str] = None
    account_manager: Optional[str] = None
    sla: Optional[str] = None
    timezone: Optional[str] = None
    contacts: List[Dict[str, Any]] = field(default_factory=list)
    source_path: Optional[str] = None

class ContactsStore:
    """
    Loads people, IT support, and customers defined via YAML frontmatter blocks
    inside Markdown files under documents/.
    Frontmatter blocks are delimited by lines starting with --- on their own.
    """
    def __init__(self, root: str = "documents"):
        self.root = root
        self.people: List[Person] = []
        self.customers: List[Customer] = []
        self._load_all()

    def _extract_frontmatter_blocks(self, text: str) -> List[Dict[str, Any]]:
        blocks = []
        # Allow multiple blocks scattered through the file
        for match in re.finditer(r"(?ms)^---\s*\n(.*?)\n---", text):
            raw = match.group(1)
            try:
                data = yaml.safe_load(raw) or {}
                blocks.append(data)
            except Exception:
                continue
        return blocks

    def _load_all(self):
        for path in glob.glob(os.path.join(self.root, "**", "*.md"), recursive=True):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                continue
            for data in self._extract_frontmatter_blocks(content):
                t = (data or {}).get("type", "").lower()
                if t == "person":
                    self.people.append(Person(
                        name=data.get("name",""),
                        role=data.get("role",""),
                        email=data.get("email",""),
                        department=data.get("department"),
                        areas=list(data.get("areas",[]) or []),
                        timezone=data.get("timezone"),
                        languages=list(data.get("languages",[]) or []),
                        availability=data.get("availability"),
                        source_path=path
                    ))
                elif t == "customer":
                    self.customers.append(Customer(
                        name=data.get("name",""),
                        domain=data.get("domain"),
                        account_manager=data.get("account_manager"),
                        sla=data.get("sla"),
                        timezone=data.get("timezone"),
                        contacts=list(data.get("contacts",[]) or []),
                        source_path=path
                    ))

    # --- Query helpers ---
    def find_people(self, role: Optional[str]=None, area: Optional[str]=None) -> List[Person]:
        res = self.people
        if role:
            res = [p for p in res if role.lower() in p.role.lower()]
        if area:
            res = [p for p in res if area.lower() in [a.lower() for a in p.areas]]
        return res

    def find_customer(self, name: Optional[str]=None, domain: Optional[str]=None) -> Optional[Customer]:
        if name:
            for c in self.customers:
                if c.name.lower() == name.lower():
                    return c
        if domain:
            for c in self.customers:
                if c.domain and c.domain.lower() == domain.lower():
                    return c
        return None

    def suggest_support(self, issue: str="", system: Optional[str]=None) -> List[Person]:
        # very simple heuristic: match by system/keyword in areas; fallback to IT Helpdesk
        key = (system or issue or "").lower()
        ranked = []
        for p in self.people:
            score = 0
            for a in p.areas:
                if a.lower() in key or key in a.lower():
                    score += 1
            if "it" in (p.department or "").lower():
                score += 0.5
            if score > 0:
                ranked.append((score, p))
        ranked.sort(key=lambda x: x[0], reverse=True)
        top = [p for _, p in ranked[:3]]
        # ensure Helpdesk always appears
        helpdesks = [p for p in self.people if "helpdesk" in p.role.lower() or "helpdesk" in p.name.lower()]
        for h in helpdesks:
            if h not in top:
                top.append(h)
        return top[:5]

