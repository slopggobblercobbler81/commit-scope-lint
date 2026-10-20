"""Configuration loader and schema for commit-scope-lint."""

import json
import os
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

DEFAULT_TYPES = [
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
]

DEFAULT_IGNORE_PATTERNS = [
    r"^Merge (branch|tag|pull request|remote-tracking branch)",
    r"^Revert \"",
    r"^Initial commit",
    r"^Version bump",
    r"^chore\(release\):",
    r"^[0-9]+\.[0-9]+\.[0-9]+",
]


@dataclass
class LintConfig:
    """Configuration settings for commit-scope-lint."""
    types: List[str] = field(default_factory=lambda: list(DEFAULT_TYPES))
    scopes: Optional[List[str]] = None
    scope_required: bool = False
    scope_case: str = "kebab-case"  # kebab-case, lowercase, camelCase, snake_case, uppercase, any
    ticket_required: bool = False
    ticket_pattern: str = r"[A-Z]{2,10}-\d+"
    ticket_in: str = "any"  # scope, footer, subject, any
    max_header_length: int = 72
    min_header_length: int = 10
    max_body_line_length: int = 100
    subject_case: str = "lowercase"  # lowercase, sentence-case, any
    subject_no_trailing_period: bool = True
    body_blank_line_required: bool = True
    ignore_patterns: List[str] = field(default_factory=lambda: list(DEFAULT_IGNORE_PATTERNS))
    strict: bool = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "LintConfig":
        """Instantiate LintConfig from a dictionary with type safety."""
        valid_keys = {
            "types",
            "scopes",
            "scope_required",
            "scope_case",
            "ticket_required",
            "ticket_pattern",
            "ticket_in",
            "max_header_length",
            "min_header_length",
            "max_body_line_length",
            "subject_case",
            "subject_no_trailing_period",
            "body_blank_line_required",
            "ignore_patterns",
            "strict",
        }
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return asdict(self)

    def to_json(self, indent: int = 2) -> str:
        """Serialize configuration to formatted JSON."""
        return json.dumps(self.to_dict(), indent=indent)


def find_config_file(explicit_path: Optional[str] = None) -> Optional[Path]:
    """Find configuration file from explicit path or common repository locations."""
    if explicit_path:
        p = Path(explicit_path)
        if p.is_file():
            return p
        raise FileNotFoundError(f"Specified configuration file not found: {explicit_path}")

    # Search current working directory and parents
    search_names = [
        ".commit-scope-lint.json",
        ".commit-scope-lint.yaml",
        ".commit-scope-lint.yml",
        "commit-scope-lint.json",
        "pyproject.toml",
    ]

    cwd = Path.cwd()
    for name in search_names:
        candidate = cwd / name
        if candidate.is_file():
            return candidate

    return None


def _parse_pyproject_toml(content: str) -> Optional[Dict[str, Any]]:
    """Parse tool.commit_scope_lint section from pyproject.toml."""
    try:
        import tomllib  # type: ignore # Python 3.11+
        data = tomllib.loads(content)
        return data.get("tool", {}).get("commit_scope_lint")
    except ImportError:
        pass

    try:
        import tomli  # type: ignore
        data = tomli.loads(content)
        return data.get("tool", {}).get("commit_scope_lint")
    except ImportError:
        pass

    try:
        import toml  # type: ignore
        data = toml.loads(content)
        return data.get("tool", {}).get("commit_scope_lint")
    except ImportError:
        pass

    # Simple regex fallback parser for basic [tool.commit_scope_lint] key-values
    in_section = False
    result: Dict[str, Any] = {}
    for line in content.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            in_section = (line == "[tool.commit_scope_lint]")
            continue
        if in_section and "=" in line:
            key, val = [x.strip() for x in line.split("=", 1)]
            try:
                result[key] = json.loads(val)
            except Exception:
                result[key] = val.strip("\"'")
    return result if result else None


def load_config(path: Optional[str] = None) -> LintConfig:
    """Load LintConfig from path or defaults."""
    config_file = find_config_file(path)
    if not config_file:
        return LintConfig()

    content = config_file.read_text(encoding="utf-8")
    
    if config_file.suffix == ".json":
        data = json.loads(content)
        return LintConfig.from_dict(data)

    if config_file.suffix in (".yaml", ".yml"):
        try:
            import yaml
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                return LintConfig.from_dict(data)
        except ImportError:
            raise RuntimeError("PyYAML must be installed to read .yaml configuration files.")

    if config_file.name == "pyproject.toml":
        section = _parse_pyproject_toml(content)
        if section and isinstance(section, dict):
            return LintConfig.from_dict(section)

    return LintConfig()
