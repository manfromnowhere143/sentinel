import pytest

from tools.ci import verify_ci_install as install
from tools.ci import verify_supply_chain as supply


@pytest.mark.parametrize("minor", ["3.10", "3.11"])
def test_research_lock_retains_cpu_wheel_hashes(minor):
    raw = (supply.ROOT / supply.LOCKS[minor]).read_bytes()
    packages = install.parse_lock_bytes(raw)
    assert packages["torch"][0] == "2.10.0+cpu"
    assert len(packages["torch"][1]) == 1
    assert packages["shapely"][0] == "2.1.2"
    assert supply._parse_lock(raw.decode(), minor)


@pytest.mark.parametrize("replacement", [
    "--find-links https://example.invalid/torch/",
    "--extra-index-url https://download.pytorch.org/whl/cpu/torch/",
    "--trusted-host download.pytorch.org",
])
def test_research_lock_refuses_other_sources_and_options(replacement):
    text = (supply.ROOT / supply.LOCKS["3.11"]).read_text()
    corrupted = replacement + "\n" + text.split("\n", 1)[1]
    with pytest.raises(supply.SupplyChainError):
        supply._parse_lock(corrupted, "3.11")
    with pytest.raises(install.InstallVerificationError):
        install.parse_lock_bytes(corrupted.encode())


def test_research_lock_refuses_duplicate_source_directive():
    text = (supply.ROOT / supply.LOCKS["3.11"]).read_text()
    corrupted = text.split("\n", 1)[0] + "\n" + text
    with pytest.raises(supply.SupplyChainError):
        supply._parse_lock(corrupted, "3.11")
    with pytest.raises(install.InstallVerificationError):
        install.parse_lock_bytes(corrupted.encode())
