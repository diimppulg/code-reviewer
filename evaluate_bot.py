"""Evaluate saved bot comments against explicit expected concepts.

This is a lightweight project evaluation, not a substitute for human annotation.
It requires both a blocking verdict and a relevant concept match for a bug to count
as detected, avoiding the original script's "any REQUEST_CHANGES means caught" flaw.
"""

import argparse
import csv
import os
import re

import requests


EXPECTED = {
    "pr01": (True, "hardcoded password", ("hardcoded", "password", "credential")),
    "pr02": (True, "SQL injection", ("sql injection", "parameterized", "concatenat")),
    "pr03": (True, "divide by zero", ("divide by zero", "empty", "len(numbers)")),
    "pr04": (True, "input validation", ("validation", "invalid", "email", "age")),
    "pr05": (True, "infinite loop", ("infinite", "indexerror", "out of range")),
    "pr06": (True, "unused imports", ("unused import", "unused")),
    "pr07": (True, "mutable default", ("mutable default", "shared list", "items=[]")),
    "pr08": (True, "swallowed exception", ("bare except", "swallow", "exception")),
    "pr09": (True, "hardcoded secrets", ("hardcoded", "secret", "api key")),
    "pr10": (True, "request error handling", ("timeout", "raise_for_status", "error handling")),
    "pr11": (True, "XSS", ("xss", "escape", "html injection")),
    "pr12": (True, "insecure random", ("insecure random", "cryptographic", "secrets")),
    "pr13": (True, "unbounded cache", ("memory", "unbounded", "cache")),
    "pr14": (True, "race condition", ("race", "lock", "thread safe")),
    "pr15": (True, "plaintext password", ("plaintext", "hash", "password")),
    "pr16": (False, "clean code", ()),
    "pr17": (False, "clean code", ()),
    "pr18": (True, "global state", ("global", "shared state", "side effect")),
    "pr19": (True, "type confusion", ("type", "typeerror", "incompatible")),
    "pr20": (True, "debug code", ("debug", "card number", "pdb", "sensitive")),
}


def verdict(body: str) -> str:
    matches = re.findall(r"\b(APPROVE|REQUEST_CHANGES|NEEDS_DISCUSSION)\b", body)
    return matches[-1] if matches else "NO_VERDICT"


def evaluate(repo: str, token: str, output: str) -> list[dict[str, object]]:
    session = requests.Session()
    session.headers.update(
        {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    )
    prs_response = session.get(
        f"https://api.github.com/repos/{repo}/pulls",
        params={"state": "all", "per_page": 100},
        timeout=30,
    )
    prs_response.raise_for_status()
    results: list[dict[str, object]] = []

    for pr in prs_response.json():
        branch = pr["head"]["ref"].lower()
        key = next((candidate for candidate in EXPECTED if candidate in branch), None)
        if not key:
            continue
        has_bug, bug_type, terms = EXPECTED[key]
        comments_response = session.get(pr["comments_url"], timeout=30)
        comments_response.raise_for_status()
        comments = [c["body"] for c in comments_response.json() if "AI Code Review" in c["body"]]
        body = comments[-1] if comments else ""
        actual_verdict = verdict(body)
        concept_match = any(term in body.casefold() for term in terms) if terms else False
        caught = has_bug and actual_verdict == "REQUEST_CHANGES" and concept_match
        false_positive = not has_bug and actual_verdict == "REQUEST_CHANGES"
        correct = caught if has_bug else actual_verdict == "APPROVE"
        results.append(
            {
                "pr_key": key,
                "pr_number": pr["number"],
                "bug_type": bug_type,
                "has_bug": has_bug,
                "bot_commented": bool(comments),
                "verdict": actual_verdict,
                "concept_match": concept_match,
                "bug_caught": caught,
                "false_positive": false_positive,
                "correct": correct,
            }
        )

    results.sort(key=lambda row: str(row["pr_key"]))
    if not results:
        raise RuntimeError("No matching test pull requests were found")
    with open(output, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)
    return results


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True, help="Repository in owner/name format")
    parser.add_argument("--output", default="evaluation_report.csv")
    args = parser.parse_args()
    token = os.getenv("GITHUB_TOKEN", "").strip()
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required")
    rows = evaluate(args.repo, token, args.output)
    correct = sum(bool(row["correct"]) for row in rows)
    print(f"Correct: {correct}/{len(rows)} ({correct / len(rows):.1%})")
    print(f"Report written to {args.output}")


if __name__ == "__main__":
    main()

