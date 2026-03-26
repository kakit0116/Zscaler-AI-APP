import os
import re
import json
from typing import Dict, List, Optional

import requests
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

load_dotenv()

PROXY_URL = os.getenv("PROXY_URL", "https://proxy.us1.zseclipse.net/v1/chat/completions")
PROXY_API_KEY = os.getenv("PROXY_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4.1-mini")

FAISS_DIR = os.getenv("FAISS_DIR", "faiss_store")

app = FastAPI(title="Support Bot (Proxy ChatCompletions + FAISS RAG)")

# -------- Embeddings (LOCAL, no OpenAI) --------
# IMPORTANT: FAISS must be built with the same embedding model.
_embeddings = HuggingFaceEmbeddings(
    model_name=os.getenv("HF_EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
)

# -------- Load FAISS once --------
_vector_db = None
_faiss_index_file = os.path.join(FAISS_DIR, "index.faiss")
if os.path.isfile(_faiss_index_file):
    _vector_db = FAISS.load_local(
        FAISS_DIR,
        _embeddings,
        allow_dangerous_deserialization=True,
    )
else:
    print(f"⚠️ FAISS index not found at {_faiss_index_file}. RAG disabled until ingest runs.")

# -------- Models --------
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    product: Optional[str] = None  # "ZPA"/"ZIA"/None
    context: Optional[str] = None

class ChatResponse(BaseModel):
    answer: str

# -------- Domain router (controls only whether we inject Zscaler docs) --------
ZSCALER_HINTS = [
    r"\bzscaler\b", r"\bzia\b", r"\bzpa\b", r"\bzdx\b", r"\bzcc\b", r"\bzcp\b",
    r"app\s*segment", r"\bconnector\b", r"service\s*edge", r"zscaler client connector",
    r"ssl\s*inspection", r"forwarding\s*profile", r"\bpac\b", r"\bnss\b",
    r"private\s*access", r"internet\s*access",
]

def is_zscaler_related(text: str) -> bool:
    t = (text or "").lower()
    return any(re.search(p, t) for p in ZSCALER_HINTS)

# -------- Tools (demo + optional web_search) --------
def kb_search(query: str) -> List[Dict[str, str]]:
    return [
        {
            "title": "ZPA Connector Health Checklist",
            "snippet": "Check outbound 443, DNS, upgrades, service reachability.",
            "url": "internal://kb/zpa-connector-health",
        },
        {
            "title": "ZIA SSL Inspection Troubleshooting",
            "snippet": "Verify cert deployment, bypass rules, trust store.",
            "url": "internal://kb/zia-ssl-inspection",
        },
    ]

def status_check() -> Dict[str, str]:
    return {"status": "unknown", "note": "Hook this to your preferred status source."}

def web_search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
    api_key = os.getenv("TAVILY_API_KEY", "")
    if not api_key:
        return [{"title": "Search not configured", "url": "", "snippet": "Set TAVILY_API_KEY to enable web_search."}]

    from tavily import TavilyClient
    tv = TavilyClient(api_key=api_key)
    res = tv.search(query=query, max_results=max_results)

    out: List[Dict[str, str]] = []
    for r in (res.get("results") or [])[:max_results]:
        out.append({
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "snippet": (r.get("content") or "")[:450],
        })
    return out

# NOTE: Chat Completions tool schema uses {"type":"function","function":{...}}
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "kb_search",
            "description": "Search internal Zscaler KB and return relevant articles.",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "status_check",
            "description": "Check service status (Zscaler or internal services).",
            "parameters": {"type": "object", "properties": {}, "required": [], "additionalProperties": False},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "web_search",
            "description": "Search the internet for any topic and return top results with snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "max_results": {"type": "integer", "minimum": 1, "maximum": 10, "default": 5},
                },
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
]

