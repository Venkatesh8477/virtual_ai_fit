# Project Logs

Track each problem found while working on the project and the solution ultimately used.

## Entries

For each issue, record:
- **Date**
- **Problem**
- **Solution used**
- **Verification**

### Phase 1:

**Priority and order:** Work locally through pose detection and metrics, then person segmentation, then garment extraction. Colab is out of scope.

### Entry 1: MediaPipe Pose Detection — Reliability of Landmark Detection

* **Date:** 2026-10-13
* **Problem:** The pose detection module uses MediaPipe Pose to identify human body landmarks. However, when MediaPipe is unavailable, pose processing fails, or a person cannot be detected, the implementation falls back to generating approximate landmarks using `generate_fallback_pose`. This can make the system return plausible-looking coordinates even when actual pose detection has failed. Consequently, downstream processing may use inaccurate landmarks without distinguishing them from genuine detections.
* **Solution used:** Removed synthetic fallback landmarks. The detector now returns `detected` or `not_detected`, an explicit reason on no detection, and no fabricated points or metrics. Invalid images map to HTTP 422; unavailable or failed MediaPipe inference maps to HTTP 503. Try-on refuses to proceed when no pose is detected.
* **Verification:** Six focused `unittest` checks pass. The original image-name-based test report said MediaPipe detected 8 and the two `*_no_person.jpg` files returned zero landmarks; later visual review established that those two files contain people. The detector's outputs were observed, but this earlier run did not establish no-person behavior. API checks confirmed no-person try-on returns HTTP 422, invalid images return HTTP 422, and simulated MediaPipe unavailability returns HTTP 503.

### Entry 2: MediaPipe Pose Detection — Landmark Accuracy

* **Date:** 2026-10-13
* **Problem:** The virtual try-on pipeline depends on body landmarks such as the nose, shoulders, and hips to position and scale garments. Inaccurate or missing landmarks can result in incorrect garment placement, particularly when the person is photographed from an unusual angle, is partially outside the frame, or has their body obscured.
* **Solution used:** Each returned landmark now includes its visibility, in-frame status, and `usable_for_measurement` flag. Usability requires visibility of at least 0.5 and normalized image coordinates within `[0, 1]`; raw coordinates are preserved. Measurements exclude unusable points, and try-on is rejected if the nose, shoulders, or hips needed for fitting are unusable.
* **Verification:** On the 10 supplied images, low-visibility/out-of-frame points were flagged. Seven images passed the fit-landmark gate; the second partially occluded image was rejected because both hips were unreliable. The later visual review found that the two files named `*_no_person.jpg` contain people and two other files contain empty scenes; some earlier image-category interpretations are therefore superseded by the corrected Phase 3.1 results. This confidence gate indicates model visibility only; it does not prove anatomical correctness.

### Entry 3: MediaPipe Pose Detection — Body Measurement Reliability

* **Date:** 2026-10-13
* **Problem:** The body-metrics implementation derives distances from image-space landmarks and estimates measurements in centimetres. Pixel distances alone cannot establish reliable real-world dimensions without appropriate calibration or additional assumptions. Measurements may vary with camera distance, perspective, body orientation, and image cropping.
* **Solution used:** Removed centimetre values based on the assumed 42 cm shoulder width. Metrics now use image pixels only, omit a metric when its required landmarks are unusable, and label the waist line and silhouette category as estimates. The result page now displays pixels and explains that values are not calibrated.
* **Verification:** Unit tests confirm missing/low-confidence landmarks yield unavailable metrics and no centimetre fields. A local front-facing try-on returned HTTP 200 with `measurement_units: pixels`; frontend production build passed. Real-world centimetres remain out of scope until calibration or a reference object is available.

### Entry 4: Person Segmentation — Output Quality and Reliability

