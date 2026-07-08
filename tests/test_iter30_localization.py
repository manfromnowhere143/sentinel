from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments/iter30_full_trainval_lowdiv_localization/analyze_localization.py"


def load_module():
    spec = importlib.util.spec_from_file_location("iter30_localization", SCRIPT)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_iter30_label_recompute_distinguishes_primary_classes():
    module = load_module()

    eligible = module.annotate(
        {
            "traj": [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]],
            "objs": [[1.0, 0.0]],
            "futs": [[[[0.0, 0.0], [0.0, 0.0], [0.0, 0.0]]]],
            "cands": [
                [[0.0, 0.0], [1.0, 0.0]],
                [[0.0, 0.0], [1.2, 0.0]],
                [[0.0, 0.0], [1.4, 0.0]],
            ],
        }
    )
    benign = module.annotate(
        {
            "traj": [[0.0, 0.0], [1.0, 0.0], [2.0, 0.0]],
            "objs": [],
            "futs": [],
            "cands": [
                [[0.0, 0.0], [0.0, 0.0]],
                [[0.0, 0.0], [3.0, 0.0]],
                [[0.0, 0.0], [0.0, 3.0]],
            ],
        }
    )

    assert eligible["eligible_lowdiv"]
    assert not eligible["benign_control"]
    assert benign["benign_control"]
    assert not benign["eligible_lowdiv"]


def test_iter30_threshold_tie_chooses_highest_threshold():
    module = load_module()

    threshold, score, ties = module.choose_threshold(
        module.np.asarray([0, 1]), module.np.asarray([0.5, 0.5])
    )

    assert threshold == 1.0
    assert score == 0.5
    assert ties == 3


def test_iter30_specificity_counts_true_negatives():
    module = load_module()

    value = module.specificity(module.np.asarray([0, 0, 1, 1]), module.np.asarray([0, 1, 1, 1]))

    assert value == 0.5


def test_iter30_bootstrap_reports_valid_resamples():
    module = load_module()
    original = module.N_BOOTSTRAP
    module.N_BOOTSTRAP = 20
    try:
        report = module.bootstrap_scene_clusters(
            {
                "heldout_labels": [0, 1, 0, 1],
                "heldout_scores": [0.1, 0.9, 0.2, 0.8],
                "heldout_scenes": ["scene-a", "scene-a", "scene-b", "scene-b"],
                "calibration_threshold": 0.5,
            }
        )
    finally:
        module.N_BOOTSTRAP = original

    assert report["n_resamples"] == 20
    assert report["valid_resamples"] == 20
    assert report["skipped_single_class_resamples"] == 0
    assert report["auc_p05"] == 1.0
