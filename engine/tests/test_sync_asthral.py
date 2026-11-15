import os
import shutil
import subprocess
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
SYNC_SCRIPT = ROOT / "engine" / "tools" / "sync_asthral.ps1"
POWERSHELL = shutil.which("pwsh") or shutil.which("powershell")
BRANCH = "feature/sync-test"


def git(cwd: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(cwd), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


@pytest.fixture
def two_computers(tmp_path):
    if os.name != "nt" or not POWERSHELL:
        pytest.skip("PowerShell is required for the Windows sync helper")
    remote = tmp_path / "remote.git"
    first = tmp_path / "computer-a"
    second = tmp_path / "computer-b"
    subprocess.run(["git", "init", "--bare", "--initial-branch", BRANCH, str(remote)], check=True, capture_output=True)
    subprocess.run(["git", "init", "--initial-branch", BRANCH, str(first)], check=True, capture_output=True)
    git(first, "config", "user.name", "Sync Test")
    git(first, "config", "user.email", "sync-test@example.invalid")
    (first / "state.txt").write_text("base\n", encoding="utf-8")
    git(first, "add", "--", "state.txt")
    git(first, "commit", "-m", "initial state")
    git(first, "remote", "add", "origin", str(remote))
    git(first, "push", "-u", "origin", BRANCH)
    subprocess.run(["git", "clone", "--branch", BRANCH, str(remote), str(second)], check=True, capture_output=True)
    git(second, "config", "user.name", "Sync Test B")
    git(second, "config", "user.email", "sync-test-b@example.invalid")
    return first, second


def run_sync(repo: Path, *arguments: str) -> subprocess.CompletedProcess:
    script_literal = "'" + str(SYNC_SCRIPT).replace("'", "''") + "'"
    extra = " ".join(arguments)
    command = f"& {script_literal} {extra}; exit $LASTEXITCODE"
    return subprocess.run(
        [POWERSHELL, "-NoProfile", "-Command", command],
        cwd=repo,
        capture_output=True,
        text=True,
        timeout=30,
    )


def backup_branches(repo: Path) -> list[str]:
    return git(repo, "branch", "--list", f"backup/pre-sync/{BRANCH}/*").splitlines()


def test_fast_forward_updates_only_current_branch_and_keeps_backup(two_computers):
    first, second = two_computers
    (second / "state.txt").write_text("from computer b\n", encoding="utf-8")
    git(second, "add", "--", "state.txt")
    git(second, "commit", "-m", "remote update")
    git(second, "push")

    result = run_sync(first)
    assert result.returncode == 0, result.stdout + result.stderr
    assert (first / "state.txt").read_text(encoding="utf-8") == "from computer b\n"
    assert backup_branches(first)
    assert git(first, "rev-parse", "HEAD") == git(first, "rev-parse", f"origin/{BRANCH}")


def test_dirty_local_edits_stop_before_updating_and_remain_intact(two_computers):
    first, second = two_computers
    (second / "state.txt").write_text("remote version\n", encoding="utf-8")
    git(second, "add", "--", "state.txt")
    git(second, "commit", "-m", "remote update")
    git(second, "push")
    (first / "state.txt").write_text("uncommitted local version\n", encoding="utf-8")
    before = git(first, "rev-parse", "HEAD")

    result = run_sync(first)
    assert result.returncode == 2, result.stdout + result.stderr
    assert git(first, "rev-parse", "HEAD") == before
    assert (first / "state.txt").read_text(encoding="utf-8") == "uncommitted local version\n"


def test_incoming_deletion_stops_and_preserves_file_and_branch(two_computers):
    first, second = two_computers
    git(second, "rm", "--", "state.txt")
    git(second, "commit", "-m", "remote deletion")
    git(second, "push")
    before = git(first, "rev-parse", "HEAD")

    result = run_sync(first)
    assert result.returncode == 3, result.stdout + result.stderr
    assert git(first, "rev-parse", "HEAD") == before
    assert (first / "state.txt").is_file()
    assert backup_branches(first)
    assert "state.txt" in result.stdout


def test_diverged_commits_are_preserved_without_automatic_merge(two_computers):
    first, second = two_computers
    (second / "state.txt").write_text("remote version\n", encoding="utf-8")
    git(second, "add", "--", "state.txt")
    git(second, "commit", "-m", "remote update")
    git(second, "push")
    (first / "state.txt").write_text("local commit\n", encoding="utf-8")
    git(first, "add", "--", "state.txt")
    git(first, "commit", "-m", "local update")
    before = git(first, "rev-parse", "HEAD")

    result = run_sync(first)
    assert result.returncode == 3, result.stdout + result.stderr
    assert git(first, "rev-parse", "HEAD") == before
    assert (first / "state.txt").read_text(encoding="utf-8") == "local commit\n"
    assert backup_branches(first)
