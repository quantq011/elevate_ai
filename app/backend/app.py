# backend/app.py
import os, json
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Body
from dotenv import load_dotenv
from openai import OpenAI
from .docstore import DocStore
from .contacts_store import ContactsStore

from .memory import ChatMemory
from .tools import (
    get_policy, create_it_ticket, check_task,
    list_pending_tasks, list_pending_by_user, summarize_tasks, pretty_summarize
)
from .topic_extractor import extract_topic

load_dotenv()

ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
DEPLOYMENT = os.getenv("DEPLOYMENT_NAME", "gpt-4o-mini")

client = OpenAI(
    api_key=API_KEY,
    base_url=f"{ENDPOINT}",
)

app = FastAPI(title="Onboarding Copilot API")

# đơn giản: mỗi tiến trình giữ 1 memory cho demo
MEM = ChatMemory(max_turns=30)
DOCS = DocStore(root="documents")
CONTACTS = ContactsStore(root="documents")

TOOLS_SPEC = [
    {
        "type": "function",
        "function": {
            "name": "get_policy",
            "description": "Get onboarding policy details by topic (e.g., leave, it_access, security).",
            "parameters": {
                "type": "object",
                "properties": {"topic": {"type": "string"}},
                "required": ["topic"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_it_ticket",
            "description": "Create an IT access ticket for a system.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {"type": "string"},
                    "system": {"type": "string"},
                    "justification": {"type": "string"},
                },
                "required": ["email", "system"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "check_task",
            "description": "Check onboarding task progress by task_id.",
            "parameters": {
                "type": "object",
                "properties": {"task_id": {"type": "string"}},
                "required": ["task_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_docs",
            "description": "Search markdown documents for onboarding/development/specifications/tasks.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "top_k": {"type": "number", "description": "Top results", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"lookup_contact",
            "description":"Find people by role and/or expertise area (e.g., role=IT Support, area=vpn or java spring boot).",
            "parameters":{
                "type":"object",
                "properties":{
                    "role":{"type":"string"},
                    "area":{"type":"string"}
                }
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"get_customer_info",
            "description":"Get customer info by name or domain.",
            "parameters":{
                "type":"object",
                "properties":{
                    "name":{"type":"string"},
                    "domain":{"type":"string"}
                }
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"suggest_support",
            "description":"Suggest the best support contacts for a given issue/system.",
            "parameters":{
                "type":"object",
                "properties":{
                    "issue":{"type":"string"},
                    "system":{"type":"string"}
                }
            }
        }
    },
    {
        "type":"function",
        "function":{
            "name":"get_it_contact",
            "description":"Return IT Helpdesk contact (email + hotline) from contacts documents.",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"list_pending",
            "description":"List all non-done onboarding tasks (pending/in_progress/blocked).",
            "parameters":{"type":"object","properties":{}}
        }
    },
    {
        "type":"function",
        "function":{
            "name":"list_my_pending",
            "description":"List non-done tasks for a specific assignee email.",
            "parameters":{
                "type":"object",
                "properties":{"email":{"type":"string"}},
                "required":["email"]
            }
        }
    }
]

SYSTEM_PROMPT = (
    "You are an Employee Onboarding Assistant. "
    "Answer clearly, cite policy names if available, and call tools for factual data. "
    "If data is missing (e.g., email), ask a brief follow-up."
    "For IT access/intake questions, FIRST provide the official IT contact channel "
    "(email + hotline) before asking for missing details. "
    "If user asks about development setup/specifications/tasks, prefer search_docs first."
    "For queries like 'pending tasks' or 'my pending tasks', call the appropriate tools "
    "and then present a concise summary (counts, overdue, due soon) before listing a few items."
    "If required info is missing (e.g., customer name not given), ask a brief follow-up."
    "Use tools for factual data."
    "For 'who to contact' or 'who supports X', prefer lookup_contact(area=topic)."
    "For customer details, prefer get_customer_info(name/domain)."
    "When the user asks who should support a technology topic (e.g., Angular, Java Spring Boot), "
    "First normalize the topic (use extract_topic helper in the backend), then call lookup_contact(area=<topic>)."
    "Only then, if the user wants to proceed with a ticket, collect email/system."
)

def _call_tool(name: str, args_json: str) -> Dict[str, Any]:
    args = json.loads(args_json or "{}")
    if name == "get_policy":
        return get_policy(**args)
    if name == "create_it_ticket":
        return create_it_ticket(**args)
    if name == "check_task":
        return check_task(**args)
    if name == "search_docs":
        return {"results": DOCS.search(args.get("query", ""), int(args.get("top_k", 5)))}
    if name == "lookup_contact":
        res = CONTACTS.find_people(**args)
        return {"people":[p.__dict__ for p in res]}
    if name == "get_customer_info":
        c = CONTACTS.find_customer(**args)
        return {"customer": c.__dict__ if c else None}
    if name == "suggest_support":
        res = CONTACTS.suggest_support(**args)
        return {"people":[p.__dict__ for p in res]}
    if name == "get_it_contact":
        # Pick the first 'Helpdesk' or IT person; prefer one with hotline
        best = None
        with_hotline = [p for p in CONTACTS.people if (getattr(p, "hotline", None)) and ("helpdesk" in p.role.lower() or "helpdesk" in p.name.lower())]
        if with_hotline:
            best = with_hotline[0]
        else:
            candidates = [p for p in CONTACTS.people if ("helpdesk" in p.role.lower() or "it" in (p.department or "").lower())]
            if candidates:
                best = candidates[0]
        if best:
            return {"email": best.email, "hotline": getattr(best, "hotline", None), "name": best.name, "role": best.role}
        return {"email": None, "hotline": None}
    if name == "list_pending":
        tasks = list_pending_tasks()
        return {"tasks": tasks, "summary": summarize_tasks(tasks), "pretty": pretty_summarize(summarize_tasks(tasks))}
    if name == "list_my_pending":
        tasks = list_pending_by_user(args.get("email",""))
        return {"tasks": tasks, "summary": summarize_tasks(tasks), "pretty": pretty_summarize(summarize_tasks(tasks))}
    return {"error": "unknown tool"}

def _chat_once(messages: List[Dict[str, Any]], tools=TOOLS_SPEC, tool_choice="auto"):
    """Gọi Chat Completions một lượt (có khai báo tools)."""
    return client.chat.completions.create(
        model=DEPLOYMENT,
        messages=messages,
        tools=tools,
        tool_choice=tool_choice
    )

@app.post("/chat")
def chat(payload: Dict[str, Any] = Body(...)):
    user_text: str = payload.get("message", "")
    session_id: Optional[str] = payload.get("session_id")  # nơi bạn map nhiều user
    # 1) nạp system + history + user
    msgs: List[Dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    msgs += MEM.history()
    msgs.append({"role": "user", "content": user_text})

    low = user_text.lower()
    if any(k in low for k in ["request it access", "it access", "access request", "quyền truy cập it", "yêu cầu truy cập it"]):
        # Force a tool call to read IT contact info from documents
        forced = [{"id":"get_it","type":"function","function":{"name":"get_it_contact","arguments":"{}"}}]
        patched = [
            {"role":"system","content":SYSTEM_PROMPT},
            {"role":"user","content":user_text},
            {"role":"assistant","content":"", "tool_calls": forced},
        ]
        result = _call_tool("get_it_contact", "{}")
        patched.append({"role":"tool","tool_call_id":"get_it","name":"get_it_contact","content": json.dumps(result)})
        # Finalize wording
        final = _chat_once(patched, tools=TOOLS_SPEC, tool_choice="auto")
        return {"answer": final.choices[0].message.content, "tool_calls": ["get_it_contact"]}
    
    pre_calls = []
    try:
        # very lightweight heuristic
        lower_q = user_text.lower()
        if "who" in lower_q and ("support" in lower_q or "owner" in lower_q or "phụ trách" in lower_q):
            topic = extract_topic(client, user_text)   # {'topic': 'java spring boot', 'synonyms': [...], ...}
            # seed a tool call to lookup_contact(area=<topic>)
            pre_calls = [{
                "id": "seed_lookup_contact",
                "type":"function",
                "function":{"name":"lookup_contact","arguments": json.dumps({"area": topic.get("topic")})}
            }]
            # add a synthetic assistant message that proposes the tool call
            msgs.append({"role":"assistant","content":"", "tool_calls": pre_calls})
            # execute immediately (patching pattern)
            tool_result = _call_tool("lookup_contact", json.dumps({"area": topic.get("topic")}))
            msgs.append({"role":"tool","tool_call_id":"seed_lookup_contact","name":"lookup_contact","content": json.dumps(tool_result)})

    except Exception:
        pass

    # 2) vòng đầu: để model quyết định tool_calls
    first = _chat_once(msgs)

    assistant_msg = first.choices[0].message
    MEM.add("user", user_text)
    # Lưu thông điệp assistant (kể cả tool_calls) để “patch”/vá tiếp
    MEM.add("assistant", assistant_msg.content or "", tool_calls=assistant_msg.tool_calls)

    # 3) Nếu có tool_calls → thực thi tuần tự và “vá” lại hội thoại
    tool_calls = assistant_msg.tool_calls or []
    patched_messages = [{"role": "user", "content": user_text},
                        {"role": "assistant", "content": assistant_msg.content or "",
                         "tool_calls": tool_calls}]
    for tc in tool_calls:
        result = _call_tool(tc.function.name, tc.function.arguments or "{}")
        patched_messages.append({
            "role": "tool",
            "tool_call_id": tc.id,
            "name": tc.function.name,
            "content": json.dumps(result)
        })
        # ghi vào memory để duy trì ngữ cảnh
        MEM.add("tool", json.dumps(result), name=tc.function.name, tool_call_id=tc.id)

    # 4) Gọi lượt cuối để model diễn giải kết quả tools
    final = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}] + MEM.history()
    )
    answer = final.choices[0].message.content
    MEM.add("assistant", answer)

    return {"answer": answer, "tool_calls": [tc.function.name for tc in tool_calls]}
