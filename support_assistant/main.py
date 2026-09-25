"""FastAPI wrapper. Run: uvicorn main:app --host 0.0.0.0 --port 7860
In Colab: run this in one cell (it blocks), then curl localhost:7860 from
a second cell — no ngrok needed since both run on the same VM.
"""
from fastapi import FastAPI
from graph import ask
from schemas import AskRequest, AskResponse

app = FastAPI(title="Zepto Support Assistant")


@app.get("/")
def root():
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
def ask_endpoint(req: AskRequest) -> AskResponse:
    return AskResponse(**ask(req.query))
