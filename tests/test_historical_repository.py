from pathlib import Path
import subprocess

from scripts.historical_repository import HISTORICAL_COMMIT, archived_state_errors, git


def test_changed_archived_mission_is_rejected_before_replay(tmp_path: Path) -> None:
    repo = Path(__file__).resolve().parents[1]
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    objects = Path(git(repo, "rev-parse", "--git-common-dir").decode().strip())
    if not objects.is_absolute():
        objects = (repo / objects).resolve()
    (tmp_path / ".git/objects/info/alternates").write_text(str(objects / "objects") + "\n")
    original = git(repo, "show", f"{HISTORICAL_COMMIT}:MISSION_STATE.json")
    (tmp_path / "MISSION_STATE.json").write_bytes(original + b"\n")
    assert archived_state_errors(tmp_path) == [
        "historical mission bytes changed; declare and validate a new contract"
    ]
