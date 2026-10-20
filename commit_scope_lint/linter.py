"""Commit message linter orchestration engine."""

import re
from typing import List, Optional, Tuple, Union
from .config import LintConfig
from .models import CommitMessage, LintLevel, LintResult, LintSuiteResult, LintViolation
from .parser import parse_commit_message
from .rules import ALL_RULES, BaseRule


class CommitLinter:
    """Core linter engine responsible for parsing and evaluating commits."""

    def __init__(self, config: Optional[LintConfig] = None, rules: Optional[List[BaseRule]] = None):
        self.config = config or LintConfig()
        self.rules = rules or ALL_RULES
        self._compiled_ignores = [re.compile(p) for p in self.config.ignore_patterns]

    def is_ignored(self, text: str) -> Optional[str]:
        """Check if message matches any ignore pattern."""
        first_line = text.strip().splitlines()[0] if text.strip() else ""
        for pattern in self._compiled_ignores:
            if pattern.search(first_line):
                return f"Matches ignore pattern '{pattern.pattern}'"
        return None

    def lint_commit(
        self,
        raw_message: str,
        commit_hash: Optional[str] = None,
        author: Optional[str] = None,
        strip_comments: bool = False,
    ) -> LintResult:
        """Lint a single commit message string."""
        ignore_reason = self.is_ignored(raw_message)
        commit = parse_commit_message(
            raw=raw_message,
            commit_hash=commit_hash,
            author=author,
            strip_comments=strip_comments,
        )

        if ignore_reason:
            return LintResult(
                commit=commit,
                violations=[],
                is_ignored=True,
                ignore_reason=ignore_reason,
            )

        violations: List[LintViolation] = []
        for rule in self.rules:
            rule_violations = rule.validate(commit, self.config)
            violations.extend(rule_violations)

        # Enforce strict mode if enabled
        if self.config.strict:
            for v in violations:
                if v.level == LintLevel.WARNING:
                    v.level = LintLevel.ERROR

        return LintResult(
            commit=commit,
            violations=violations,
            is_ignored=False,
            ignore_reason=None,
        )

    def lint_commits(
        self,
        commits: List[Union[str, Tuple[str, str, str]]],
        strip_comments: bool = False,
    ) -> LintSuiteResult:
        """Lint multiple commit messages."""
        results: List[LintResult] = []

        for item in commits:
            if isinstance(item, tuple):
                commit_hash, author, raw_msg = item
                res = self.lint_commit(
                    raw_message=raw_msg,
                    commit_hash=commit_hash,
                    author=author,
                    strip_comments=strip_comments,
                )
            else:
                res = self.lint_commit(
                    raw_message=item,
                    strip_comments=strip_comments,
                )
            results.append(res)

        return LintSuiteResult(results=results)
