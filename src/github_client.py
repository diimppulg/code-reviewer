import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


class GitHubClient:
    def __init__(self, token: str, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            }
        )
        retry = Retry(
            total=3,
            backoff_factor=0.5,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
        )
        self.session.mount("https://", HTTPAdapter(max_retries=retry))

    def _url(self, repo: str, suffix: str) -> str:
        owner, separator, name = repo.partition("/")
        if not separator or not owner or not name or "/" in name:
            raise ValueError("repo must use the owner/name format")
        return f"https://api.github.com/repos/{owner}/{name}/{suffix.lstrip('/')}"

    def get_diff(self, repo: str, pr_number: int) -> str:
        if pr_number < 1:
            raise ValueError("pr_number must be positive")
        response = self.session.get(
            self._url(repo, f"pulls/{pr_number}"),
            headers={"Accept": "application/vnd.github.v3.diff"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.text

    def post_comment(self, repo: str, pr_number: int, body: str) -> None:
        response = self.session.post(
            self._url(repo, f"issues/{pr_number}/comments"),
            json={"body": body},
            timeout=self.timeout,
        )
        response.raise_for_status()

