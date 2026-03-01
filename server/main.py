"""FastAPI application entry point.

Defines the API routes and application lifecycle.
"""

from fastapi import FastAPI, WebSocket
from pydantic import BaseModel

from server.coach import coach
from server.voice import voice_handler

app = FastAPI(
    title="Wololo Coach",
    description="Real-time AoE2 battle coach powered by Gemini 2.5 Flash",
    version="0.1.0",
)


class QueryRequest(BaseModel):
    """Request model for /ask endpoint."""
    query: str


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok", "service": "wololo-coach"}


@app.post("/ask")
async def ask(request: QueryRequest) -> dict:
    """Ask the coach a strategy question.

    Args:
        request: QueryRequest object with a "query" string.

    Returns:
        Dict with an "answer" key containing the coach's response.
    """
    answer = await coach.ask(request.query)
    return {"answer": answer, "query": request.query}


@app.websocket("/voice")
async def voice_endpoint(websocket: WebSocket):
    """WebSocket endpoint for bidirectional audio streaming."""
    await voice_handler.handle_session(websocket)
