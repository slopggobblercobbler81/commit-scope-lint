"""Data models for commit-scope-lint."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class LintLevel(str, Enum):
    """Severity level of a lint violation."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class LintViolation:
    """Represents a single rule violation in a commit message."""
    rule_id: str
    message: str
    level: LintLevel = LintLevel.ERROR
    line_number: Optional[int] = None
    suggestion: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert violation to dictionary format."""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "level": self.level.value,
            "line_number": self.line_number,
            "suggestion": self.suggestion,
        }


@dataclass
class CommitMessage:
    """Parsed conventional commit message structure."""
    raw: str
    header: str
    type: Optional[str] = None
    scope: Optional[str] = None
    is_breaking: bool = False
    subject: Optional[str] = None
    body: Optional[str] = None
    body_lines: List[str] = field(default_factory=list)
    footers: List[Tuple[str, str]] = field(default_factory=list)
    commit_hash: Optional[str] = None
    author: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert parsed commit to dictionary format."""
        return {
            "raw": self.raw,
            "header": self.header,
            "type": self.type,
            "scope": self.scope,
            "is_breaking": self.is_breaking,
            "subject": self.subject,
            "body": self.body,
            "footers": [{"token": k, "value": v} for k, v in self.footers],
            "commit_hash": self.commit_hash,
            "author": self.author,
        }


@dataclass
class LintResult:
    """Linting outcome for a single commit message."""
    commit: CommitMessage
    violations: List[LintViolation] = field(default_factory=list)
    is_ignored: bool = False
    ignore_reason: Optional[str] = None

    @property
    def passed(self) -> bool:
        """True if the commit passed with zero errors."""
        if self.is_ignored:
            return True
        return not any(v.level == LintLevel.ERROR for v in self.violations)

    @property
    def errors_count(self) -> int:
        """Count of error-level violations."""
        if self.is_ignored:
            return 0
        return sum(1 for v in self.violations if v.level == LintLevel.ERROR)

    @property
    def warnings_count(self) -> int:
        """Count of warning-level violations."""
        if self.is_ignored:
            return 0
        return sum(1 for v in self.violations if v.level == LintLevel.WARNING)

    def to_dict(self) -> Dict[str, Any]:
        """Convert lint result to dictionary format."""
        return {
            "commit": self.commit.to_dict(),
            "passed": self.passed,
            "is_ignored": self.is_ignored,
            "ignore_reason": self.ignore_reason,
            "errors_count": self.errors_count,
            "warnings_count": self.warnings_count,
            "violations": [v.to_dict() for v in self.violations],
        }


@dataclass
class LintSuiteResult:
    """Aggregated linting outcome for one or more commits."""
    results: List[LintResult] = field(default_factory=list)

    @property
    def total_commits(self) -> int:
        return len(self.results)

    @property
    def passed_commits(self) -> int:
        return sum(1 for r in self.results if r.passed)

    @property
    def failed_commits(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def total_errors(self) -> int:
        return sum(r.errors_count for r in self.results)

    @property
    def total_warnings(self) -> int:
        return sum(r.warnings_count for r in self.results)

    @property
    def success(self) -> bool:
        """True if all commits passed with zero errors."""
        return self.total_commits == 0 or all(r.passed for r in self.results)

    def to_dict(self) -> Dict[str, Any]:
        """Convert entire suite result to dictionary format."""
        return {
            "success": self.success,
            "summary": {
                "total_commits": self.total_commits,
                "passed_commits": self.passed_commits,
                "failed_commits": self.failed_commits,
                "total_errors": self.total_errors,
                "total_warnings": self.total_warnings,
            },
            "results": [r.to_dict() for r in self.results],
        }