* **Date:** 2026-10-13
* **Problem:** The backend includes a person-segmentation module, but its output quality and reliability have not yet been established through runtime testing. Segmentation errors around hair, arms, clothing, and the boundaries between the person and background can affect subsequent garment placement and compositing.
* **Solution used:** Kept the existing pretrained MediaPipe Selfie Segmentation model and its 0.4 foreground threshold after comparing its landscape variant and thresholds from 0.1 to 0.4; those alternatives did not resolve the visible failures. Validated probability-map dimensions, finite values, and range. The function now reports the method and warning when an OpenCV fallback is used, plus the foreground fraction.
* **Verification:** Saved and inspected original/mask/cutout outputs for all 10 supplied photos. A later visual review found that the filenames `pose_test_1_no_person.jpg` and `pose_test_2_no_person.jpg` actually contain people; the earlier 0% and 0.33% foreground figures therefore do not verify no-person behavior. The two visually verified empty-scene inputs instead produce 11.35% and 12.40% foreground in the corrected run. Raised hands are missed and foliage overlaps the person in the plant-occlusion case; these remain model limitations. Four segmentation tests pass; API and frontend build checks pass.

### Entry 5: Person Segmentation — Mask Integration

* **Date:** 2026-10-13
* **Problem:** Even when a segmentation module produces a mask, downstream processing must interpret that mask correctly. Incorrect dimensions, colour-channel handling, thresholding, or foreground/background conventions can lead to inverted masks, incomplete person extraction, or incorrect compositing.
* **Solution used:** The output contract is now an input-sized RGBA PNG plus an input-sized grayscale PNG derived from the final alpha mask. Both are exposed by the local API; the result page has a mask-inspection tab. Model/fallback method, fallback warning, and foreground fraction are also exposed.
* **Verification:** Automated tests assert RGBA/mask dimensions and foreground alpha behavior. All 10 outputs matched their original image dimensions. The earlier no-person checks were based on misleading filenames and are superseded by the corrected visually verified measurements in Phase 3.1. The local analyze/generate API returned the mask and method fields with HTTP 200.

### Entry 6: Garment Extraction — Background Removal Limitations

* **Date:** 2026-10-13
* **Problem:** Garment extraction uses traditional image-processing techniques, including corner-background colour estimation, thresholding, morphological operations, and contour selection. This approach may fail when the garment and background have similar colours, when the background is textured, or when shadows and reflections create misleading regions.
* **Solution used:** *Pending implementation.* Build a test set covering different garment colours, backgrounds, lighting conditions, and garment shapes. Evaluate the current method against manually reviewed reference masks. Based on the results, tune the thresholding and morphological operations or replace the extraction method with a more robust foreground-segmentation approach if the current method cannot meet the required quality.
* **Verification:** Pending. No garment-specific test photos are present in the workspace. Compare extracted garment masks with reference masks once a permitted test set is supplied; record background leakage, garment pixels removed incorrectly, and edge-quality issues before changing the algorithm.

### Entry 7: Garment Extraction — Largest-Contour Assumption

* **Date:** 2026-10-13
* **Problem:** The extraction pipeline selects the largest contour to identify the garment. This assumes that the largest detected foreground region corresponds to the complete garment. The assumption may fail when background regions are incorrectly classified as foreground, the garment is split into separate regions, or multiple objects appear in the image.
* **Solution used:** *Pending implementation.* Validate the largest-contour assumption against representative inputs. If it proves unreliable, evaluate contour area, connectivity, location, shape, and mask quality together. Where appropriate, retain multiple garment components instead of automatically discarding every region except the largest.
* **Verification:** Pending. Test garments with thin straps, sleeves, gaps, complex silhouettes, and disconnected components. Verify that the complete garment is retained and unrelated background regions are excluded.

### Entry 8: Garment Extraction — Edge Quality and Mask Refinement

