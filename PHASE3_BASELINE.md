# Phase 3.1 — Component Baseline

## Scope and run

This baseline uses the corrected diagnostic evaluation run `20261013T185711.532501+0530`, recorded on 2026-10-13. It evaluated the same 10 pose images for pose detection and person segmentation, plus 10 garment images. Detailed per-image records and generated masks/cutouts are in the ignored `tests/results/` directory.

The 10 pose and 10 garment images are already present under the expected test directories, so no archive was downloaded or files overwritten. Their current filenames match the corrected run. Earlier runs did not record input-file hashes, so historical byte-for-byte identity cannot be independently verified.

| Component | Current implementation | Images processed | Mean time / image |
|---|---|---:|---:|
| Pose detection | MediaPipe Pose | 10/10 | 0.2271 s |
| Person segmentation | MediaPipe Selfie Segmentation, model selection 0; OpenCV GrabCut fallback | 10/10 | 0.0222 s |
| Garment extraction | OpenCV GrabCut with a centered rectangle initialization | 10/10 | 0.2312 s |

These are single-run measurements, not warmed-up repeated benchmarks. They include existing component-call overhead and are initial references, not fair candidate-model latency comparisons.

## Pose detection

The original filenames did not reliably describe their image contents. The 10 images were visually reviewed and relabeled in `tests/pose-detection/pose_labels.csv`; the evaluator now requires this manifest and checks that it covers exactly the discovered pose images. In the manifest, 8 images contain a person and 2 do not.

The evaluator requires usable nose, shoulder, and hip landmarks. A required landmark must pass the current confidence and in-frame checks. The CSV records each required landmark's coordinates, visibility, and in-frame status, along with the model source and whether detection agrees with the visually reviewed person label.

| Image | Verified content | MediaPipe pose | Required landmark visibility (nose, L/R shoulder, L/R hip) | Fit-landmark check |
|---|---|---|---|---|
| `pose_test_1_arms_raised.jpg` | Person, arms raised | Detected; no fallback | 1.00, 1.00, 1.00, 1.00, 0.99 | Passed |
| `pose_test_1_front_facing.jpg` | No person (chair/plant) | Detected; no fallback | 1.00, 1.00, 1.00, 1.00, 1.00 | False positive |
| `pose_test_1_no_person.jpg` | Front-facing person | No pose returned | No landmarks | Missed |
| `pose_test_1_partially_occluded.jpg` | Partially occluded person | Detected; no fallback | 0.98, 0.97, 1.00, 0.60, 0.73 | Passed |
| `pose_test_1_side_pose.jpg` | Side pose | Detected; no fallback | 0.99, 0.99, 1.00, 0.96, 0.97 | Passed |
| `pose_test_2_arms_raised.jpg` | No person (park/bench) | Detected; no fallback | 1.00, 1.00, 1.00, 1.00, 0.99 | False positive |
| `pose_test_2_front_facing.jpg` | Person, arms raised | Detected; no fallback | 1.00, 1.00, 1.00, 1.00, 1.00 | Passed |
| `pose_test_2_no_person.jpg` | Front-facing person | No pose returned | No landmarks | Missed |
| `pose_test_2_partially_occluded.jpg` | Partially occluded person | Detected; no fallback | 1.00, 0.99, 1.00, 0.18, 0.23 | Rejected: both hips below visibility threshold and out of frame |
| `pose_test_2_side_pose.jpg` | Side pose | Detected; no fallback | 1.00, 1.00, 1.00, 1.00, 0.99 | Passed |

Overall, 6/8 images containing people received a pose detection, 5/8 passed the fit-landmark gate, and neither of the 2 empty scenes was rejected. Both false positives came from actual MediaPipe inference, not fallback landmarks; their required-point visibility values were near 1.0, demonstrating that visibility confidence alone does not establish a genuine person. The second partially occluded person was detected but failed required-landmark validation because both hips had visibility below 0.5 and normalized y coordinates beyond the image boundary.

