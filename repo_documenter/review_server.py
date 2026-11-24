from __future__ import annotations

import json
import logging
import shutil
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from google.adk.apps import App
from google.adk.apps._configs import EventsCompactionConfig
from pydantic import BaseModel, Field
from google.genai import types
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService, DatabaseSessionService

load_dotenv(Path(__file__).with_name(".env"))

from .agent import review_workflow, commit_workflow
from .tools.zip_repository import extract_repository_zip, sha256_file

logger = logging.getLogger("repo_documenter.review_server")

APP_NAME = "repo_documenter"
USER_ID = "local-review-user"
UI_DIR = Path(__file__).parent / "review_ui"

app = FastAPI(title="Repository README Reviewer")
app.mount("/static", StaticFiles(directory=UI_DIR), name="static")

# Local-development store. Use a persistent database/session store for a
# multi-user or production deployment.
_pending_reviews: dict[str, dict[str, Any]] = {}


class ReviewRequest(BaseModel):
    repository_path: str | None = Field(default=None, min_length=1)
    zip_path: str | None = Field(default=None, min_length=1)


class DecisionRequest(BaseModel):
    decision: str = Field(pattern="^(accept|reject)$")


async def _run_workflow(workflow: Any, input_text: str) -> Any:
    """Run an ADK workflow and return its terminal node output.

    ADK exposes workflow data through Event.output. Keep the last non-empty
    output because intermediate nodes also emit outputs while the workflow is
    running. Fail explicitly on ADK error events instead of treating them as a
    successful, empty workflow.
    """
    # DB_URL = "postgresql+asyncpg://postgres:mysecretpassword@localhost:5432/agent_db"
    # # Step 3: Define Event Compaction for session history
    # compacting_config = EventsCompactionConfig(
    #     compaction_interval=3,
    #     overlap_size=1,
    # )
    # app = App(
    #     name=APP_NAME,
    #     events_compaction_config=compacting_config,
    # )
    # session_service = DatabaseSessionService(db_url=DB_URL)
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
    event_count = 0

    async for event in runner.run_async(
        user_id=USER_ID,
        session_id=session_id,
        new_message=message,
    ):
        event_count += 1
        error_code = getattr(event, "error_code", None)
        if error_code:
            error_message = getattr(event, "error_message", None) or str(error_code)
            raise RuntimeError(f"ADK workflow failed: {error_code}: {error_message}")

        output = getattr(event, "output", None)
        if output is not None:
            last_output = output

        content = getattr(event, "content", None)
        if content and content.parts:
            for part in content.parts:
                if getattr(part, "text", None):
                    last_text = part.text

    logger.info(
        "ADK workflow %s completed: session_id=%s events=%d output_type=%s",
        getattr(workflow, "name", type(workflow).__name__),
        session_id,
        event_count,
        type(last_output).__name__ if last_output is not None else "none",
    )

    if last_output is not None:
        return last_output
    if last_text:
        try:
            return json.loads(last_text)
        except json.JSONDecodeError:
            return last_text
    raise RuntimeError(
        f"ADK workflow {getattr(workflow, 'name', type(workflow).__name__)} "
        f"completed without a terminal output (events={event_count})."
    )


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(UI_DIR / "index.html")


