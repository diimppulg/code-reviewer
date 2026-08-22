import os

from src.config import Settings
from src.reviewer import run_review


def main() -> None:
    repo = os.environ.get("REPO", "").strip()
    pr_number_raw = os.environ.get("PR_NUMBER", "").strip()
    if not repo or not pr_number_raw:
        raise RuntimeError("REPO and PR_NUMBER are required")
    try:
        pr_number = int(pr_number_raw)
    except ValueError as exc:
        raise RuntimeError("PR_NUMBER must be an integer") from exc

    result = run_review(repo, pr_number, Settings.from_env())
    print(f"Review posted: {result.verdict.value}; {len(result.issues)} issue(s)")


if __name__ == "__main__":
    main()

