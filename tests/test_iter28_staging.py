from __future__ import annotations

import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter28_nuscenes_trainval_staging/stage_local_archive.py"


def load_staging_module():
    spec = importlib.util.spec_from_file_location("iter28_stage_local_archive", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_signed_url_redaction_drops_query_and_fragment():
    module = load_staging_module()

    redacted = module.redacted_url_source(
        "https://example.com/private/v1.0-trainval04_blobs.tgz"
        "?token=secret&expires=soon#fragment"
    )

    assert redacted == {
        "source_host": "example.com",
        "source_path_basename": "v1.0-trainval04_blobs.tgz",
        "source_scheme": "https",
    }


def test_signed_url_file_must_contain_single_https_url(tmp_path):
    module = load_staging_module()
    url_file = tmp_path / "url.txt"
    url_file.write_text("https://example.com/archive.tgz\nhttps://example.com/other.tgz\n")

    with pytest.raises(SystemExit, match="exactly one URL"):
        module.read_signed_url(url_file)

    url_file.write_text("http://example.com/archive.tgz\n")
    with pytest.raises(SystemExit, match="https URL"):
        module.read_signed_url(url_file)


def test_strip_ssh_destination_removes_tty_and_preserves_proxy_command():
    module = load_staging_module()
    ssh_prefix, destination = module.strip_ssh_destination(
        "/usr/bin/ssh -t -i /tmp/key -o 'ProxyCommand proxy words' user@host"
    )

    assert "-t" not in ssh_prefix
    assert destination == "user@host"
    assert ssh_prefix == [
        "/usr/bin/ssh",
        "-i",
        "/tmp/key",
        "-o",
        "ProxyCommand proxy words",
    ]


def test_rsync_ssh_command_enables_gcloud_site_packages(monkeypatch):
    module = load_staging_module()
    captured = {}

    def fake_run_command(cmd, *, env=None, timeout=None):
        captured["cmd"] = cmd
        captured["env"] = env
        captured["timeout"] = timeout
        return SimpleNamespace(stdout="/usr/bin/ssh -t user@host\n")

    monkeypatch.setattr(module, "run_command", fake_run_command)

    ssh_prefix, destination = module.rsync_ssh_command(
        SimpleNamespace(
            gcloud_prefix=[],
            rsync_transport="iap",
            instance="sentinel-gpu",
            project="test-project",
            zone="us-west1-a",
        )
    )

    assert destination == "user@host"
    assert "-t" not in ssh_prefix
    assert captured["env"]["CLOUDSDK_PYTHON_SITEPACKAGES"] == "1"
    assert captured["cmd"][-1] == "--dry-run"


def test_rsync_ssh_command_can_use_direct_temporary_firewall_path():
    module = load_staging_module()

    ssh_prefix, destination = module.rsync_ssh_command(
        SimpleNamespace(
            direct_host="35.227.136.146",
            direct_known_hosts="/tmp/direct-known-hosts",
            remote_user="danielwahnich",
            rsync_transport="direct",
            ssh_key=Path("/tmp/key"),
        )
    )

    assert destination == "danielwahnich@35.227.136.146"
    assert ssh_prefix[:4] == ["/usr/bin/ssh", "-i", "/tmp/key", "-o"]
    assert "UserKnownHostsFile=/tmp/direct-known-hosts" in ssh_prefix
