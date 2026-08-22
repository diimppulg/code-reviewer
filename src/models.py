from dataclasses import dataclass
from enum import Enum


class Severity(str, Enum):
    critical = "CRITICAL"
    high = "HIGH"
    medium = "MEDIUM"
    low = "LOW"
    style = "STYLE"


class Verdict(str, Enum):
    approve = "APPROVE"
    request_changes = "REQUEST_CHANGES"
    needs_discussion = "NEEDS_DISCUSSION"


@dataclass(frozen=True)
class Issue:
    severity: Severity
    file: str
    line: int | None
    description: str

    @classmethod
    def from_dict(cls, data: object) -> "Issue":
        if not isinstance(data, dict):
            raise ValueError("Each issue must be an object")
        file = data.get("file")
        description = data.get("description")
        line = data.get("line")
        if not isinstance(file, str) or not file.strip() or len(file) > 500:
            raise ValueError("Issue file is invalid")
        if not isinstance(description, str) or not description.strip() or len(description) > 2000:
            raise ValueError("Issue description is invalid")
        if line is not None and (not isinstance(line, int) or isinstance(line, bool) or line < 1):
            raise ValueError("Issue line is invalid")
        return cls(Severity(data.get("severity")), file, line, description)


@dataclass(frozen=True)
class ReviewResult:
    summary: str
    issues: list[Issue]
    verdict: Verdict

    @classmethod
    def from_dict(cls, data: object) -> "ReviewResult":
        if not isinstance(data, dict):
            raise ValueError("Review must be an object")
        summary = data.get("summary")
        raw_issues = data.get("issues")
        if not isinstance(summary, str) or not summary.strip() or len(summary) > 1000:
            raise ValueError("Review summary is invalid")
        if not isinstance(raw_issues, list) or len(raw_issues) > 100:
            raise ValueError("Review issues are invalid")
        return cls(summary, [Issue.from_dict(issue) for issue in raw_issues], Verdict(data.get("verdict")))

    def to_dict(self) -> dict[str, object]:
        return {
            "summary": self.summary,
            "issues": [
                {
                    "severity": issue.severity.value,
                    "file": issue.file,
                    "line": issue.line,
                    "description": issue.description,
                }
                for issue in self.issues
            ],
            "verdict": self.verdict.value,
        }