* **Date:** 2026-10-13
* **Problem:** Morphological operations and mask-edge blurring can remove narrow garment features or produce soft, inaccurate boundaries. These issues may become noticeable around sleeves, collars, straps, and other fine details when the garment is placed over a person.
* **Solution used:** *Pending implementation.* Inspect intermediate masks before and after morphological operations. Tune kernel sizes and thresholds using representative garments, and distinguish mask cleanup from edge smoothing. Preserve important garment details while removing isolated noise.
* **Verification:** Pending. Compare intermediate and final masks for fine garment features. Inspect extracted garments against contrasting backgrounds and record missing details, jagged edges, and unwanted transparency.

### Entry 9: Integration — Handling Failed Detection or Extraction

* **Date:** 2026-10-13
* **Problem:** Pose detection and garment extraction feed later processing stages. If either component returns invalid or unreliable output, downstream code may still attempt to generate a result using incomplete landmarks or an unusable garment mask.
* **Solution used:** *Pending implementation.* Introduce explicit validation at each processing boundary. Check that required landmarks exist, the person image is usable, and garment extraction produces a valid foreground mask. Return meaningful errors when essential inputs are unavailable instead of silently continuing with invalid data.
* **Verification:** Pending. Test missing landmarks, images without a person, blank images, invalid masks, and garment images that cannot be separated reliably from their backgrounds. Confirm that failures are reported clearly and do not produce misleading success responses.

## Next Steps

1. **MediaPipe Pose and metrics:** Completed; see Entries 1–3 and the focused local tests.
2. **Person Segmentation:** Completed and visually checked; raised hands and overlapping foliage remain known model limitations.
3. **Garment Extraction:** Completed and visually checked on 10 permitted samples; attached objects and similar-background edges remain known limitations.
4. **Evaluation Pipeline:** Completed; rerun from `backend` with `..\.venv\Scripts\python.exe -m tests.evaluate`. Add manually verified reference masks before comparing segmentation/extraction accuracy.
5. **Phase 3.1:** Baseline consolidated in `PHASE3_BASELINE.md`.
6. **Next:** Obtain independent ground-truth masks and, if pose accuracy comparisons are required, keypoint annotations before model selection or integration.

## Logging Convention

For each entry, update the **Solution used** field only after implementing a fix. Update **Verification** only after running the relevant tests and recording the results. Keep unresolved problems marked as pending rather than treating proposed solutions as completed work.


### Phase 2: Local Setup

### Entry 1: Backend startup blocked by a mismatched Python environment

* **Date:** 2026-10-13
* **Problem:** The project virtual environment contained a `pydantic_core` native extension built for CPython 3.14, while the backend was running under Python 3.11. Package installation reported requirements as satisfied, but starting FastAPI failed with `ImportError: cannot import name 'ArgsKwargs'`.
* **Solution used:** Recreated the project-root `.venv` with Python 3.11, then installed `backend/requirements.txt` into that environment.
* **Verification:** `pip check` reported no broken requirements; FastAPI started and `GET /` returned HTTP 200. The frontend built successfully and its dev server returned HTTP 200.

### Entry 2: MediaPipe API mismatch silently disabled pose and segmentation

* **Date:** 2026-10-13
* **Problem:** The open-ended `mediapipe>=0.10.0` requirement installed MediaPipe 1.1.0, which does not expose the legacy `mp.solutions` API used by both pose detection and segmentation. The app silently used heuristic fallbacks instead.
* **Solution used:** Constrained MediaPipe to `>=0.10.21,<0.10.22` in `backend/requirements.txt`, the release range compatible with the project's `mp.solutions` calls.
* **Verification:** Confirmed MediaPipe 0.10.21 exposes `mp.solutions`; the sample upload/generate flow completed with HTTP 200 and actual MediaPipe inference logs, without the fallback warnings.

### Phase 2: Repeatable Evaluation Pipeline

