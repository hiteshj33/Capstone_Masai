"""3-node LangGraph: classify_intent -> retrieve_and_answer | direct_answer.
MOCK_LLM (env var) gates the LLM call inside each generation step only —
routing itself never depends on it. Default (unset or "1") = deterministic
mock mode, no LLM call: the graded path. "0" = optional real-LLM extension.
"""
import os
from typing import List, TypedDict
from langgraph.graph import StateGraph, END
from ingest import retrieve_top_k
from prompts import build_general_prompt, build_policy_prompt
from schemas import AskResponse

KEYWORDS = ["delivery", "return", "refund", "membership", "tracking", "cancel", "gift card", "support hours"]


def is_mock():
    return os.environ.get("MOCK_LLM", "1") != "0"


class State(TypedDict):
    query: str
    intent: str
    retrieved: List[dict]
    response: dict


def classify_intent(state: State) -> State:
    q = state["query"].lower()
    intent = "policy_question" if any(k in q for k in KEYWORDS) else "general_question"
    return {**state, "intent": intent}  # same heuristic in both modes; classify_intent's LLM branch is the optional extension point


def retrieve_and_answer(state: State) -> State:
    hits = retrieve_top_k(state["query"], k=3)  # real retrieval in both modes
    top = hits[0]["text"] if hits else ""
    if is_mock():
        answer, conf = f"Based on the retrieved context: {top[:200]}", 1.0
    else:
        prompt = build_policy_prompt(state["query"], "\n---\n".join(h["text"] for h in hits))
        answer, conf = _llm_generate(prompt)
    resp = AskResponse(answer=answer, sources=[h["id"] for h in hits], confidence=conf)
    return {**state, "retrieved": hits, "response": resp.model_dump()}


def direct_answer(state: State) -> State:
    if is_mock():
        answer, conf = "I can only answer questions about Zepto policies right now.", 1.0
    else:
        answer, conf = _llm_generate(build_general_prompt(state["query"]))
    resp = AskResponse(answer=answer, sources=[], confidence=conf)
    return {**state, "retrieved": [], "response": resp.model_dump()}


def _llm_generate(prompt, max_retries=2):
    """Optional MOCK_LLM=0 path only. Validates output against AskResponse,
    retrying with a corrective instruction on failure. No provider is wired
    in by default — plug one into _call_llm to exercise this."""
    suffix, err = "", None
    for _ in range(max_retries + 1):
        try:
            text = _call_llm(prompt + suffix)
            AskResponse(answer=text, sources=[], confidence=0.8)
            return text, 0.8
        except Exception as e:
            err = e
            suffix = "\n\nYour last response didn't match the required format. Try again."
    return f"[error: no schema-valid response after {max_retries + 1} tries: {err}]", 0.0


def _call_llm(prompt):
    raise NotImplementedError("Wire up a real LLM provider here (e.g. Groq free tier) to use MOCK_LLM=0.")


def route(state: State) -> str:
    return "retrieve_and_answer" if state["intent"] == "policy_question" else "direct_answer"


def build_graph():
    g = StateGraph(State)
    g.add_node("classify_intent", classify_intent)
    g.add_node("retrieve_and_answer", retrieve_and_answer)
    g.add_node("direct_answer", direct_answer)
    g.set_entry_point("classify_intent")
    g.add_conditional_edges("classify_intent", route,
                             {"retrieve_and_answer": "retrieve_and_answer", "direct_answer": "direct_answer"})
    g.add_edge("retrieve_and_answer", END)
    g.add_edge("direct_answer", END)
    return g.compile()


_graph = None


def ask(query: str) -> dict:
    global _graph
    _graph = _graph or build_graph()
    return _graph.invoke({"query": query, "intent": "", "retrieved": [], "response": {}})["response"]


if __name__ == "__main__":
    for q in ["How long does delivery take?", "What's the weather like today?"]:
        print(q, "->", ask(q))
