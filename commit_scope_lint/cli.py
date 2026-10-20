"""Command line interface for commit-scope-lint."""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Tuple

from . import __version__
from .config import LintConfig, load_config
from .formatters import (
    format_github,
    format_json,
    format_markdown,
    format_terminal,
)
from .git_utils import (
    get_commit_message_from_file,
    get_commit_range,
    get_last_n_commits,
    read_stdin,
)
from .hook import hook_status, install_hook, uninstall_hook
from .linter import CommitLinter
from .models import LintSuiteResult


def build_lint_parser() -> argparse.ArgumentParser:
    """Construct argument parser for commit validation."""
    parser = argparse.ArgumentParser(
        prog="commit-scope-lint",
        description="Fast, production-grade Conventional Commits & Scope Linter CLI.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Validate a message directly
  commit-scope-lint "feat(api): add auth endpoint"

  # Validate from git commit-msg hook file
  commit-scope-lint --file .git/COMMIT_EDITMSG

  # Validate stdin
  git log -1 --pretty=%%B | commit-scope-lint -

  # Validate last 5 commits
  commit-scope-lint --last 5

  # Validate a PR branch against main
  commit-scope-lint --from origin/main --to HEAD --format github

  # Install git hook automatically
  commit-scope-lint hook install
""",
    )

    parser.add_argument(
        "message",
        nargs="?",
        default=None,
        help="Commit message text or '-' to read from standard input.",
    )

    parser.add_argument(
        "-m", "--message-arg",
        dest="flag_message",
        help="Explicit commit message string.",
    )

    parser.add_argument(
        "-f", "--file",
        help="Path to file containing commit message (e.g. .git/COMMIT_EDITMSG) or '-' for stdin.",
    )

    parser.add_argument(
        "--from",
        dest="from_rev",
        help="Starting git commit revision or branch for range linting.",
    )

    parser.add_argument(
        "--to",
        dest="to_rev",
        default="HEAD",
        help="Ending git commit revision or branch for range linting (default: HEAD).",
    )

    parser.add_argument(
        "--last",
        type=int,
        metavar="N",
        help="Lint the last N git commits on the current branch.",
    )

    parser.add_argument(
        "-c", "--config",
        help="Path to custom configuration file (.json, .yaml, or pyproject.toml).",
    )

    parser.add_argument(
        "--format",
        choices=["terminal", "json", "github", "markdown"],
        default="terminal",
        help="Output report format (default: terminal).",
    )

    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat all warnings as errors.",
    )

    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="Return exit code 0 even if linting violations are found.",
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode: suppress non-error output.",
    )

    parser.add_argument(
        "-v", "--version",
        action="version",
        version=f"commit-scope-lint {__version__}",
    )

    return parser


def build_hook_parser() -> argparse.ArgumentParser:
    """Construct argument parser for git hook management."""
    parser = argparse.ArgumentParser(
        prog="commit-scope-lint hook",
        description="Manage git commit-msg hook.",
    )
    parser.add_argument(
        "action",
        choices=["install", "uninstall", "status"],
        help="Hook operation to perform.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force overwrite of existing git hook if already present.",
    )
    return parser


def build_init_parser() -> argparse.ArgumentParser:
    """Construct argument parser for config file initialization."""
    parser = argparse.ArgumentParser(
        prog="commit-scope-lint init",
        description="Create a starter configuration file.",
    )
    parser.add_argument(
        "-o", "--output",
        default=".commit-scope-lint.json",
        help="Path where configuration will be created (default: .commit-scope-lint.json).",
    )
    return parser


def handle_hook_command(args: argparse.Namespace) -> int:
    """Handle hook subcommand execution."""
    action = args.action
    if action == "install":
        success, msg = install_hook(force=args.force)
        print(msg)
        return 0 if success else 1
    elif action == "uninstall":
        success, msg = uninstall_hook()
        print(msg)
        return 0 if success else 1
    elif action == "status":
        status = hook_status()
        if status["installed"]:
            managed = "managed by commit-scope-lint" if status["is_managed_by_commit_scope_lint"] else "custom hook"
            print(f"Hook installed at: {status['path']} ({managed})")
            return 0
        else:
            print(f"No hook installed ({status['reason']})")
            return 1
    return 1


def handle_init_command(args: argparse.Namespace) -> int:
    """Handle init subcommand execution."""
    out_path = Path(args.output)
    if out_path.exists():
        print(f"Error: Configuration file already exists at {out_path}")
        return 2

    config = LintConfig(
        types=[
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
            "revert",
        ],
        scopes=["core", "api", "cli", "deps", "docs", "test"],
        scope_required=False,
        scope_case="kebab-case",
        ticket_required=False,
        ticket_pattern=r"[A-Z]{2,10}-\d+",
        max_header_length=72,
        min_header_length=10,
        max_body_line_length=100,
        subject_case="lowercase",
        subject_no_trailing_period=True,
    )

    out_path.write_text(config.to_json(indent=2) + "\n", encoding="utf-8")
    print(f"✔ Initialized configuration at {out_path}")
    return 0


def render_output(suite: LintSuiteResult, fmt: str, quiet: bool = False) -> str:
    """Render suite result with designated formatter."""
    if fmt == "json":
        return format_json(suite)
    elif fmt == "github":
        return format_github(suite)
    elif fmt == "markdown":
        return format_markdown(suite)
    return format_terminal(suite, quiet=quiet)


def safe_print(text: str) -> None:
    """Print text with fallback for non-UTF8 terminals."""
    try:
        print(text)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "ascii"
        encoded = text.encode(encoding, errors="replace").decode(encoding)
        print(encoded)


def main(argv: Optional[List[str]] = None) -> int:
    """Main CLI entrypoint."""
    if sys.platform == "win32":
        try:
            if hasattr(sys.stdout, "reconfigure"):
                sys.stdout.reconfigure(encoding="utf-8", errors="replace")
            if hasattr(sys.stderr, "reconfigure"):
                sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass

    args_list = sys.argv[1:] if argv is None else argv

    if args_list and args_list[0] == "hook":
        hook_parser = build_hook_parser()
        hook_args = hook_parser.parse_args(args_list[1:])
        return handle_hook_command(hook_args)

    if args_list and args_list[0] == "init":
        init_parser = build_init_parser()
        init_args = init_parser.parse_args(args_list[1:])
        return handle_init_command(init_args)

    parser = build_lint_parser()
    args = parser.parse_args(args_list)

    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        sys.stderr.write(f"Configuration Error: {e}\n")
        return 2

    if args.strict:
        config.strict = True

    linter = CommitLinter(config)
    commits_to_lint: List[Tuple[str, str, str]] = []
    strip_comments = False

    # Collect commits
    if args.from_rev:
        try:
            commits_to_lint = get_commit_range(args.from_rev, args.to_rev)
        except Exception as e:
            sys.stderr.write(f"Git Range Error: {e}\n")
            return 2
    elif args.last is not None:
        try:
            commits_to_lint = get_last_n_commits(args.last)
        except Exception as e:
            sys.stderr.write(f"Git Log Error: {e}\n")
            return 2
    elif args.file:
        strip_comments = True
        try:
            if args.file == "-":
                raw_text = read_stdin()
            else:
                raw_text = get_commit_message_from_file(args.file)
            commits_to_lint = [("", "", raw_text)]
        except Exception as e:
            sys.stderr.write(f"File Error: {e}\n")
            return 2
    elif args.flag_message:
        commits_to_lint = [("", "", args.flag_message)]
    elif args.message:
        if args.message == "-":
            raw_text = read_stdin()
            strip_comments = True
            commits_to_lint = [("", "", raw_text)]
        else:
            commits_to_lint = [("", "", args.message)]
    else:
        # Check if stdin is available and piped
        try:
            is_tty = sys.stdin.isatty()
            if not is_tty:
                raw_text = sys.stdin.read()
                if raw_text.strip():
                    strip_comments = True
                    commits_to_lint = [("", "", raw_text)]
        except Exception:
            pass

    if not commits_to_lint:
        parser.print_help(sys.stderr)
        return 2

    # Execute linting
    suite = linter.lint_commits(commits_to_lint, strip_comments=strip_comments)
    output = render_output(suite, args.format, quiet=args.quiet)
    if output.strip():
        safe_print(output)

    if args.warn_only:
        return 0

    return 0 if suite.success else 1


if __name__ == "__main__":
    sys.exit(main())
