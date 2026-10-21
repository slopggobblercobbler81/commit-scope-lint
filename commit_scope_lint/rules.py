"""Rule definitions and validation logic for commit messages."""

import re
from typing import List, Optional
from .config import LintConfig
from .models import CommitMessage, LintLevel, LintViolation


def is_kebab_case(s: str) -> bool:
    """Check if string is valid kebab-case (e.g. auth-provider or api-v2)."""
    return bool(re.match(r"^[a-z0-9]+(-[a-z0-9]+)*$", s))


def is_snake_case(s: str) -> bool:
    """Check if string is valid snake_case (e.g. auth_provider)."""
    return bool(re.match(r"^[a-z0-9]+(_[a-z0-9]+)*$", s))


def is_camel_case(s: str) -> bool:
    """Check if string is valid camelCase (e.g. authProvider)."""
    return bool(re.match(r"^[a-z]+([A-Z0-9][a-z0-9]*)*$", s))


def check_scope_case(scope: str, expected_case: str) -> bool:
    """Verify scope string matches expected casing style."""
    if expected_case == "any":
        return True
    if expected_case == "kebab-case":
        return is_kebab_case(scope)
    if expected_case == "lowercase":
        return scope.islower()
    if expected_case == "snake_case":
        return is_snake_case(scope)
    if expected_case == "camelCase":
        return is_camel_case(scope)
    if expected_case == "uppercase":
        return scope.isupper()
    return True


def is_url_or_code(line: str) -> bool:
    """Return True if line contains an URL, markdown link, or code snippet that should be exempt from length limits."""
    stripped = line.strip()
    if stripped.startswith("http://") or stripped.startswith("https://"):
        return True
    if re.search(r"https?://[^\s]+", stripped):
        return True
    if stripped.startswith("```") or stripped.startswith("`"):
        return True
    return False


class BaseRule:
    """Base class for all commit validation rules."""
    rule_id: str = "base"
    default_level: LintLevel = LintLevel.ERROR

    def validate(self, commit: CommitMessage, config: LintConfig) -> List[LintViolation]:
        raise NotImplementedError


class RuleHeaderFormat(BaseRule):
    """Ensure commit header follows Conventional Commits format."""
    rule_id = "header-format"

    def validate(self, commit: CommitMessage, config: LintConfig) -> List[LintViolation]:
        violations: List[LintViolation] = []
        if not commit.header.strip():
            violations.append(
                LintViolation(
                    rule_id="header-empty",
                    message="Commit message header must not be empty",
                    level=LintLevel.ERROR,
                    line_number=1,
                    suggestion="Add a header formatted as: <type>(<scope>): <subject>",
                )
            )
            return violations

        if commit.type is None or commit.subject is None:
            violations.append(
                LintViolation(
                    rule_id=self.rule_id,
                    message=f"Header '{commit.header}' does not follow Conventional Commits format '<type>(<scope>): <subject>'",
                    level=LintLevel.ERROR,
                    line_number=1,
                    suggestion=f"Example: feat({commit.scope or 'core'}): add requested functionality",
                )
            )
        return violations


class RuleType(BaseRule):
    """Validate commit type against enum and casing."""
    rule_id = "type-enum"

    def validate(self, commit: CommitMessage, config: LintConfig) -> List[LintViolation]:
        if not commit.type:
            return []

        violations: List[LintViolation] = []
        
        # Check type casing
        if not commit.type.islower():
            violations.append(
                LintViolation(
                    rule_id="type-case",
                    message=f"Commit type '{commit.type}' must be lowercase",
                    level=LintLevel.ERROR,
                    line_number=1,
                    suggestion=f"Change '{commit.type}' to '{commit.type.lower()}'",
                )
            )

        # Check allowed types
        if config.types and commit.type.lower() not in [t.lower() for t in config.types]:
            violations.append(
                LintViolation(
                    rule_id=self.rule_id,
                    message=f"Commit type '{commit.type}' is not in allowed types: {', '.join(config.types)}",
                    level=LintLevel.ERROR,
                    line_number=1,
                    suggestion=f"Use one of: {', '.join(config.types[:5])}...",
                )
            )
        return violations


