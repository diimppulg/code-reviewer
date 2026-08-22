import hmac
import os

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from src.config import Settings
from src.models import ReviewResult
from src.reviewer import run_review

app = FastAPI(title="AI Code Review Bot", version="2.0.0")


class ReviewRequest(BaseModel):
    repo: str = Field(pattern=r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
    pr_number: int = Field(ge=1)
    post_comment: bool = True


def authorize(authorization: str | None = Header(default=None)) -> None:
    expected = os.getenv("SERVICE_TOKEN", "").strip()
    if not expected:
        raise HTTPException(status_code=503, detail="SERVICE_TOKEN is not configured")
    supplied = authorization.removeprefix("Bearer ").strip() if authorization else ""
    if not hmac.compare_digest(supplied, expected):
        raise HTTPException(status_code=401, detail="Invalid bearer token")


@app.get("/")
def root() -> dict[str, str]:
    return {"status": "running", "service": "AI Code Reviewer", "version": "2.0.0"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy"}


@app.post("/review", dependencies=[Depends(authorize)])
def review(request: ReviewRequest) -> dict[str, object]:
    try:
        result = run_review(
            request.repo,
            request.pr_number,
            Settings.from_env(),
            post_comment=request.post_comment,
        )
        return result.to_dict()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        # Avoid returning credentials or upstream response bodies to callers.
        raise HTTPException(status_code=502, detail="Review service failed") from exc
