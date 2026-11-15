from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path

import pytest


INSTALLER = Path(__file__).parents[1] / "tools" / "install_computer_vision_models.py"
SPEC = spec_from_file_location("asthral_cv_model_installer", INSTALLER)
MODULE = module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(MODULE)


def test_echo_asset_download_fails_closed_before_touching_disk(tmp_path, monkeypatch):
    monkeypatch.setattr(MODULE, "ROOT", tmp_path / "computer-vision")
    assert "echo" not in MODULE.ASSETS
    with pytest.raises(PermissionError, match="written permission"):
        MODULE.install("echo")
    assert not MODULE.ROOT.exists()


def test_install_all_contains_only_assets_with_reviewed_provenance():
    assert set(MODULE.ASSETS) == {"oct", "motion"}
    assert "echo" in MODULE.BLOCKED_ASSETS