The two missed people produced no landmarks, so per-landmark visibility is unavailable. The code decodes the images as BGR and converts to RGB for MediaPipe; inputs are 303×177 (side-pose samples are 304×177), and no application-level resizing is applied. A diagnostic sweep over `min_detection_confidence` 0.3, 0.5, and 0.7 did not change any of the 10 outcomes. `model_complexity` 0, 1, and 2 also produced the same outcomes. In `static_image_mode=True`, tracking confidence is not used. The pose detector has no fallback path; it reports MediaPipe results or an explicit error.

The checked preprocessing, configured threshold, model-complexity setting, and fallback logic therefore do not explain these errors. The exact cause inside model inference is undetermined; limited image resolution is a hypothesis, not a confirmed cause. No annotated keypoints exist, so anatomical accuracy, PCK, and OKS remain unmeasured.

## Person segmentation

All 10 images returned finite, correctly sized masks and RGBA cutouts using `mediapipe_selfie_segmentation`; the evaluator recorded no fallback warnings. Mean latency was 0.0222 s/image.

The two visually verified no-person images produced foreground fractions of 11.35% and 12.40%. Inspection of their masks shows coherent human-shaped silhouettes rather than only scattered noise. This localizes the empty-scene false foreground to MediaPipe Selfie Segmentation output (no fallback warning), but does not establish why the model produced it. Mask validity only verifies output format and dimensions. No independent person masks are available, so IoU, Dice, precision, recall, foreground completeness, and background leakage are otherwise unmeasured.

The metric-enabled rerun `20261013T191453.437642+0530` reported 6,086 and 6,649 false foreground pixels respectively (mean false foreground 11.87%). It confirmed the same 5/8 positive pose fit-landmark passes and 0/2 empty-scene pose rejections.

The later evaluator run `20261013T193531.720201+0530` used independently verified all-black references for the two confirmed empty scenes. Both passed strict size/binary/empty-scene validation. Their mean IoU, Dice, and precision were 0.0; recall was 1.0 under the evaluator's empty-reference convention, so the separately reported 11.87% false-foreground fraction is the meaningful negative-scene measure. These two negative references do not assess person-boundary quality. Positive-person masks, garment masks, and keypoint annotations are still pending; their metrics remain unavailable.

## Garment extraction

OpenCV GrabCut returned a non-empty, binary mask matching the source dimensions on all 10 images. Per-category processing results and mean times:

| Garment category | Valid masks | Images | Mean time |
|---|---:|---:|---:|
| Dark garment / light background | 2 | 2 | 0.1026 s |
| Light garment / dark background | 2 | 2 | 0.1301 s |
| Similar-colour background | 2 | 2 | 0.3697 s |
| Complex background | 2 | 2 | 0.3202 s |
| Fine straps / outline | 2 | 2 | 0.2334 s |

Valid output shape does not establish accurate garment boundaries. No independent garment masks are available, so IoU, Dice, precision, recall, and boundary accuracy are unmeasured. The two-sample category timings are noisy and are not quality scores.

## Environment and limits

- OS: Windows; CPU: Intel Core i5-11400H; RAM: 7.7 GiB.
- Reported graphics adapter: Intel UHD Graphics; the evaluator did not record GPU inference or peak memory use.
- Inputs: 10 pose/segmentation images and 10 garment images. The sample set is too small to support strong generalization claims.
- No annotated keypoints or positive-person/garment reference masks are present. Only two verified all-black references for the no-person segmentation examples exist.
- No alternative model was run in this baseline.

## Phase 3 decision

The failure analysis rules out fallback landmarks and shows that threshold/model-complexity changes in the tested ranges do not change these pose outcomes. MediaPipe misses both real people in the mislabeled `*_no_person.jpg` files and falsely detects people in both empty scenes; segmentation also produces human-like false foreground on the empty scenes. Do not select or replace models yet. Next create independent person and garment reference masks and, if pose accuracy is to be scored, keypoint annotations. Then use the annotations to compare preprocessing or candidate models. Candidate latency comparisons need warmed-up repeated measurements with model loading recorded separately.
