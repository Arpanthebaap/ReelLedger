"""
ReelLedger backend.

Serves the static dashboard and exposes /chat, which runs a turn through the
Producer Agent (and its exposure/comps sub-agents, which call ClickHouse via
MCP) and returns the synthesized answer.
"""
import os
import uuid

import clickhouse_connect
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from google.genai import types
from pydantic import BaseModel

from agents.orchestrator import build_runner

load_dotenv()

app = FastAPI(title="ReelLedger")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before a real production deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")

# One runner instance per process; ADK's InMemoryRunner manages session state
# internally per (user_id, session_id).
_runner = build_runner()


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    user_id: str = "demo-user"


class ChatResponse(BaseModel):
    reply: str
    session_id: str


@app.get("/")
def root():
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))


@app.get("/healthz")
def healthz():
    return {"status": "ok"}


def _clickhouse_client():
    return clickhouse_connect.get_client(
        host=os.environ.get("CLICKHOUSE_HOST", "localhost"),
        port=int(os.environ.get("CLICKHOUSE_PORT", "8123")),
        username=os.environ.get("CLICKHOUSE_USER", "default"),
        password=os.environ.get("CLICKHOUSE_PASSWORD", ""),
        secure=os.environ.get("CLICKHOUSE_SECURE", "false").lower() == "true",
        database=os.environ.get("CLICKHOUSE_DATABASE", "reelledger"),
    )


@app.get("/api/exposure-summary")
def exposure_summary(project_id: str = "demo-project-001"):
    """Direct ClickHouse aggregation (bypassing the agent) that powers the
    dashboard chart -- separate from the agent's own ClickHouse-via-MCP
    queries, so the dashboard renders instantly without waiting on an LLM
    turn, while the chat still goes through the full agent pipeline.
    """
    client = _clickhouse_client()
    query = """
        SELECT
            b.department AS department,
            b.total_budget AS budget,
            sum(s.actual_amount) AS spent
        FROM reelledger.project_budgets b
        LEFT JOIN reelledger.spend_line_items s
            ON b.project_id = s.project_id AND b.department = s.department
        WHERE b.project_id = {project_id:String}
        GROUP BY b.department, b.total_budget
        ORDER BY (spent / budget) DESC
    """
    result = client.query(query, parameters={"project_id": project_id})
    rows = [
        {"department": r[0], "budget": float(r[1]), "spent": float(r[2] or 0)}
        for r in result.result_rows
    ]
    return {"project_id": project_id, "departments": rows}


@app.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())

    session = await _runner.session_service.get_session(
        app_name="reelledger", user_id=req.user_id, session_id=session_id
    )
    if session is None:
        session = await _runner.session_service.create_session(
            app_name="reelledger", user_id=req.user_id, session_id=session_id
        )

    content = types.Content(role="user", parts=[types.Part(text=req.message)])

    final_text = ""
    async for event in _runner.run_async(
        user_id=req.user_id, session_id=session_id, new_message=content
    ):
        if event.is_final_response() and event.content and event.content.parts:
            final_text = "".join(p.text or "" for p in event.content.parts)

    return ChatResponse(reply=final_text, session_id=session_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8080")), reload=True)
