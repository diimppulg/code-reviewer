import unittest

from src.models import Issue, ReviewResult, Severity, Verdict
from src.reviewer import format_comment, merge_reviews, split_diff


class ReviewerTests(unittest.TestCase):
    def test_split_diff_reports_truncation(self) -> None:
        chunks, truncated = split_diff("a\n" * 20, chunk_size=5, max_chunks=2)
        self.assertEqual(len(chunks), 2)
        self.assertTrue(truncated)

    def test_merge_deduplicates_issues_and_blocks_high_severity(self) -> None:
        issue = Issue(severity=Severity.high, file="app.py", line=3, description="Unchecked input")
        review = ReviewResult(summary="Changes input handling.", issues=[issue], verdict=Verdict.request_changes)
        merged = merge_reviews([review, review], truncated=False)
        self.assertEqual(merged.issues, [issue])
        self.assertEqual(merged.verdict, Verdict.request_changes)

    def test_clean_review_is_approved(self) -> None:
        review = ReviewResult(summary="Updates a docstring.", issues=[], verdict=Verdict.approve)
        merged = merge_reviews([review], truncated=False)
        self.assertEqual(merged.verdict, Verdict.approve)
        self.assertIn("No meaningful issues found", format_comment(merged))


if __name__ == "__main__":
    unittest.main()
