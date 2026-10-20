"""Tests for the command-line interface."""

import json
from pathlib import Path
import pytest
from commit_scope_lint.cli import main


def test_cli_valid_message_positional(capsys):
    ret = main(["feat(test): add cli tests"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "PASS" in captured.out


def test_cli_invalid_message(capsys):
    ret = main(["bad commit header missing type"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.out


def test_cli_file_option(tmp_path: Path, capsys):
    msg_file = tmp_path / "COMMIT_EDITMSG"
    msg_file.write_text("fix(cli): resolve exit code on error\n\n# git comments\n", encoding="utf-8")
    ret = main(["--file", str(msg_file)])
    assert ret == 0
    captured = capsys.readouterr()
    assert "PASS" in captured.out


def test_cli_json_format(capsys):
    ret = main(["feat(core): test json output", "--format", "json"])
    assert ret == 0
    captured = capsys.readouterr()
    assert '"success": true' in captured.out


def test_cli_github_format(capsys):
    ret = main(["bad message", "--format", "github"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "::error" in captured.out


def test_cli_markdown_format(capsys):
    ret = main(["feat(ci): test markdown output", "--format", "markdown"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "## 🔍 Commit Scope Lint Report" in captured.out


def test_cli_strict_flag(capsys):
    # Trailing period is a warning, strict converts to error (exit 1)
    ret = main(["feat(core): trailing period warning.", "--strict"])
    assert ret == 1
    captured = capsys.readouterr()
    assert "FAIL" in captured.out


def test_cli_quiet_flag(capsys):
    ret = main(["feat(core): perfectly valid commit", "--quiet"])
    assert ret == 0
    captured = capsys.readouterr()
    assert captured.out.strip() == ""


def test_cli_warn_only(capsys):
    ret = main(["bad commit message", "--warn-only"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "FAIL" in captured.out


def test_cli_init_command(tmp_path: Path, capsys):
    target = tmp_path / "custom-config.json"
    ret = main(["init", "-o", str(target)])
    assert ret == 0
    assert target.is_file()
    captured = capsys.readouterr()
    assert "Initialized configuration" in captured.out

    # Running init again should fail without overwrite
    ret2 = main(["init", "-o", str(target)])
    assert ret2 == 2


def test_cli_no_args_shows_help(capsys):
    ret = main([])
    assert ret == 2


def test_cli_custom_config(tmp_path: Path, capsys):
    cfg_file = tmp_path / ".commit-scope-lint.json"
    cfg_data = {
        "scope_required": True,
        "scopes": ["ui", "backend"]
    }
    cfg_file.write_text(json.dumps(cfg_data), encoding="utf-8")

    # Missing scope should fail with custom config
    ret = main(["feat: missing scope", "-c", str(cfg_file)])
    assert ret == 1
    captured = capsys.readouterr()
    assert "scope-required" in captured.out

    # Valid scope with custom config
    ret_ok = main(["feat(ui): valid scope", "-c", str(cfg_file)])
    assert ret_ok == 0


def test_cli_hook_subcommands(tmp_path: Path, monkeypatch, capsys):
    # Mock current working dir to tmp_path with a fake .git
    git_dir = tmp_path / ".git"
    git_dir.mkdir()
    monkeypatch.setattr("commit_scope_lint.hook.get_repo_root", lambda: tmp_path)

    # Status before install
    ret_status1 = main(["hook", "status"])
    assert ret_status1 == 1

    # Install
    ret_install = main(["hook", "install"])
    assert ret_install == 0

    # Status after install
    ret_status2 = main(["hook", "status"])
    assert ret_status2 == 0

    # Uninstall
    ret_uninst = main(["hook", "uninstall"])
    assert ret_uninst == 0