class RuleScope(BaseRule):
    """Validate commit scope presence, casing, and enum."""
    rule_id = "scope-rules"

    def validate(self, commit: CommitMessage, config: LintConfig) -> List[LintViolation]:
        violations: List[LintViolation] = []

        # Scope required check
        if config.scope_required and not commit.scope:
            violations.append(
                LintViolation(
                    rule_id="scope-required",
                    message="Commit scope is required by configuration but was omitted",
                    level=LintLevel.ERROR,
                    line_number=1,
                    suggestion="Specify a scope like 'feat(auth): ...'",
                )
            )
            return violations

        if not commit.scope:
            return violations

        # Scope enum check
        if config.scopes is not None and commit.scope not in config.scopes:
            violations.append(
                LintViolation(
                    rule_id="scope-enum",
                    message=f"Scope '{commit.scope}' is not in allowed list: {', '.join(config.scopes)}",
                    level=LintLevel.ERROR,
                    line_number=1,
                    suggestion=f"Allowed scopes: {', '.join(config.scopes)}",
                )
            )

        # Scope casing check
        if not check_scope_case(commit.scope, config.scope_case):
            level = LintLevel.ERROR if config.strict else LintLevel.WARNING
            violations.append(
                LintViolation(
                    rule_id="scope-case",
                    message=f"Scope '{commit.scope}' violates case requirement '{config.scope_case}'",
                    level=level,
                    line_number=1,
                    suggestion=f"Format scope in '{config.scope_case}'",
                )
            )

        return violations


class RuleHeaderLength(BaseRule):
    """Validate commit header length constraints."""
    rule_id = "header-length"

    def validate(self, commit: CommitMessage, config: LintConfig) -> List[LintViolation]:
        violations: List[LintViolation] = []
        header_len = len(commit.header.strip())

        if header_len > config.max_header_length:
            level = LintLevel.ERROR if config.strict else LintLevel.WARNING
            violations.append(
                LintViolation(
                    rule_id="header-max-length",
                    message=f"Header length ({header_len}) exceeds maximum configured limit of {config.max_header_length}",
                    level=level,
                    line_number=1,
                    suggestion=f"Shorten header by {header_len - config.max_header_length} characters",
                )
            )

        if header_len < config.min_header_length and header_len > 0:
            level = LintLevel.ERROR if config.strict else LintLevel.WARNING
            violations.append(
                LintViolation(
                    rule_id="header-min-length",
                    message=f"Header length ({header_len}) is shorter than minimum required length of {config.min_header_length}",
                    level=level,
                    line_number=1,
                    suggestion="Provide a more descriptive subject",
                )
            )

        return violations


class RuleSubject(BaseRule):
    """Validate subject format, punctuation, and casing."""
    rule_id = "subject-rules"

    def validate(self, commit: CommitMessage, config: LintConfig) -> List[LintViolation]:
        if commit.subject is None:
            return []

        violations: List[LintViolation] = []
        subj = commit.subject.strip()

        if not subj:
            violations.append(
                LintViolation(
                    rule_id="subject-empty",
                    message="Commit subject description must not be empty",
                    level=LintLevel.ERROR,
                    line_number=1,
                    suggestion="Add a concise explanation of the change after the colon",
                )
            )
            return violations

        # Trailing period check
        if config.subject_no_trailing_period and subj.endswith("."):
            violations.append(
                LintViolation(
                    rule_id="subject-full-stop",
                    message="Subject must not end with a trailing period ('.')",
                    level=LintLevel.WARNING,
                    line_number=1,
                    suggestion=f"Remove '.' from '{subj}' -> '{subj[:-1]}'",
                )
            )

        # Subject casing check
        first_char = subj[0]
        if first_char.isalpha():
            if config.subject_case == "lowercase" and first_char.isupper():
                violations.append(
                    LintViolation(
                        rule_id="subject-case",
                        message=f"Subject should start with lowercase letter: '{first_char}'",
                        level=LintLevel.WARNING,
                        line_number=1,
                        suggestion=f"Change '{first_char}' to '{first_char.lower()}'",
                    )
                )
            elif config.subject_case == "sentence-case" and first_char.islower():
                violations.append(
                    LintViolation(
                        rule_id="subject-case",
                        message=f"Subject should start with uppercase letter: '{first_char}'",
                        level=LintLevel.WARNING,
                        line_number=1,
                        suggestion=f"Change '{first_char}' to '{first_char.upper()}'",
                    )
                )

        return violations


