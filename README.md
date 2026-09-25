<<<<<<< HEAD

# Capstone_Masai
=======
# Zepto Data & AI Platform

One repo, three modules: [`/data_pipeline`](./data_pipeline) (25) — scrape → clean → convert
→ SQLite → SQL/pandas queries. [`/analytics`](./analytics) (50) — Titanic EDA + full
classification/regression modeling pipeline. [`/support_assistant`](./support_assistant)
(25) — RAG assistant (ChromaDB + LangGraph + FastAPI) over Zepto's own policy docs.

Every module runs identically **locally or in Google Colab** — each entry script detects
Colab (`"google.colab" in sys.modules`) and auto-installs its own `requirements.txt`, so
there's no separate setup step on Colab beyond `!git clone` and `%cd`.

## Setup — local

Each module has its own `requirements.txt` (kept separate since the three modules share
almost no dependencies):

```bash
pip install -r data_pipeline/requirements.txt
pip install -r analytics/requirements.txt
pip install -r support_assistant/requirements.txt
```

## Setup — Google Colab

No local install step needed — clone once, `%cd` into whichever module, and run its
scripts; each one installs what it needs on first run:

```python
!git clone <your-repo-url>
%cd zepto-data-ai-platform/data_pipeline   # or /analytics, /support_assistant
```

See each module's own README for its exact run commands (they're identical between local
and Colab except for the `!git clone`/`%cd` cell).

## Run everything end to end

```bash
cd data_pipeline && python scrape.py && python clean_and_load.py && python queries.py && cd ..
cd analytics && python 01_eda.py && python 02_modeling.py && cd ..
cd support_assistant && python ingest.py && uvicorn main:app --host 0.0.0.0 --port 7860
```

## Design decisions — summary

**`/data_pipeline`** — 63 real books across 3 categories; normalized `categories`↔`books`
schema (PK/FK); fixed 1 GBP = 105.50 INR conversion; 5 required SQL clauses plus a
`pd.merge`-only reproduction of the JOIN, confirmed identical.

**`/analytics`** — Titanic loaded once, cleaned per the stated missing-value threshold
rule, `ColumnTransformer`+`Pipeline` so all preprocessing fits on the training split only.
Three classifiers compared, imbalance handling compared (baseline/`class_weight`/SMOTE),
`GridSearchCV`+OOB tuning, a separate fare-regression side-task. **Logistic Regression**
is the recommended/saved model (highest AUC, near-best F1, simplest to serve).

**`/support_assistant`** — one chunk per policy doc, embedded (MiniLM, with an automatic
local TF-IDF fallback only if `huggingface.co` is unreachable), retrieved via ChromaDB,
routed by a 3-node LangGraph behind FastAPI. `MOCK_LLM` gates every LLM call — default is
fully deterministic (graded path); retrieval itself is always real.

Full detail, all written interpretations, and captured run output are in each module's own
README.

## Git workflow

History includes a feature branch, committed to twice, merged back into `main` —
`git log --graph --all`.
>>>>>>> 3f08314 (support_assistant: RAG pipeline (ChromaDB + LangGraph + FastAPI), root README)
=======
# Capstone_Masai
>>>>>>> 6996db25d6ab0b1f854815c0ae25bafb8541e73a
