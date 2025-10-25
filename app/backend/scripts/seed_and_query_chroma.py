"""Small smoke test for ChromaStore: seed default docs and run a search.
Run: python backend\scripts\seed_and_query_chroma.py
"""
from backend.chromastore import ChromaStore
from openai import OpenAI
import os

# minimal: create an OpenAI client if env vars present, else None
API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
client = None
if API_KEY and ENDPOINT:
    client = OpenAI(api_key=API_KEY, base_url=ENDPOINT)

cs = ChromaStore(openai_client=client) if client else ChromaStore()

# seed
docs = [
    {"id": "s1", "text": "How to request IT access? Use the portal and include justification.", "metadata": {"source": "faq"}},
    {"id": "s2", "text": "Onboarding checklist: create account, enable 2FA, join channels.", "metadata": {"source": "kb"}},
]
cs.upsert_documents(docs)
print("Seeded")

res = cs.query("how do i request access", top_k=3)
print("Query results:\n", res)
