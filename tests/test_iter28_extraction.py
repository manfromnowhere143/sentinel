from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter28_nuscenes_trainval_staging/extract_archives.py"


def load_extract_module():
    spec = importlib.util.spec_from_file_location("iter28_extract_archives", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_expected_archive_set_is_complete_and_ordered():
    module = load_extract_module()

    assert module.EXPECTED_ARCHIVES[0] == "v1.0-trainval_meta.tgz"
    assert module.EXPECTED_ARCHIVES[1:] == tuple(
        f"v1.0-trainval{i:02d}_blobs.tgz" for i in range(1, 11)
    )


def test_member_safety_accepts_regular_nuscenes_paths():
    module = load_extract_module()

    assert module.safety_reason("samples/CAM_FRONT/n015-2018.jpg") is None
    assert module.safety_reason("v1.0-trainval/scene.json") is None


def test_member_safety_rejects_path_traversal_and_absolute_names():
    module = load_extract_module()

    assert module.safety_reason("../escape") == "parent traversal in member path"
    assert module.safety_reason("samples/../../escape") == "parent traversal in member path"
    assert module.safety_reason("/tmp/escape") == "absolute member path"


def test_member_safety_rejects_escaping_links():
    module = load_extract_module()

    assert module.safety_reason("samples/link", linkname="/etc/passwd") == "absolute link target"
    assert (
        module.safety_reason("samples/CAM_FRONT/link", linkname="../../escape")
        == "parent traversal in link target"
    )


def test_remote_extractor_template_is_redacted_and_configured():
    module = load_extract_module()
    rendered = module.render_remote_extractor(module.DEST_ROOT)

    assert module.DEST_ROOT in rendered
    assert "v1.0-trainval10_blobs.tgz" in rendered
    assert "signed" not in rendered.lower()
    assert "cookie" not in rendered.lower()
