# Official nuScenes download reference used for iter26

Source context: operator-provided excerpt from the signed-in nuScenes downloads page on
2026-07-06. Iteration 26 uses this as the official package-size reference for remedy planning
only. It does not download data.

Relevant package: **Full dataset (v1.0) / Trainval / File blobs of 85 scenes, parts 1-10**.

The metadata package is not the blocker; metadata is already present on `sentinel-gpu`. The
missing data class is sensor file blobs, especially the camera files under `samples/CAM_*`.

| package | size GB |
|---|---:|
| File blobs of 85 scenes, part 1 | 29.41 |
| File blobs of 85 scenes, part 2 | 28.06 |
| File blobs of 85 scenes, part 3 | 27.81 |
| File blobs of 85 scenes, part 4 | 29.87 |
| File blobs of 85 scenes, part 5 | 26.25 |
| File blobs of 85 scenes, part 6 | 25.61 |
| File blobs of 85 scenes, part 7 | 27.50 |
| File blobs of 85 scenes, part 8 | 28.19 |
| File blobs of 85 scenes, part 9 | 31.21 |
| File blobs of 85 scenes, part 10 | 38.87 |
| **Total archive-size budget** | **292.78** |

Iter26's frozen capacity bar requires at least 1.25x expected staged bytes before a remedy can
authorize a later staging pre-registration:

`292.78 GB * 1.25 = 365.975 GB`

This is a planning budget, not evidence that the archives are already staged.
