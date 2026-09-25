"""Chunk docs/, embed with all-MiniLM-L6-v2, store in ChromaDB.
Falls back to a local TF-IDF embedder only if the MiniLM weights can't be
downloaded (e.g. a restricted network) — the real model is used automatically
wherever huggingface.co is reachable (including Colab). Run: python ingest.py
"""
import sys, subprocess, pathlib
if "google.colab" in sys.modules:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r",
                     str(pathlib.Path(__file__).parent / "requirements.txt")])

import glob, os
import chromadb

HERE = pathlib.Path(__file__).parent
CHROMA_DIR = str(HERE / "chroma_db")
COLLECTION = "zepto_policies"

_model, _backend = None, None


def get_embedder(corpus=None):
    global _model, _backend
    if _model:
        return _model
    try:
        from sentence_transformers import SentenceTransformer
        _model, _backend = SentenceTransformer("all-MiniLM-L6-v2"), "minilm"
    except Exception:
        from sklearn.feature_extraction.text import TfidfVectorizer
        import numpy as np

        class _Fallback:
            def __init__(self, texts):
                self.vec = TfidfVectorizer(stop_words="english").fit(texts)

            def encode(self, texts):
                m = self.vec.transform(texts).toarray()
                n = np.linalg.norm(m, axis=1, keepdims=True); n[n == 0] = 1
                return m / n

        print("[ingest] MiniLM unreachable -> using local TF-IDF fallback embedder.")
        corpus = corpus or [c["text"] for c in load_chunks()]  # e.g. called at query time with no corpus arg
        _model, _backend = _Fallback(corpus), "tfidf-fallback"
    return _model


def load_chunks():
    # One chunk per doc — each policy is already a short, self-contained paragraph.
    out = []
    for path in sorted(glob.glob(str(HERE / "docs" / "doc_*.txt"))):
        out.append({"id": pathlib.Path(path).stem, "text": open(path, encoding="utf-8").read().strip()})
    return out


def build_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        client.delete_collection(COLLECTION)
    except Exception:
        pass
    coll = client.create_collection(COLLECTION)
    chunks = load_chunks()
    texts = [c["text"] for c in chunks]
    embeddings = get_embedder(texts).encode(texts)
    coll.add(ids=[c["id"] for c in chunks], documents=texts, embeddings=embeddings.tolist())
    return coll


def get_collection():
    client = chromadb.PersistentClient(path=CHROMA_DIR)
    try:
        return client.get_collection(COLLECTION)
    except Exception:
        return build_collection()


def retrieve_top_k(query, k=3):
    coll = get_collection()
    emb = get_embedder().encode([query]).tolist()
    res = coll.query(query_embeddings=emb, n_results=k)
    return [{"id": i, "text": t, "distance": d}
            for i, t, d in zip(res["ids"][0], res["documents"][0], res["distances"][0])]


if __name__ == "__main__":
    coll = build_collection()
    print(f"Ingested {coll.count()} chunks into '{COLLECTION}'.")
    for q in ["How long does delivery take?", "What is Zepto Pass+?"]:
        print(f"\n{q!r} ->", [h["id"] for h in retrieve_top_k(q, k=2)])
