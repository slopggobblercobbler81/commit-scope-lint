# commit-scope-lint 🔍

[![CI](https://github.com/slopggobblercobbler81/commit-scope-lint/actions/workflows/ci.yml/badge.svg)](https://github.com/slopggobblercobbler81/commit-scope-lint/actions/workflows/ci.yml)
[![Python Versions](https://img.shields.io/badge/python-3.8%20%7C%203.9%20%7C%203.10%20%7C%203.11%20%7C%203.12-blue)](https://pypi.org/project/commit-scope-lint/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code Style: Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-yellow.svg)](https://conventionalcommits.org)

**commit-scope-lint** is a blazing-fast, production-grade Conventional Commits (v1.0.0) and Scope validation CLI tool. It enforces team conventions, Jira/GitHub ticket tracking, scope casing, breaking change declarations, and git hook policies across your repositories and CI pipelines.

---

## 🌟 Key Features

- ⚡ **Zero Mandatory Dependencies**: Runs on standard Python library (`>=3.8`) for instant installation and lightweight execution.
- 📐 **Strict Conventional Commits 1.0.0**: Validates types, scopes, breaking changes (`!`), headers, bodies, and footers.
- 🎯 **Scope Enforcement & Casing**: Enforce allowed scope lists, mandatory scopes, and casing styles (`kebab-case`, `camelCase`, `snake_case`, `lowercase`, `uppercase`).
- 🎫 **Ticket & Issue Traceability**: Require issue or Jira ticket references (e.g. `JIRA-1234` or `#42`) in scopes, subjects, or footers.
- 🪝 **One-Command Git Hook**: Run `commit-scope-lint hook install` to configure `.git/hooks/commit-msg` automatically with zero friction.
- 🤖 **CI/CD Native**: Direct support for GitHub Actions annotations (`--format github`), Markdown summaries (`--format markdown`), and machine-readable JSON (`--format json`).
- 🌲 **Commit Range & Git History Linting**: Lint PR branch ranges with `--from origin/main --to HEAD` or inspect recent commits with `--last 5`.
- ⚙️ **Multi-format Configuration**: Configure via `.commit-scope-lint.json`, `pyproject.toml`, or `.commit-scope-lint.yaml`.

---

## 📦 Installation

Install via pip:

```bash
pip install commit-scope-lint
```

Or with [pipx](https://pypa.github.io/pipx/) for CLI isolation:

```bash
pipx install commit-scope-lint
```

Or with `uv`:

```bash
uv tool install commit-scope-lint
```

---

## 🚀 Quickstart

### 1. Validate a commit message string

```bash
# Valid commit
commit-scope-lint "feat(auth): implement oauth2 refresh token rotation"

# Invalid commit (returns exit code 1 with actionable suggestions)
commit-scope-lint "fixed some bugs and updated css."
```

### 2. Validate from file (Git Hook target)

```bash
commit-scope-lint --file .git/COMMIT_EDITMSG
```

### 3. Validate PR range in CI

```bash
commit-scope-lint --from origin/main --to HEAD --format github
```

### 4. Automatically install git `commit-msg` hook

```bash
commit-scope-lint hook install
```

---

## 📋 CLI Usage & Options

```text
usage: commit-scope-lint [-h] [-m FLAG_MESSAGE] [-f FILE] [--from FROM_REV]
                         [--to TO_REV] [--last N] [-c CONFIG]
                         [--format {terminal,json,github,markdown}] [--strict]
                         [--warn-only] [-q] [-v]
                         [message]

Positional Arguments:
  message               Commit message text or '-' to read from stdin.

Flags:
  -m, --message-arg     Explicit commit message string.
  -f, --file            Path to file containing commit message or '-' for stdin.
  --from FROM_REV       Starting git commit revision or branch for range linting.
  --to TO_REV           Ending git commit revision or branch (default: HEAD).
  --last N              Lint the last N git commits on the current branch.
  -c, --config          Path to configuration file.
  --format FORMAT       Output format: terminal (default), json, github, markdown.
  --strict              Treat all warnings as fatal errors.
  --warn-only           Return exit code 0 even if violations are present.
  -q, --quiet           Suppress non-error output.
  -v, --version         Show program version and exit.

Subcommands:
  commit-scope-lint hook install [--force]   Install commit-msg git hook
  commit-scope-lint hook uninstall           Remove commit-msg git hook
  commit-scope-lint hook status              Inspect hook installation state
  commit-scope-lint init [-o PATH]           Scaffold starter config file
```

---

## 🛠️ Configuration

Initialize a starter configuration file:

```bash
commit-scope-lint init
```

This creates `.commit-scope-lint.json`:

```json
{
  "types": [
    "feat",
    "fix",
    "docs",
    "style",
    "refactor",
    "perf",
    "test",
    "build",
    "ci",
    "chore",
    "revert"
  ],
  "scopes": ["core", "api", "cli", "deps", "docs", "test"],
  "scope_required": false,
  "scope_case": "kebab-case",
  "ticket_required": false,
  "ticket_pattern": "[A-Z]{2,10}-\\d+",
  "ticket_in": "any",
  "max_header_length": 72,
  "min_header_length": 10,
  "max_body_line_length": 100,
  "subject_case": "lowercase",
  "subject_no_trailing_period": true,
  "body_blank_line_required": true,
  "strict": false
}
```

### Configuring via `pyproject.toml`

You can also embed configuration directly in `pyproject.toml`:

```toml
[tool.commit_scope_lint]
scopes = ["api", "client", "infra", "docs"]
scope_required = true
scope_case = "kebab-case"
ticket_required = true
ticket_pattern = "^(PROJ|ENG)-\\d+$"
ticket_in = "scope"
max_header_length = 72
```

---

## 🛡️ Built-in Rule Index

| Rule ID | Level | Description |
| :--- | :--- | :--- |
| `header-empty` | **ERROR** | Commit message header cannot be empty. |
| `header-format` | **ERROR** | Header must follow `<type>[(<scope>)][!]: <subject>`. |
| `type-enum` | **ERROR** | Type must be in configured allowed types list. |
| `type-case` | **ERROR** | Type prefix must be lowercase. |
| `scope-required` | **ERROR** | Scope is required when `scope_required: true`. |
| `scope-enum` | **ERROR** | Scope must match declared allowed scopes. |
| `scope-case` | **WARN / ERROR** | Scope must adhere to casing rule (`kebab-case`, etc.). |
| `header-max-length`| **WARN / ERROR** | Header exceeds maximum allowed length (default: 72). |
| `header-min-length`| **WARN / ERROR** | Header shorter than minimum required length (default: 10). |
| `subject-empty` | **ERROR** | Subject description cannot be empty. |
| `subject-case` | **WARN** | Subject should start in lowercase (or sentence-case). |
| `subject-full-stop`| **WARN** | Subject must not terminate with a period (`.`). |
| `body-leading-blank`| **ERROR** | Blank line required between header and body. |
| `body-max-line-length`| **WARN / ERROR**| Body line length limit (exempts URLs and code blocks). |
| `ticket-required` | **ERROR** | Required ticket pattern was not matched in scope/footer. |

---

## 🤖 CI/CD Integration

### GitHub Actions Workflow

Add `.github/workflows/commit-lint.yml`:

```yaml
name: Lint Commits

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install commit-scope-lint
        run: pip install commit-scope-lint

      - name: Lint Pull Request Commits
        run: |
          commit-scope-lint --from ${{ github.event.pull_request.base.sha }} \
                            --to ${{ github.event.pull_request.head.sha }} \
                            --format github
```

---

## 🪝 Pre-commit Hook Integration

Add to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/slopggobblercobbler81/commit-scope-lint
    rev: v1.0.0
    hooks:
      - id: commit-scope-lint
        stages: [commit-msg]
```

---

## 🏗️ Architecture Overview

```
commit_scope_lint/
├── __init__.py         # Package exports & version
├── __main__.py         # python -m commit_scope_lint runner
├── cli.py              # CLI argument parser & subcommand routing
├── config.py           # Configuration schema, discovery & loaders
├── formatters.py       # Terminal (ANSI), JSON, GitHub Actions & Markdown formatters
├── git_utils.py        # Subprocess git interaction & delimiter-safe log parsing
├── hook.py             # Git commit-msg hook installer & lifecycle
├── linter.py           # Core linting orchestration engine
├── models.py           # Dataclasses (CommitMessage, LintViolation, LintResult)
├── py.typed            # PEP 561 typing marker
└── rules.py            # Modular validation rules
```

---

## 🧪 Development & Testing

```bash
# Clone the repository
git clone https://github.com/slopggobblercobbler81/commit-scope-lint.git
cd commit-scope-lint

# Install development dependencies
pip install -e ".[dev]"

# Run test suite with pytest & coverage
pytest --cov=commit_scope_lint --cov-report=term-missing
```

---

## 📄 License

This project is licensed under the terms of the [MIT License](LICENSE).