* **Date:** 2026-10-13
* **Problem:** The pose detector, person segmentor, and garment extractor had no single repeatable command to evaluate all supplied samples, report per-image outcomes/timings, and save predicted masks. Segmentation and garment-extraction accuracy could not be quantified without independent reference masks.
* **Solution used:** Added `tests.evaluate`, which calls the existing component functions, validates required pose landmarks and mask dimensions, captures per-image errors and processing times, saves predicted masks/cutouts, and writes a CSV report. Pose photos are reused for segmentation; the existing photo folders remain in place. Added optional IoU/Dice against same-basename reference masks, with both-empty masks defined as a perfect match. Added a shared full-frame garment-mask function used by both the local extractor and evaluator.
* **Verification:** An initial run processed all 30 component/image pairs, but its pose labels were inferred from filenames. Visual review later found multiple mislabeled images, invalidating its reported 7/8 positive pose passes and 2/2 no-person rejections. The corrected run and results are recorded in Phase 3.1. Segmentation and garment masks were output-valid on 10/10 each; no independent reference masks exist, so IoU/Dice remain blank. Predictions remain under ignored run-specific result folders.
* **Remaining manual work:** Create and verify independent reference masks for segmentation and garment examples, then rerun the evaluator. Do not use the generated prediction masks as references; doing so would make the accuracy scores circular.

### Phase 3.1: Component Baseline and Label Correction

* **Date:** 2026-10-13
* **Solution used:** Added `tests/pose-detection/pose_labels.csv` with visually verified categories and person-presence labels. The evaluator requires exact manifest coverage, records the label version and raw required-landmark coordinates/visibility/in-frame status, flags detection/label mismatches, and skips pose-quality comparisons across different label versions. Updated `PHASE3_BASELINE.md`, this log, and the README.
* **Verification:** Diagnostic run `20261013T185711.532501+0530` processed 10 images per component. With corrected labels, MediaPipe detected 6/8 people; 5/8 passed required-landmark validation. It falsely detected a pose in both empty scenes, and missed both front-facing people; no fallback landmarks were used. Sweeps over detection confidence 0.3/0.5/0.7 and model complexity 0/1/2 did not change outcomes. The second partially occluded person's hips had visibility 0.18/0.23 and were out of frame. The empty-scene segmentation masks contain coherent human-like foreground at 11.35% and 12.40%; no fallback warnings occurred. All 10 segmentation and 10 garment outputs were format-valid. No reference masks/keypoint annotations exist, so accuracy scores remain unavailable. All 20 evaluator, pose, segmentation, and garment `unittest` checks pass.
* **Remaining manual work:** The internal cause of the pose model's missed detections and false positives remains undetermined; the checked preprocessing, threshold, model complexity, and fallback path do not explain them. Annotate independent person/garment masks before quantitative mask comparison and keypoints before PCK/OKS. Then test preprocessing or candidate models against those references; warm models and record loading separately for latency comparisons.

### Phase 3.2: Failure Analysis and Annotation-Ready Metrics

* **Date:** 2026-10-13
* **Problem:** The corrected baseline identifies pose mismatches and false foreground on empty scenes, but initially had no per-image confidence evidence or mask metrics beyond IoU/Dice. The specified pose and garment image files are already present, but the positive-person/garment reference masks and keypoint annotations are not yet available.
* **Solution used:** Added required-landmark coordinates, visibility, in-frame state, model source, and detection/label agreement to evaluation rows. Ran controlled diagnostic sweeps without changing production thresholds: detection confidence 0.3/0.5/0.7 and model complexity 0/1/2. Inspected both empty-scene segmentation masks. Extended mask evaluation with precision, recall, false-positive count/fraction, strict binary-reference validation, and separate empty-scene false-foreground reporting.
* **Verification:** Evaluation run `20261013T185711.532501+0530` shows both empty-scene pose false positives came directly from MediaPipe, with required-landmark visibilities near 1.0 and no fallback. Both genuine front-facing people were missed; their detector outputs contained no landmarks. The second partially occluded person's hips had visibility 0.18/0.23 and were out of frame. Neither diagnostic sweep changed the detected/not-detected outcomes. Both empty-scene segmentation masks contain human-shaped regions, at 11.35% and 12.40% foreground, with no fallback warning. All 11 evaluator tests, 4 pose tests, 6 segmentation tests, and 2 garment tests pass.
* **Remaining manual work:** Independently annotate the 8 positive-person masks, 10 garment masks, and five keypoints for each of the 8 person images. Inspect mask boundaries and ensure image dimensions and binary values match. Until then, positive-scene mask accuracy and keypoint accuracy are unavailable; candidate-model comparisons remain blocked to avoid selecting on unverified visual impressions.

