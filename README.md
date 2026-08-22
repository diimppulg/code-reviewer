# AI Code Review Bot

An automated code-review assistant that analyzes GitHub pull requests with a large language model and posts structured feedback directly on the pull request.

I developed this project as part of a Cloud Computing course to explore how LLMs can be integrated into a practical CI/CD workflow. The project combines GitHub Actions, the GitHub REST API, Google Gemini models, FastAPI, and Docker.

## What it does

When a pull request is opened or updated, the bot:

1. Starts automatically through GitHub Actions.
2. Retrieves the pull-request diff from GitHub.
3. Splits large diffs into bounded chunks.
4. Sends each chunk to the configured language model through Gemini.
5. Validates and combines the model responses.
6. Posts a review containing a summary, severity-tagged findings, and a verdict.

Example verdicts are `APPROVE`, `REQUEST_CHANGES`, and `NEEDS_DISCUSSION`.

> The generated review is advisory and should be verified by a human before merging.

## Key features

- Automatic reviews for new and updated pull requests
- Structured findings with `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, and `STYLE` severity levels
- Large-diff chunking with a configurable processing limit
- Response validation before comments are posted
- Retry and timeout handling for external API calls
- Basic protection against instructions embedded inside untrusted code diffs
- FastAPI endpoint for invoking the same review pipeline as a service
- Docker support for portable deployment
- Evaluation script for measuring results on test pull requests

## System design

```text
Developer opens a pull request
              |
              v
       GitHub Actions
              |
              v
   Fetch diff from GitHub API
              |
              v
      Split and review diff
              |
              v
      Google Gemini 3.5 Flash
              |
              v
 Validate and combine findings
              |
              v
 Post review comment on GitHub
```

Both the GitHub Actions workflow and the FastAPI application use the same review pipeline under `src/`.

## Technology stack

| Technology | Purpose |
|---|---|
| Python 3.12 | Core application language |
| GitHub Actions | Pull-request automation |
| GitHub REST API | Retrieve diffs and post comments |
| Gemini API | LLM inference |
| Gemini 3.5 Flash | Default code-review model |
| FastAPI | Optional REST API |
| Docker | Containerized deployment |

## Project structure

```text
.
|-- .github/workflows/review.yml  # GitHub Actions workflow
|-- api.py                        # FastAPI application
|-- main.py                       # GitHub Actions entry point
|-- evaluate_bot.py               # Evaluation utility
|-- Dockerfile
|-- requirements.txt
|-- src/
|   |-- config.py                 # Environment configuration
|   |-- github_client.py          # GitHub API client
|   |-- llm_client.py             # Gemini API client
|   |-- models.py                 # Review data models
|   `-- reviewer.py               # Shared review pipeline
`-- tests/
    `-- test_reviewer.py
```

## Run with GitHub Actions

This is the main way to use the project.

1. Generate a free-tier API key in Google AI Studio.
2. In the GitHub repository, open **Settings > Secrets and variables > Actions**.
3. Create a repository secret named `GEMINI_API_KEY`.
4. Create a branch, push a code change, and open a pull request into `main`.
5. Open the **Actions** tab to monitor the workflow.
6. Check the pull request for the generated review comment.

The workflow uses GitHub's temporary `${{ github.token }}` automatically. No personal GitHub token needs to be committed or added as a repository secret.

## Run locally

Install the dependencies:

```bash
python -m venv .venv
pip install -r requirements.txt
```

Provide credentials through environment variables, never through source files:

```powershell
$env:GITHUB_TOKEN = "your short-lived GitHub token"
$env:GEMINI_API_KEY = "your Gemini API key"
$env:REPO = "owner/repository"
$env:PR_NUMBER = "1"
python main.py
```

## Run the API

The FastAPI service requires an additional bearer token chosen by the operator:

```powershell
$env:SERVICE_TOKEN = "a-random-local-value"
uvicorn api:app --host 0.0.0.0 --port 8000
```

Interactive API documentation is available at `http://localhost:8000/docs`.

Example request body for `POST /review`:

```json
{
  "repo": "owner/repository",
  "pr_number": 1,
  "post_comment": true
}
```

## Configuration

| Variable | Required | Default | Description |
|---|---:|---:|---|
| `GITHUB_TOKEN` | Yes | - | Reads pull requests and posts comments |
| `GEMINI_API_KEY` | Yes | - | Authenticates requests to Gemini |
| `SERVICE_TOKEN` | API only | - | Authorizes calls to `/review` |
| `GEMINI_MODEL` | No | `gemini-3.5-flash` | Gemini model used for reviews |
| `REQUEST_TIMEOUT` | No | `30` | Network timeout in seconds |
| `DIFF_CHUNK_SIZE` | No | `12000` | Maximum characters in each chunk |
| `MAX_DIFF_CHUNKS` | No | `5` | Maximum chunks reviewed per pull request |

No API keys or credential values are stored in this repository.

## Testing

Run the offline unit tests with:

```bash
python -m unittest discover -s tests -v
```

The course evaluation used 20 pull-request scenarios: 18 containing intentional issues and two containing clean code. In that experiment, all 18 intentionally problematic pull requests received blocking verdicts, while both clean examples were also flagged. This produced 18 correct decisions out of 20, or 90% decision accuracy.

These results describe that specific test run and model configuration. They should not be treated as a general benchmark. The included evaluator also checks whether a review mentions a concept related to the expected problem instead of counting every blocking verdict as successful detection.

## Current limitations

- LLM output may include false positives or miss context outside the diff.
- Reviews exceeding the configured chunk limit are marked incomplete.
- Feedback is posted as one pull-request comment rather than inline comments.
- Pull requests from forks are skipped because GitHub does not expose repository secrets to untrusted fork workflows.
- Model behavior can change, so evaluation should be repeated for each model and prompt version.

## Future work

- Add inline comments on exact changed lines
- Apply labels based on issue severity
- Add fallback support for multiple LLM providers
- Expand the evaluation dataset and include precision and recall per finding
- Add integration tests with mocked GitHub and Gemini responses
