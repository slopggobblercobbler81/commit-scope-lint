"""commit-scope-lint: Fast, production-grade Conventional Commits & Scope Linter CLI."""

from .models import (
    CommitMessage,
    LintLevel,
    LintResult,
    LintSuiteResult,
    LintViolation,
)
from .parser import parse_commit_message
from .config import LintConfig, load_config
from .linter import CommitLinter

__version__ = "1.0.0"
__all__ = [
    "__version__",
    "CommitMessage",
    "LintLevel",
    "LintResult",
    "LintSuiteResult",
    "LintViolation",
    "parse_commit_message",
    "LintConfig",
    "load_config",
    "CommitLinter",
]