class RuleBody(BaseRule):
    """Validate commit body blank line separator and line length."""
    rule_id = "body-rules"

    def validate(self, commit: CommitMessage, config: LintConfig) -> List[LintViolation]:
        violations: List[LintViolation] = []
        raw_lines = commit.raw.replace("\r\n", "\n").split("\n")

        # Check blank line between header and body
        if config.body_blank_line_required and len(raw_lines) > 1:
            second_line = raw_lines[1].strip()
            if second_line:
                violations.append(
                    LintViolation(
                        rule_id="body-leading-blank",
                        message="Commit body must be separated from header by a blank line",
                        level=LintLevel.ERROR,
                        line_number=2,
                        suggestion="Insert an empty line after the commit header",
                    )
                )

        # Line length checks for body
        if commit.body_lines:
            for idx, line in enumerate(commit.body_lines, start=3):
                line_len = len(line)
                if line_len > config.max_body_line_length and not is_url_or_code(line):
                    level = LintLevel.ERROR if config.strict else LintLevel.WARNING
                    violations.append(
                        LintViolation(
                            rule_id="body-max-line-length",
                            message=f"Body line {idx} length ({line_len}) exceeds max allowed ({config.max_body_line_length})",
                            level=level,
                            line_number=idx,
                            suggestion="Wrap long body lines to under 100 characters",
                        )
                    )

        return violations


class RuleTicket(BaseRule):
    """Validate ticket reference presence if required."""
    rule_id = "ticket-rules"

    def validate(self, commit: CommitMessage, config: LintConfig) -> List[LintViolation]:
        if not config.ticket_required:
            return []

        violations: List[LintViolation] = []
        pattern = re.compile(config.ticket_pattern)

        found = False
        target = config.ticket_in

        if target in ("scope", "any") and commit.scope:
            if pattern.search(commit.scope):
                found = True

        if not found and target in ("subject", "any") and commit.subject:
            if pattern.search(commit.subject):
                found = True

        if not found and target in ("footer", "any") and commit.footers:
            for token, value in commit.footers:
                combined = f"{token} {value}"
                if pattern.search(combined):
                    found = True
                    break

        if not found and target == "any" and commit.body:
            if pattern.search(commit.body):
                found = True

        if not found:
            violations.append(
                LintViolation(
                    rule_id="ticket-required",
                    message=f"Ticket reference matching pattern '{config.ticket_pattern}' was not found in [{target}]",
                    level=LintLevel.ERROR,
                    line_number=1,
                    suggestion=f"Reference a valid ticket (e.g. PROJ-123) in {target}",
                )
            )

        return violations


ALL_RULES: List[BaseRule] = [
    RuleHeaderFormat(),
    RuleType(),
    RuleScope(),
    RuleHeaderLength(),
    RuleSubject(),
    RuleBody(),
    RuleTicket(),
]


def is_alphanumeric_scope(scope: str) -> bool:
    """Check if scope contains only alphanumeric characters, dashes, and underscores."""
    return bool(re.match(r"^[A-Za-z0-9_\-]+$", scope))


def is_valid_scope_length(scope: str, min_len: int = 1, max_len: int = 50) -> bool:
    """Check if scope length falls within permitted boundary limits."""
    s = scope.strip()
    return min_len <= len(s) <= max_len

def is_kebab_or_snake(s: str) -> bool:
    """Returns True if string matches valid kebab-case or snake_case format."""
    return bool(re.match(r"^[a-z0-9]+([_\-][a-z0-9]+)*$", s))