# -------- RAG retrieval --------
def retrieve_context(user_query: str, product: Optional[str] = None, k: int = 5) -> str:
    if _vector_db is None:
        return ""

    q = user_query if not product else f"[{product}] {user_query}"
    docs = _vector_db.similarity_search(q, k=k)

    lines = []
    for i, d in enumerate(docs, start=1):
        src = d.metadata.get("source", "unknown")
        snippet = d.page_content.strip().replace("\n", " ")
        if len(snippet) > 450:
            snippet = snippet[:450] + "..."
        lines.append(f"[S{i}] Source: {src}\n{snippet}\n")
    return "\n".join(lines)

# -------- Proxy call (Chat Completions style) --------
def proxy_chat(messages: List[Dict], tools: Optional[List[Dict]] = None) -> Dict:
    if not PROXY_API_KEY:
        raise RuntimeError("PROXY_API_KEY is not set. Put it in .env or container env vars.")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PROXY_API_KEY}",
        "X-Apikey": PROXY_API_KEY,  # Keep for backwards compatibility
    }

    payload: Dict = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.2,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    r = requests.post(PROXY_URL, headers=headers, json=payload, timeout=180)
    
    if r.status_code == 403:
        # AI Guard may block certain content - return friendly message
        return {
            "choices": [{
                "message": {
                    "content": "I'm unable to process this request. The content may have been blocked by security policies. Please try rephrasing your question.",
                    "role": "assistant"
                }
            }]
        }
    
    r.raise_for_status()
    return r.json()

def run_agent(user_text: str, product: Optional[str], extra_context: Optional[str]) -> str:
    use_rag = is_zscaler_related(user_text) or (product in ("ZPA", "ZIA"))
    rag_context = retrieve_context(user_text, product=product, k=5) if use_rag else ""

    system = (
        "You are a helpful assistant.\n"
        "When the user asks about Zscaler (ZIA/ZPA/ZDX/ZCC), prefer the provided "
        "'Relevant internal context' snippets and cite them like [S1], [S2].\n"
        "When the question is NOT about Zscaler, answer normally using general knowledge. "
        "If you need up-to-date facts, use the web_search tool.\n"
        "Do not invent citations—only cite [S#] when those snippets are provided."
    )

    messages: List[Dict] = [{"role": "system", "content": system}]

    if product:
        messages.append({"role": "user", "content": f"Product focus: {product}"})

    if rag_context:
        messages.append({"role": "user", "content": f"Relevant internal context:\n{rag_context}"})

    if extra_context:
        messages.append({"role": "user", "content": f"User-provided context:\n{extra_context}"})

    messages.append({"role": "user", "content": user_text})

    # 1st call
    resp = proxy_chat(messages, tools=TOOLS)
    msg = (resp.get("choices") or [{}])[0].get("message") or {}
    content = (msg.get("content") or "").strip()
    tool_calls = msg.get("tool_calls") or []

    if not tool_calls:
        return content or "No answer returned."

    # Tool loop (max 3)
    for _ in range(3):
        tool_outputs = []

        for tc in tool_calls:
            fn = (tc.get("function") or {})
            name = fn.get("name", "")
            args_raw = fn.get("arguments", "{}")

            try:
                args = json.loads(args_raw) if isinstance(args_raw, str) else (args_raw or {})
            except json.JSONDecodeError:
                args = {}

            if name == "kb_search":
                result = kb_search(args.get("query", user_text))
            elif name == "status_check":
                result = status_check()
            elif name == "web_search":
                result = web_search(args.get("query", user_text), int(args.get("max_results", 5)))
            else:
                result = {"error": f"Unknown tool: {name}"}

            tool_outputs.append({
                "role": "tool",
                "tool_call_id": tc.get("id"),
                "content": json.dumps(result),
            })

        # Feed back assistant tool-call message + tool outputs
        messages.append(msg)
        messages.extend(tool_outputs)

        resp = proxy_chat(messages, tools=TOOLS)
        msg = (resp.get("choices") or [{}])[0].get("message") or {}
        content = (msg.get("content") or "").strip()
        tool_calls = msg.get("tool_calls") or []

        if not tool_calls:
            return content or "No final answer returned."

    return content or "No final answer returned after tool loop."

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    answer = run_agent(req.message, req.product, req.context)
    return ChatResponse(answer=answer)

