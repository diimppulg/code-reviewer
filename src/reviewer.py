from src.config import Settings
from src.models import Issue, ReviewResult, Severity, Verdict


def split_diff(diff: str, chunk_size: int, max_chunks: int) -> tuple[list[str], bool]:
    lines = diff.splitlines(keepends=True)
    chunks: list[str] = []
    current = ""
    for line in lines:
        if current and len(current) + len(line) > chunk_size:
            chunks.append(current)
            current = ""
            if len(chunks) == max_chunks:
                return chunks, True
        current += line
    if current and len(chunks) < max_chunks:
        chunks.append(current)
    return chunks, False


def merge_reviews(reviews: list[ReviewResult], truncated: bool) -> ReviewResult:
    issues: list[Issue] = []
    seen: set[tuple[str, int | None, str]] = set()
    for review in reviews:
        for issue in review.issues:
            key = (issue.file, issue.line, issue.description.casefold())
            if key not in seen:
                seen.add(key)
                issues.append(issue)

    blockers = {Severity.critical, Severity.high, Severity.medium}
    if any(issue.severity in blockers for issue in issues):
        verdict = Verdict.request_changes
    elif issues or truncated:
        verdict = Verdict.needs_discussion
    else:
        verdict = Verdict.approve

    summary = reviews[0].summary if reviews else "No reviewable changes found."
    if len(reviews) > 1:
        summary = f"Reviewed the pull request in {len(reviews)} diff chunks. {summary}"
    if truncated:
        summary += " The diff exceeded the configured review limit."
    return ReviewResult(summary=summary, issues=issues, verdict=verdict)


def format_comment(review: ReviewResult) -> str:
    lines = ["## AI Code Review", "", "### Summary", review.summary, "", "### Issues Found"]
    if not review.issues:
        lines.append("No meaningful issues found.")
    else:
        for issue in review.issues:
            location = issue.file + (f":{issue.line}" if issue.line else "")
            lines.append(f"- **[{issue.severity.value}]** `{location}` - {issue.description}")
    lines.extend(["", "### Verdict", f"**{review.verdict.value}**", "", "---", "*AI-generated review; verify before merging.*"])
    return "\n".join(lines)


def run_review(repo: str, pr_number: int, settings: Settings, post_comment: bool = True) -> ReviewResult:
    # Keep network adapters at the application boundary so review formatting and
    # aggregation remain independently testable.
    from src.github_client import GitHubClient
    from src.llm_client import LLMClient

    github = GitHubClient(settings.github_token, settings.request_timeout)
    llm = LLMClient(settings.gemini_api_key, settings.model, settings.request_timeout)
    diff = github.get_diff(repo, pr_number)
    if not diff.strip():
        return ReviewResult(summary="No reviewable changes found.", issues=[], verdict=Verdict.approve)

    chunks, truncated = split_diff(diff, settings.chunk_size, settings.max_chunks)
    result = merge_reviews([llm.review_diff(chunk) for chunk in chunks], truncated)
    if post_comment:
        github.post_comment(repo, pr_number, format_comment(result))
    return result
