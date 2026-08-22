import os
from dataclasses import dataclass


def _positive_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if value < 1:
        raise ValueError(f"{name} must be positive")
    return value


@dataclass(frozen=True)
class Settings:
    github_token: str
    groq_api_key: str
    model: str = "groq/compound"
    request_timeout: int = 30
    chunk_size: int = 12_000
    max_chunks: int = 5

    @classmethod
    def from_env(cls) -> "Settings":
        github_token = os.getenv("GITHUB_TOKEN", "").strip()
        groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        missing = [
            name
            for name, value in (
                ("GITHUB_TOKEN", github_token),
                ("GROQ_API_KEY", groq_api_key),
            )
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")
        return cls(
            github_token=github_token,
            groq_api_key=groq_api_key,
            model=os.getenv("GROQ_MODEL", cls.model),
            request_timeout=_positive_int("REQUEST_TIMEOUT", 30),
            chunk_size=_positive_int("DIFF_CHUNK_SIZE", 12_000),
            max_chunks=_positive_int("MAX_DIFF_CHUNKS", 5),
        )
