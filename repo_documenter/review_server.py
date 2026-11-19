from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

load_dotenv(Path(__file__).with_name(".env"))

from .agent import review_workflow, commit_workflow

APP_NAME = "repo_documenter"
USER_ID = "local-review-user"
UI_DIR = Path(__file__).parent / "review_ui"

app = FastAPI(title="Repository README Reviewer")
app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

# Local-development store. Use a persistent database/session store for a
# multi-user or production deployment.
_pending_reviews: dict[str, dict[str, Any]] = {}


class ReviewRequest(BaseModel):
    repository_path: str = Field(min_length=1)


class DecisionRequest(BaseModel):
    decision: str = Field(pattern="^(accept|reject)$")


async def _run_workflow(workflow: Any, input_text: str) -> Any:
    """Run an ADK workflow and return the last FunctionNode output."""
    session_service = InMemorySessionService()
    runner = Runner(
        agent=workflow,
        app_name=APP_NAME,
        session_service=session_service,
    )
    session_id = str(uuid.uuid4())
    await session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        session_id=session_id,
    )
    message = types.Content(
        role="user",
        parts=[types.Part(text=input_text)],
    )
    last_output: Any = None
    last_text: str | None = None
    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        output = getattr(event, "output", None)
        if output is not None:
            last_output = output
        content = getattr(event, "content", None)
        if content and content.parts:
            for part in content.parts:
                if getattr(part, "text", None):
                    last_text = part.text
    if last_output is not None:
        return last_output
    if last_text:
        try:
            return json.loads(last_text)
        except json.JSONDecodeError:
            return last_text
    raise RuntimeError("ADK workflow completed without returning an output.")


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.post("/api/reviews")
async def create_review(request: ReviewRequest) -> dict[str, Any]:
    try:
        result = await _run_workflow(review_workflow, request.repository_path)
        if isinstance(result, str):
            result = json.loads(result)
        if not isinstance(result, dict):
            raise RuntimeError(f"Unexpected review output type: {type(result).__name__}")
        review_id = str(uuid.uuid4())
        _pending_reviews[review_id] = result
        return {"review_id": review_id, "review": result}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/reviews/{review_id}/decision")
async def decide_review(review_id: str, request: DecisionRequest) -> dict[str, Any]:
    review = _pending_reviews.get(review_id)
    if review is None:
        raise HTTPException(status_code=404, detail="Review not found or already completed.")

    if request.decision == "reject":
        _pending_reviews.pop(review_id, None)
        return {"status": "rejected", "message": "README.md was left unchanged."}

    # Only the server-held review is passed to ADK. The browser cannot alter
    # proposed Markdown or the old-file hash when it clicks Accept.
    commit_request = json.dumps({"approved": True, "review": review})
    try:
        result = await _run_workflow(commit_workflow, commit_request)
    except Exception as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    finally:
        _pending_reviews.pop(review_id, None)

    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            result = {"status": "success", "message": result}
    return result
