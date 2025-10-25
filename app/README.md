# employee-chatbot

## ChromaDB integration

This project includes an optional ChromaDB vector store integration for storing and searching embeddings.

Quick start:

- Install dependencies (in your environment):

  pip install -r requirements.txt

- Or using pyproject.toml with your tooling (pip, pipx, or poetry). Ensure `chromadb` and `openai` are installed.

- Seed mock data (from project root):

  python backend\scripts\seed_and_query_chroma.py

- Start the API and use endpoints:

  - POST /chroma/seed to seed documents (body: {docs: [...]})
  - GET /chroma/search?q=your+query to search the Chroma store

Note: The ChromaStore uses an in-memory Chroma instance by default. For embeddings, set Azure OpenAI environment
variables (AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY) so the provided OpenAI client can compute embeddings.

# Onboarding Assistant – FastAPI × Streamlit (Azure OpenAI, uv)

A small demo chatbot for **employee onboarding** that answers policy questions, searches your Markdown docs (development/specifications/tasks), and calls tools (e.g., create IT ticket, check task).

---

## 1) Prerequisites

- Python **3.11+**
- An Azure OpenAI deployment (e.g., `gpt-4o`)
- (Optional) Git

---

## 2) Install `uv`

```bash
# Linux/macOS
curl -LsSf https://astral.sh/uv/install.sh | sh
# Windows PowerShell
powershell -ExecutionPolicy Bypass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Verify:
```bash
uv --version
```

---

## 3) Project setup

```bash
# clone or copy your project
git clone <your-repo> onboarding-bot
cd onboarding-bot

# install dependencies from pyproject.toml
uv sync
```

Create `.env` from the sample:

```bash
cp .env.example .env
```

Edit `.env`:

```dotenv
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com
AZURE_OPENAI_API_KEY=xxxxxxxxxxxxxxxxxxxxxxxx
DEPLOYMENT_NAME=gpt-4o
```

---

## 4) Documents (Markdown data source)

Put your Markdown files in `documents/`:

```
documents/
├─ development/
│  ├─ setup-environment-angular.md
│  ├─ setup-environment-spring-boot.md
│  ├─ setup-environment-postgresql.md
│  ├─ setup-ms-sql.md
│  ├─ setup-aws-basic.md
│  └─ jenkins-cicd.md
├─ specifications/
│  ├─ onboarding-user-stories.md
│  └─ access-request-user-stories.md
└─ tasks/
   ├─ current-tasks.md
   └─ pending-tasks.md
```

*Tip:* The bot has a tool `search_docs` that scans these files and cites the file path in answers.

---

## 5) Run the backend (FastAPI)

```bash
uv run uvicorn backend.app:app --reload --port 8000
```

- API: `POST http://localhost:8000/chat`
- Body: `{ "message": "<your question>" }`
- Returns: `{ "answer": "...", "tool_calls": [...] }`

---

## 6) Run the frontend (choose one)

### A) Streamlit

```bash
uv run streamlit run frontend/streamlit_app.py
```

Open the link shown by Streamlit (usually http://localhost:8501).

### B) Gradio (optional)

```bash
uv run python frontend/gradio_app.py
```

Open the Gradio URL shown in terminal.

---

## 7) Quick start – send a prompt (examples)

Try these right away in the UI (or POST to `/chat`):

- **Policy:**  
  *“What’s the new-hire security training requirement?”*  
  *“How do I request IT access?”*

- **Development docs (Markdown search):**  
  *“Show me how to set up Angular environment.”*  
  *“How to set up Postgresql locally?”*  
  *“Summarize pending onboarding tasks and owners.”*

- **Tool calling:**  
  *“Create an IT access ticket for VPN for email=jane@corp.com with justification ‘remote onboarding’.”*  
  *“Check progress of task NH-0001.”*

- **Mixed:**  
  *“List pending tasks and suggest who to reassign if the owner is on leave.”*

---

## 8) Run locally with a single command (optional)

If you prefer separate terminals:

```bash
# Terminal 1
uv run uvicorn backend.app:app --reload --port 8000

# Terminal 2
uv run streamlit run frontend/streamlit_app.py
```

---

## 9) Project structure (reference)

```
onboarding-bot/
├─ pyproject.toml
├─ .env.example
├─ .env                # (you create)
├─ documents/          # (your Markdown)
│  ├─ development/ …
│  ├─ specifications/ …
│  └─ tasks/ …
├─ backend/
│  ├─ app.py           # FastAPI, tool calling, message management
│  ├─ tools.py         # get_policy, create_it_ticket, check_task, etc.
│  ├─ memory.py        # simple chat history
│  └─ docstore.py      # loads & searches Markdown
└─ frontend/
   ├─ streamlit_app.py
   └─ gradio_app.py
```

---

## 10) Troubleshooting

- **401/403**: check `AZURE_OPENAI_API_KEY`, endpoint URL, and that your model deployment name matches `DEPLOYMENT_NAME`.  
- **No citations from docs**: confirm files exist under `documents/` and contain relevant keywords.  
- **Prompt hangs**: verify backend is running on `http://localhost:8000`.  
- **Model not found**: ensure you deployed (e.g., `gpt-4o`) in Azure AI Studio.

---

## 11) Notes

- This demo uses **Chat Completions + tool calling** and a simple in-process memory.  
- You can swap the simple Markdown search with BM25/embeddings later without changing the tool interface.  
- For production, add auth (e.g., Microsoft Entra ID), structured outputs for forms, logging, and rate limiting.