### Phase 3.3: Local Annotation Workflow and Metric Verification

* **Date:** 2026-10-13
* **Problem:** Reference labels must be independent of model predictions, and user images should remain local during annotation. The evaluator also needed an explicit keypoint metric and verified references for the empty-scene segmentation cases.
* **Solution used:** Added `tools/annotate_references.py`, an OpenCV-based local workflow for polygon masks and keypoints. The two visually verified empty-scene person references are generated as all-black masks; positive-person and garment masks and keypoints are left for human annotation. Added keypoint CSV validation and PCK@0.2, normalized by the diagonal of the visible reference-keypoint bounding box, and documented the convention.
* **Verification:** Annotation/evaluator tests passed (16 tests), as did pose (4), segmentation (6), and garment (2) tests; Python syntax checks and `git diff --check` passed. Evaluation run `20261013T193531.720201+0530` validated both empty-scene masks and reported mean IoU/Dice/precision 0.0, recall 1.0 under the empty-reference convention, and mean false foreground 11.87%. Pose outcomes remain 5/8 positive fit-landmark passes and 0/2 no-person rejections. No positive masks, garment masks, or keypoint annotations were evaluated.
* **Remaining manual work:** Run the local annotator and create/review the 8 positive-person masks, 10 garment masks, and keypoints for the 8 people. Then rerun the evaluator and inspect the per-image CSV before any candidate-model comparison.

### UI: Luxe Intelligence Redesign

* **Date:** 2026-10-13
* **Problem:** The existing frontend used a dark, glass-heavy theme across all routes and treated the upload screen as the landing page. Several details also made the interface less trustworthy: the result screen claimed a look was saved without persisting it, and history inspection did not navigate to the result view.
* **Solution used:** Applied the warm ivory, plum, burgundy, and restrained-gold visual system with editorial typography and responsive layouts. Added a separate landing page while keeping `/upload` as the try-on studio. Refreshed the upload flow with three steps, drag/drop, image previews, replace/remove controls, input validation, and object-URL cleanup while preserving the existing try-on API call. Refreshed result, history, login, and registration views without changing API/auth semantics; removed the simulated save action and stopped presenting missing saved-history inspection images as real pose/cutout outputs. Added mobile navigation, reduced-motion support, visible errors, and truthful loading states.
* **Verification:** `npm run build` passed. `npm run lint` passed with one existing warning in `src/context/AuthContext.jsx` (`react/only-export-components`). Browser smoke checks loaded `/`, `/upload`, `/result`, `/history`, `/login`, and `/register`. Responsive checks at 390px, 800px, and 1189px showed no horizontal overflow on the landing page; `/upload`, `/result`, `/history`, `/login`, and `/register` also showed no horizontal overflow at 390px and 800px. The mobile menu works through tablet widths and is hidden at desktop width. Try-on generation and backend processing were not changed by this visual redesign.

### UI: Persistent Dark Theme Toggle

* **Date:** 2026-10-13
* **Problem:** The redesigned interface only had a light palette, with no user control to switch themes.
* **Solution used:** Added a sun/moon button to desktop and mobile navigation. The selected theme is stored in local storage and applied through a root `dark` class; CSS overrides the shared surfaces, text, borders, fields, and controls without changing page behavior.
* **Verification:** Production build passed. Lint passed with the same existing `AuthContext.jsx` fast-refresh warning. Browser-checked switching themes on the landing page and studio; dark styling and accessible toggle state were present.