@app.post("/api/reviews")
async def create_review(request: ReviewRequest) -> dict[str, Any]:
    has_folder = bool(request.repository_path and request.repository_path.strip())
    has_zip = bool(request.zip_path and request.zip_path.strip())
    if has_folder == has_zip:
        raise HTTPException(
            status_code=400,
            detail="Provide exactly one input: a repository folder path or a fully qualified ZIP file path.",
        )

    extraction_root: Path | None = None
    archive_path: Path | None = None
    try:
        if has_zip:
            archive_candidate = Path(request.zip_path.strip()).expanduser()
            if not archive_candidate.is_absolute():
                raise ValueError("The ZIP file path must be fully qualified (absolute).")
            if archive_candidate.is_symlink():
                raise ValueError("The ZIP file path must not be a symbolic link.")
            archive_path = archive_candidate.resolve(strict=True)
            archive_sha256 = sha256_file(archive_path)
            extraction_root, repository_root = extract_repository_zip(str(archive_path))
            if sha256_file(archive_path) != archive_sha256:
                raise RuntimeError("The ZIP archive changed while it was being read. Please try again.")
            workflow_input = str(repository_root)
        else:
            workflow_input = request.repository_path.strip()

        result = await _run_workflow(review_workflow, workflow_input)
        if isinstance(result, str):
            result = json.loads(result)
        if not isinstance(result, dict):
            raise RuntimeError(f"Unexpected review output type: {type(result).__name__}")

        display_review = {
            key: result[key]
            for key in (
                "old_content", "proposed_content", "diff", "readme_existed",
                "proposed_sha256", "old_sha256", "readme_path",
            )
            if key in result
        }
        pending_record: dict[str, Any] = {"review": result, "cleanup_dir": extraction_root}
        if archive_path is not None and extraction_root is not None:
            repository_root = Path(result["repository_path"]).resolve()
            relative_root = repository_root.relative_to(extraction_root.resolve()).as_posix()
            relative_readme = (
                f"{relative_root}/README.md" if relative_root != "." else "README.md"
            )
            display_review["readme_path"] = f"{archive_path}!/{relative_readme}"
            pending_record.update({
                "archive_path": str(archive_path),
                "archive_extract_root": str(extraction_root),
                "archive_repository_relative": relative_root,
                "archive_sha256": archive_sha256,
            })
        else:
            pending_record["cleanup_dir"] = None

        review_id = str(uuid.uuid4())
        _pending_reviews[review_id] = pending_record
        return {"review_id": review_id, "review": display_review}
    except Exception as exc:
        if extraction_root is not None:
            shutil.rmtree(extraction_root, ignore_errors=True)
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/reviews/{review_id}/decision")
async def decide_review(review_id: str, request: DecisionRequest) -> dict[str, Any]:
    pending = _pending_reviews.get(review_id)
    if pending is None:
        raise HTTPException(status_code=404, detail="Review not found or already completed.")

    review = pending["review"]
    cleanup_dir = pending.get("cleanup_dir")

    if request.decision == "reject":
        _pending_reviews.pop(review_id, None)
        if cleanup_dir:
            shutil.rmtree(cleanup_dir, ignore_errors=True)
        logger.info("README review %s rejected; source was left unchanged.", review_id)
        return {"status": "rejected", "message": "The source was left unchanged."}

    # The accepted proposal and archive metadata are retained server-side; the
    # browser submits only the decision, never replacement content or paths.
    commit_review = dict(review)
    for key in ("archive_path", "archive_extract_root", "archive_repository_relative", "archive_sha256"):
        if key in pending:
            commit_review[key] = pending[key]
    commit_request = json.dumps({"approved": True, "review": commit_review})
    logger.info("README review %s accepted; starting ADK commit workflow.", review_id)
    try:
        result = await _run_workflow(commit_workflow, commit_request)
        if isinstance(result, str):
            try:
                result = json.loads(result)
            except json.JSONDecodeError:
                result = {"status": "unknown", "message": result}
        if not isinstance(result, dict):
            raise RuntimeError(
                f"Commit workflow returned unexpected output: {type(result).__name__}"
            )
        if result.get("status") != "success":
            raise RuntimeError(
                result.get("message", "Commit workflow did not confirm a successful write.")
            )
    except Exception as exc:
        logger.exception("ADK commit workflow failed for review %s", review_id)
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    _pending_reviews.pop(review_id, None)
    if cleanup_dir:
        shutil.rmtree(cleanup_dir, ignore_errors=True)
    logger.info("README review %s committed: %s", review_id, result.get("readme_path"))
    return result

