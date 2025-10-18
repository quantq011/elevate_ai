# backend/topic_extractor.py
import os
from typing import Dict, Any
from openai import OpenAI

DEPLOYMENT = os.getenv("DEPLOYMENT_NAME", "gpt-4o-mini")

TOPIC_SCHEMA = {
  "type":"json_schema",
  "json_schema":{
    "name":"tech_topic",
    "schema":{
      "type":"object",
      "properties":{
        "topic":{"type":"string", "description":"canonical technology/topic in lowercase, e.g., 'angular', 'java spring boot', 'postgresql'"},
        "synonyms":{"type":"array","items":{"type":"string"}},
        "category":{"type":"string","description":"frontend/backend/devops/database/security/it"}
      },
      "required":["topic"]
    },
    "strict": True
  }
}

def extract_topic(client: OpenAI, question: str) -> Dict[str, Any]:
    """Use Structured Outputs to normalize the tech topic (Angular, Java Spring Boot, etc.)."""
    r = client.chat.completions.create(
        model=DEPLOYMENT,
        messages=[
            {"role":"system","content":"Extract the main technology/topic from the user question."},
            {"role":"user","content":question}
        ],
        response_format=TOPIC_SCHEMA
    )
    # SDK v1 provides parsed JSON
    return r.choices[0].message.parsed
