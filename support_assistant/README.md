# Support Assistant

8 Zepto policy docs → embedded (MiniLM, local TF-IDF fallback if unreachable) → ChromaDB
→ 3-node LangGraph intent router → Pydantic-validated JSON → FastAPI `POST /ask`.

## Run — local

```bash
pip install -r requirements.txt
python ingest.py
uvicorn main:app --host 0.0.0.0 --port 7860
# separate terminal:
curl -X POST http://localhost:7860/ask -H "Content-Type: application/json" -d '{"query": "What is the delivery fee?"}'
```

## Run — Google Colab

```python
!git clone <your-repo-url>
%cd zepto-data-ai-platform/support_assistant
!python ingest.py
```
Then, in a cell (this blocks, so it's the last thing you run in that cell):
```python
import subprocess, time
subprocess.Popen(["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7860"])
time.sleep(5)
```
Then in a **new** cell:
```python
!curl -X POST http://localhost:7860/ask -H "Content-Type: application/json" -d '{"query": "What is the delivery fee?"}'
```
No ngrok needed — both cells run on the same Colab VM, so `localhost` just works.

## Docker

```bash
docker build -t zepto-support-assistant .
docker run -p 7860:7860 zepto-support-assistant
```

## MOCK_LLM

Default (unset, or `MOCK_LLM=1`): fully deterministic, no LLM call — this is the graded
path. `MOCK_LLM=0`: optional extension, calls a real LLM (wire a provider into
`graph.py::_call_llm`, e.g. Groq's free tier) with retry-on-schema-failure built in.
Retrieval (ChromaDB) is real in both modes.

## Embedding note

The required path is `sentence-transformers/all-MiniLM-L6-v2`. If `huggingface.co` isn't
reachable (e.g. a locked-down network), `ingest.py` automatically falls back to a local
TF-IDF vectorizer so retrieval still works — no code changes needed either way; Colab has
full internet, so it'll use real MiniLM there automatically.

## Example calls (`MOCK_LLM` default — see `api_transcript.txt`)

**Policy question → `retrieve_and_answer` (retrieval triggered):**
```
POST /ask {"query": "What is the delivery fee?"}
{"answer": "Based on the retrieved context: Delivery Policy: Zepto delivers grocery and household essentials to serviceable pin codes within 10 to 30 minutes of order confirmation, depending on the customer's delivery zone and current order vol", "sources": ["doc_01", "doc_04", "doc_05"], "confidence": 1.0}
```
Top-retrieved source (`doc_01`) is the correct policy document.

**General question → `direct_answer` (no retrieval):**
```
POST /ask {"query": "What is the capital of France?"}
{"answer": "I can only answer questions about Zepto policies right now.", "sources": [], "confidence": 1.0}
```

## Architecture

**Ingestion** (`ingest.py::load_chunks`) — 1 chunk per doc (each policy is already a short,
self-contained paragraph). **Embedding** (`ingest.py::get_embedder`) — MiniLM or the TF-IDF
fallback, stored in ChromaDB (`chroma_db/`, collection `zepto_policies`). **Retrieval**
(`ingest.py::retrieve_top_k`, called from `graph.py`'s `retrieve_and_answer`) — top-3 by
cosine distance; real in both `MOCK_LLM` states. **Generation** — the *only* stage gated by
`MOCK_LLM`: mock mode returns a canned template/string with the schema populated in code;
`MOCK_LLM=0` builds a prompt from `prompts.py` and calls a real LLM, validated against
`AskResponse` with a 2-retry corrective loop. **Routing** — `classify_intent`'s keyword
heuristic feeds a LangGraph conditional edge to `retrieve_and_answer` or `direct_answer`;
routing itself doesn't depend on `MOCK_LLM`. **API** — `main.py`'s FastAPI app validates
request/response against the Pydantic schemas and calls `graph.py::ask()`.

```
query -> classify_intent -> [conditional edge]
             |-- policy_question  -> retrieve_and_answer -> AskResponse
             |-- general_question -> direct_answer       -> AskResponse
```

## Files

`docs/doc_01..08.txt` · `ingest.py` · `prompts.py` · `schemas.py` · `graph.py` · `main.py`
· `Dockerfile` · `api_transcript.txt`
