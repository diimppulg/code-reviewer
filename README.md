# AI Code Review Bot

An LLM-assisted GitHub bot that reviews pull-request diffs and posts structured feedback. GitHub Actions triggers the review, the GitHub API supplies the diff, and Groq's OpenAI-compatible endpoint provides the model response.

> AI review is advisory. A human should verify findings before merging.

## Improvements in this version

- One shared implementation powers both GitHub Actions and FastAPI; review logic is no longer duplicated.
- Model output is validated as structured JSON before it is posted.
- Large diffs are reviewed in bounded chunks instead of being silently cut at 8,000 characters.
- Network calls have timeouts and retries for transient failures.
- Diff content is explicitly treated as untrusted data in the prompt.
- API requests require a separately configured bearer token.
- The workflow avoids exposing repository secrets to pull requests from forks.
- Evaluation requires both a blocking verdict and a relevant concept match. It no longer counts every `REQUEST_CHANGES` response as a detected bug.
- Documentation does not claim unsupported accuracy results.

## Architecture

1. A same-repository pull request opens, changes, or reopens.
2. `.github/workflows/review.yml` runs `main.py`.
3. `GitHubClient` retrieves the pull-request diff.
4. `split_diff` divides a large diff into bounded review chunks.
5. `LLMClient` requests and validates one structured review per chunk.
6. The reviewer deduplicates findings and derives the final verdict.
7. `GitHubClient` posts one clearly labeled AI review comment.

The FastAPI application uses the same pipeline through `POST /review`.

## Repository structure

```text
.
|-- .github/workflows/review.yml
|-- api.py
|-- main.py
|-- evaluate_bot.py
|-- src/
|   |-- config.py
|   |-- github_client.py
|   |-- llm_client.py
|   |-- models.py
|   `-- reviewer.py
`-- tests/
```

## GitHub Actions setup

Add only `GROQ_API_KEY` under **Settings > Secrets and variables > Actions**. The workflow uses GitHub's short-lived `${{ github.token }}` automatically; do not create or commit a personal GitHub token.

No credential values are included in this repository.

## Local CLI

Set the required values in your shell environment, then run:

```powershell
$env:GITHUB_TOKEN = "your short-lived GitHub token"
$env:GROQ_API_KEY = "your Groq key"
$env:REPO = "owner/repository"
$env:PR_NUMBER = "1"
python main.py
```

Do not place real values in source files, shell history, screenshots, or commits.

## FastAPI

The API additionally requires `SERVICE_TOKEN`, a random value used to authorize callers.

```powershell
$env:SERVICE_TOKEN = "a locally generated random value"
uvicorn api:app --host 0.0.0.0 --port 8000
```

Call `POST /review` with `Authorization: Bearer <SERVICE_TOKEN>` and:

```json
{"repo": "owner/repository", "pr_number": 1, "post_comment": true}
```

For public deployment, also use HTTPS, network restrictions, rate limiting, and a managed secret store.

## Configuration

| Variable | Required | Default | Purpose |
|---|---:|---:|---|
| `GITHUB_TOKEN` | Yes | - | Read PRs and post comments |
| `GROQ_API_KEY` | Yes | - | Authenticate model requests |
| `SERVICE_TOKEN` | API only | - | Authorize `/review` callers |
| `GROQ_MODEL` | No | `llama-3.3-70b-versatile` | Model identifier |
| `REQUEST_TIMEOUT` | No | `30` | HTTP timeout in seconds |
| `DIFF_CHUNK_SIZE` | No | `12000` | Maximum characters per chunk |
| `MAX_DIFF_CHUNKS` | No | `5` | Maximum chunks per review |

## Tests

```bash
pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
```

## Evaluation caveat

The original course experiment reported 18 buggy PRs flagged and two clean PRs incorrectly flagged. That is 18/20 correct decisions (90%), not 20/20. More importantly, the old evaluator treated any `REQUEST_CHANGES` verdict on a buggy PR as successful detection, even when the response might have identified a different problem.

The revised evaluator performs a basic concept match in addition to checking the verdict. This is still only a heuristic. A defensible evaluation should use blinded human annotations, multiple runs, precision/recall by finding, and confidence intervals.

Run the lightweight evaluator with:

```powershell
$env:GITHUB_TOKEN = "your short-lived GitHub token"
python evaluate_bot.py --repo owner/repository
```

Generated evaluation CSV files are ignored by Git to prevent outdated results from being presented as current evidence.

## Remaining limitations

- Prompt injection risk can be reduced but not eliminated when an LLM reviews untrusted code.
- Reviews beyond the configured chunk limit are marked incomplete.
- Feedback is posted as a single PR comment, not as official GitHub review state or inline annotations.
- Model behavior may change over time; results must be re-evaluated for the exact model and prompt version.

