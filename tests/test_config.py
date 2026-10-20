"""Tests for configuration loading and serialization."""

import json
from pathlib import Path
import pytest
from commit_scope_lint.config import (
    LintConfig,
    _parse_pyproject_toml,
    find_config_file,
    load_config,
)


def test_default_config():
    config = LintConfig()
    assert "feat" in config.types
    assert "fix" in config.types
    assert config.max_header_length == 72
    assert config.scope_required is False
    assert config.strict is False


def test_config_serialization():
    config = LintConfig(scopes=["cli", "api"], scope_required=True)
    d = config.to_dict()
    assert d["scopes"] == ["cli", "api"]
    assert d["scope_required"] is True

    json_str = config.to_json()
    reloaded = LintConfig.from_dict(json.loads(json_str))
    assert reloaded.scopes == ["cli", "api"]
    assert reloaded.scope_required is True


def test_load_json_config(tmp_path: Path):
    cfg_file = tmp_path / ".commit-scope-lint.json"
    data = {
        "types": ["feature", "bugfix"],
        "max_header_length": 50,
        "scope_case": "lowercase",
    }
    cfg_file.write_text(json.dumps(data), encoding="utf-8")

    loaded = load_config(str(cfg_file))
    assert loaded.types == ["feature", "bugfix"]
    assert loaded.max_header_length == 50
    assert loaded.scope_case == "lowercase"


def test_load_yaml_config(tmp_path: Path):
    cfg_file = tmp_path / ".commit-scope-lint.yaml"
    cfg_file.write_text("types:\n  - custom\nmax_header_length: 60\n", encoding="utf-8")

    loaded = load_config(str(cfg_file))
    assert loaded.types == ["custom"]
    assert loaded.max_header_length == 60


def test_parse_pyproject_toml():
    toml_content = """
[build-system]
requires = ["setuptools"]

[tool.commit_scope_lint]
max_header_length = 80
scope_required = true
types = ["feat", "fix", "chore"]
"""
    parsed = _parse_pyproject_toml(toml_content)
    assert parsed is not None
    assert parsed["max_header_length"] == 80
    assert parsed["scope_required"] is True
    assert parsed["types"] == ["feat", "fix", "chore"]


def test_find_config_file_not_found():
    with pytest.raises(FileNotFoundError):
        find_config_file("non_existent_file.json")
