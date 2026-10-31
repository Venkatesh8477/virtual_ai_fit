import base64
import csv
import json
import math
import sys
import time
from datetime import datetime
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEST_ROOT = PROJECT_ROOT / "tests"
BACKEND_ROOT = PROJECT_ROOT / "backend"
RESULTS_ROOT = TEST_ROOT / "results"
RUN_ID = datetime.now().astimezone().strftime("%Y%m%dT%H%M%S.%f%z")
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}
REQUIRED_LANDMARKS = (0, 11, 12, 23, 24)

POSE_IMAGES = TEST_ROOT / "pose-detection" / "pose_detection_10_test_photos"
SEGMENTATION_IMAGES = POSE_IMAGES
GARMENT_IMAGES = TEST_ROOT / "garment-extraction" / "inputs"
POSE_LABELS_FILE = TEST_ROOT / "pose-detection" / "pose_labels.csv"
KEYPOINTS_FILE = TEST_ROOT / "pose-detection" / "keypoint_annotations.csv"
SEGMENTATION_REFERENCES = TEST_ROOT / "segmentation" / "reference_masks"
GARMENT_REFERENCES = TEST_ROOT / "garment-extraction" / "reference_masks"
KEYPOINT_IDS = {
    "nose": 0,
    "left_shoulder": 11,
    "right_shoulder": 12,
    "left_hip": 23,
    "right_hip": 24,
}
PCK_THRESHOLD = 0.2

sys.path.insert(0, str(BACKEND_ROOT))

from mediapipe_engine.pose_detector import analyze_body_pose, landmark_is_usable
from mediapipe_engine.segmentor import segment_person_background
from routes.tryon import extract_garment_mask


def discover_images(directory: Path) -> list[Path]:
    if not directory.is_dir():
        return []
    return sorted(
        path for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    )


def load_pose_labels(path: Path = POSE_LABELS_FILE) -> dict[str, dict]:
    labels = {}
    with path.open(newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            image = row["image"]
            has_person = row["has_person"].strip().lower()
            if has_person not in {"true", "false"}:
                raise ValueError(f"Invalid has_person value for {image}: {has_person!r}.")
            if image in labels:
                raise ValueError(f"Duplicate pose label for {image}.")
            labels[image] = {
                "category": row["category"].strip(),
                "has_person": has_person == "true",
                "label_version": row["label_version"].strip(),
            }
    return labels


def validate_pose_labels(image_paths: list[Path], labels: dict[str, dict]) -> None:
    image_names = {path.name for path in image_paths}
    label_names = set(labels)
    missing = sorted(image_names - label_names)
    extra = sorted(label_names - image_names)
    if missing or extra:
        raise ValueError(
            f"Pose label manifest mismatch; missing={missing}, unknown={extra}."
        )


def load_keypoint_annotations(
    image_paths: list[Path],
    pose_labels: dict[str, dict],
    path: Path = KEYPOINTS_FILE,
) -> dict[str, dict[str, tuple[float, float] | None]]:
    annotations: dict[str, dict[str, tuple[float, float] | None]] = {}
    with path.open(newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)
        required_columns = {
            "image", "person_present", "keypoint", "x", "y", "status",
            "image_width", "image_height",
        }
        if not required_columns.issubset(reader.fieldnames or set()):
            raise ValueError(f"Keypoint CSV must contain columns {sorted(required_columns)}.")
        for row in reader:
            image_name = row["image"]
            if image_name not in pose_labels:
                raise ValueError(f"Unknown image in keypoint annotations: {image_name}.")
            has_person = row["person_present"].strip().lower() == "true"
            if has_person != pose_labels[image_name]["has_person"]:
                raise ValueError(f"Person label mismatch in keypoint annotations: {image_name}.")
            image_path = next(
                (candidate for candidate in image_paths if candidate.name == image_name),
                None,
            )
            if image_path is None:
                raise ValueError(f"Missing source image for keypoint annotations: {image_name}.")
            source = cv2.imdecode(
                np.frombuffer(image_path.read_bytes(), np.uint8), cv2.IMREAD_COLOR
            )
            if source is None:
                raise ValueError(f"Could not decode keypoint source image: {image_name}.")
            height, width = source.shape[:2]
            if (
                row["image_width"] != str(width)
                or row["image_height"] != str(height)
            ):
                raise ValueError(f"Keypoint image dimensions mismatch: {image_name}.")

            keypoint = row["keypoint"].strip()
            status = row["status"].strip().lower()
            image_annotations = annotations.setdefault(image_name, {})
            if not has_person:
                if keypoint or status != "no_person" or row["x"] or row["y"]:
                    raise ValueError(f"Invalid no-person keypoint row: {image_name}.")
                if image_annotations:
                    raise ValueError(f"Duplicate no-person keypoint row: {image_name}.")
                image_annotations[""] = None
                continue
            if keypoint not in KEYPOINT_IDS:
                raise ValueError(f"Unknown keypoint {keypoint!r} for {image_name}.")
            if keypoint in image_annotations:
                raise ValueError(f"Duplicate {keypoint} annotation for {image_name}.")
            if status == "unavailable":
                if row["x"] or row["y"]:
                    raise ValueError(f"Unavailable keypoint must not have coordinates: {image_name}.")
                image_annotations[keypoint] = None
                continue
            if status != "visible":
                raise ValueError(f"Invalid keypoint status for {image_name}/{keypoint}.")
            try:
                x, y = float(row["x"]), float(row["y"])
            except ValueError as err:
                raise ValueError(
                    f"Invalid coordinates for {image_name}/{keypoint}."
                ) from err
            if not math.isfinite(x) or not math.isfinite(y) or not (0 <= x < width and 0 <= y < height):
                raise ValueError(f"Out-of-bounds keypoint for {image_name}/{keypoint}.")
            image_annotations[keypoint] = (x, y)

    for image_path in image_paths:
        image_annotations = annotations.get(image_path.name, {})
        if pose_labels[image_path.name]["has_person"]:
            missing = set(KEYPOINT_IDS) - image_annotations.keys()
            if missing:
                raise ValueError(
                    f"Missing keypoint annotations for {image_path.name}: {sorted(missing)}."
                )
            if not any(point is not None for point in image_annotations.values()):
                raise ValueError(f"No visible keypoints annotated for {image_path.name}.")
        elif set(image_annotations) != {""}:
            raise ValueError(f"Missing no-person keypoint label for {image_path.name}.")
    return annotations


def keypoint_accuracy(
    predictions: dict,
    references: dict[str, tuple[float, float] | None],
    width: int,
    height: int,
) -> dict[str, float | int]:
    visible_references = {
        name: point for name, point in references.items() if point is not None
    }
    if not visible_references:
        raise ValueError("No visible reference keypoints are available.")
    xs = [point[0] for point in visible_references.values()]
    ys = [point[1] for point in visible_references.values()]
    scale = math.hypot(max(xs) - min(xs), max(ys) - min(ys))
    if scale <= 0:
        raise ValueError("Reference keypoint bounding-box diagonal must be positive.")

    correct = 0
    missing = 0
    for name, (reference_x, reference_y) in visible_references.items():
        landmark = predictions.get(KEYPOINT_IDS[name])
        if not landmark_is_usable(landmark):
            missing += 1
            continue
        error = math.hypot(
            float(landmark["x"]) * width - reference_x,
            float(landmark["y"]) * height - reference_y,
        )
        correct += error / scale <= PCK_THRESHOLD
    return {
        "pck_0_2": correct / len(visible_references),
        "correct": correct,
        "visible": len(visible_references),
        "missing_predictions": missing,
    }


def mask_metrics(prediction: np.ndarray, reference: np.ndarray) -> dict[str, float | int]:
    if prediction.shape != reference.shape:
        raise ValueError(
            f"Mask dimensions differ: prediction {prediction.shape}, reference {reference.shape}."
        )
    if not np.isin(reference, (0, 255)).all():
        raise ValueError("Reference mask must contain only 0 and 255 values.")
    predicted_foreground = prediction >= 128
    reference_foreground = reference == 255
    true_positive = int(np.count_nonzero(predicted_foreground & reference_foreground))
    false_positive = int(np.count_nonzero(predicted_foreground & ~reference_foreground))
    false_negative = int(np.count_nonzero(~predicted_foreground & reference_foreground))
    predicted_count = true_positive + false_positive
    reference_count = true_positive + false_negative
    union = true_positive + false_positive + false_negative
    return {
        "iou": true_positive / union if union else 1.0,
        "dice": (
            2 * true_positive / (predicted_count + reference_count)
            if predicted_count + reference_count
            else 1.0
        ),
        "precision": (
            true_positive / predicted_count
            if predicted_count
            else float(reference_count == 0)
        ),
        "recall": (
            true_positive / reference_count if reference_count else 1.0
        ),
        "false_positive_pixels": false_positive,
        "false_positive_fraction": false_positive / reference.size,
    }


def mask_scores(prediction: np.ndarray, reference: np.ndarray) -> tuple[float, float]:
    metrics = mask_metrics(prediction, reference)
    return metrics["iou"], metrics["dice"]


def find_reference_mask(directory: Path, image_path: Path) -> Path | None:
    if not directory.is_dir():
        return None
    return next(
        (
            path for path in sorted(directory.rglob("*"))
            if path.is_file()
            and path.suffix.lower() in IMAGE_EXTENSIONS
            and path.stem == image_path.stem
        ),
        None
    )


def add_mask_metrics(
    row: dict,
    prediction: np.ndarray,
    image_path: Path,
    reference_dir: Path,
    expected_empty: bool = False,
) -> None:
    reference_path = find_reference_mask(reference_dir, image_path)
    row["reference_mask"] = str(reference_path.relative_to(TEST_ROOT)) if reference_path else ""
    row["iou"] = None
    row["dice"] = None
    row["precision"] = None
    row["recall"] = None
    row["false_positive_pixels"] = None
    row["false_positive_fraction"] = None
    row["reference_mask_error"] = ""
    if reference_path is None:
        return

    reference = cv2.imdecode(
        np.frombuffer(reference_path.read_bytes(), np.uint8), cv2.IMREAD_GRAYSCALE
    )
    if reference is None:
        row["reference_mask_error"] = "Could not decode reference mask."
        return
    if expected_empty and np.any(reference):
        row["reference_mask_error"] = (
            "Visually labeled no-person reference mask must be entirely black."
        )
        return
    try:
        row.update(mask_metrics(prediction, reference))
    except ValueError as err:
        row["reference_mask_error"] = str(err)


def row_for(component: str, image_path: Path) -> dict:
    return {
        "run_id": RUN_ID,
        "component": component,
        "image": str(image_path.relative_to(TEST_ROOT)),
        "processing_success": False,
        "processing_time_seconds": None,
        "failure_reason": "",
    }


def evaluate_pose(
    image_path: Path,
    labels: dict[str, dict],
    keypoint_references: dict[str, tuple[float, float] | None] | None = None,
) -> dict:
    row = row_for("pose_detection", image_path)
    label = labels[image_path.name]
    row["test_category"] = label["category"]
    row["pose_label_version"] = label["label_version"]
    row["expected_no_person"] = not label["has_person"]
    start = time.perf_counter()
    try:
        result = analyze_body_pose(image_path.read_bytes())
        row["processing_time_seconds"] = round(time.perf_counter() - start, 6)
        row["processing_success"] = True
        row["detection_status"] = result["detection_status"]
        row["pose_detected"] = result["detection_status"] == "detected"
        row["detection_matches_person_label"] = (
            row["pose_detected"] == label["has_person"]
        )
        row["pose_source"] = result.get("pose_source")
        row["fallback_used"] = result.get("pose_source") != "mediapipe"
        row["visibility_threshold"] = result.get("visibility_threshold")
        row["image_width"] = result.get("image_width")
        row["image_height"] = result.get("image_height")

        landmarks = result.get("landmarks_dict", {})
        landmark_checks = {
            str(landmark_id): {
                "exists": landmark_id in landmarks,
                "x": landmarks.get(landmark_id, {}).get("x"),
                "y": landmarks.get(landmark_id, {}).get("y"),
                "visibility": landmarks.get(landmark_id, {}).get("visibility"),
                "in_frame": landmarks.get(landmark_id, {}).get("in_frame", False),
                "usable": landmark_is_usable(landmarks.get(landmark_id)),
                "finite_coordinates": (
                    landmarks.get(landmark_id) is not None
                    and all(
                        isinstance(landmarks[landmark_id].get(axis), (int, float))
                        and math.isfinite(landmarks[landmark_id][axis])
                        for axis in ("x", "y")
                    )
                ),
            }
            for landmark_id in REQUIRED_LANDMARKS
        }
        invalid = [
            landmark_id for landmark_id, check in landmark_checks.items()
            if not check["usable"]
        ]
        row["required_landmarks_valid"] = not invalid
        row["required_landmarks"] = json.dumps(landmark_checks, sort_keys=True)
        row["valid_pose_detection"] = row["pose_detected"] and not invalid
        row["no_person_correctly_rejected"] = (
            row["expected_no_person"] and not row["pose_detected"]
        )
        row["detection_reason"] = result.get("detection_reason") or ""
        if keypoint_references is not None and not row["expected_no_person"]:
            point_metrics = keypoint_accuracy(
                landmarks,
                keypoint_references,
                int(result["image_width"]),
                int(result["image_height"]),
            )
            row["keypoint_pck_threshold"] = PCK_THRESHOLD
            row["keypoint_pck_0_2"] = point_metrics["pck_0_2"]
            row["keypoint_pck_correct"] = point_metrics["correct"]
            row["keypoint_visible"] = point_metrics["visible"]
            row["keypoint_missing_predictions"] = point_metrics["missing_predictions"]
        if row["expected_no_person"] and row["pose_detected"]:
            row["failure_reason"] = "Pose detected for a visually labeled no-person image."
        elif not row["expected_no_person"] and not row["valid_pose_detection"]:
            row["failure_reason"] = (
                "No pose detected."
                if not row["pose_detected"]
                else f"Required landmarks unusable: {', '.join(invalid)}."
            )
    except Exception as err:
        row["failure_reason"] = f"{type(err).__name__}: {err}"
    finally:
        if row["processing_time_seconds"] is None:
            row["processing_time_seconds"] = round(time.perf_counter() - start, 6)
    return row


def evaluate_segmentation(image_path: Path, labels: dict[str, dict]) -> dict:
    row = row_for("person_segmentation", image_path)
    row["expected_no_person"] = not labels[image_path.name]["has_person"]
    start = time.perf_counter()
    try:
        result = segment_person_background(image_path.read_bytes())
        row["processing_time_seconds"] = round(time.perf_counter() - start, 6)
        mask_url = result.get("mask_data_url", "")
        if not mask_url.startswith("data:image/png;base64,"):
            raise ValueError("Segmentor returned an invalid mask data URL.")
        mask_bytes = base64.b64decode(mask_url.split(",", 1)[1], validate=True)
        mask = cv2.imdecode(np.frombuffer(mask_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
        source = cv2.imdecode(
            np.frombuffer(image_path.read_bytes(), np.uint8), cv2.IMREAD_COLOR
        )
        if source is None or mask is None:
            raise ValueError("Could not decode source image or predicted mask.")

        height, width = source.shape[:2]
        row["mask_valid"] = (
            mask.dtype == np.uint8
            and mask.shape == (height, width)
            and np.isfinite(mask).all()
        )
        row["mask_width"] = int(mask.shape[1])
        row["mask_height"] = int(mask.shape[0])
        row["dimensions_match"] = mask.shape == (height, width)
        row["foreground_fraction"] = round(float(np.mean(mask >= 128)), 6)
        if row["expected_no_person"]:
            row["false_foreground_fraction"] = row["foreground_fraction"]
            row["false_foreground_pixels"] = int(np.count_nonzero(mask >= 128))
        row["segmentation_method"] = result.get("segmentation_method")
        row["segmentation_warning"] = result.get("segmentation_warning") or ""
        if not row["mask_valid"]:
            raise ValueError("Predicted mask has invalid values or dimensions.")

        run_root = RESULTS_ROOT / RUN_ID
        mask_dir = run_root / "segmentation" / "masks"
        cutout_dir = run_root / "segmentation" / "cutouts"
        mask_dir.mkdir(parents=True, exist_ok=True)
        cutout_dir.mkdir(parents=True, exist_ok=True)
        mask_output = mask_dir / f"{image_path.stem}.png"
        if not cv2.imwrite(str(mask_output), mask):
            raise OSError(f"Could not save predicted mask: {mask_output}")
        cutout = cv2.imdecode(
            np.frombuffer(base64.b64decode(
                result["segmented_data_url"].split(",", 1)[1], validate=True
            ), np.uint8),
            cv2.IMREAD_UNCHANGED
        )
        if cutout is None or cutout.shape != (height, width, 4):
            raise ValueError("Segmentor returned an invalid or misaligned RGBA cutout.")
        cutout_output = cutout_dir / f"{image_path.stem}.png"
        if not cv2.imwrite(str(cutout_output), cutout):
            raise OSError(f"Could not save segmented cutout: {cutout_output}")
        row["mask_output"] = str(mask_output.relative_to(TEST_ROOT))
        row["cutout_output"] = str(cutout_output.relative_to(TEST_ROOT))
        add_mask_metrics(
            row, mask, image_path, SEGMENTATION_REFERENCES,
            expected_empty=row["expected_no_person"],
        )
        row["processing_success"] = True
    except Exception as err:
        row["failure_reason"] = f"{type(err).__name__}: {err}"
    finally:
        if row["processing_time_seconds"] is None:
            row["processing_time_seconds"] = round(time.perf_counter() - start, 6)
    return row


def evaluate_garment(image_path: Path) -> dict:
    row = row_for("garment_extraction", image_path)
    start = time.perf_counter()
    try:
        image_bytes = image_path.read_bytes()
        mask = extract_garment_mask(image_bytes)
        row["processing_time_seconds"] = round(time.perf_counter() - start, 6)
        source = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if source is None:
            raise ValueError("Could not decode garment image.")
        height, width = source.shape[:2]
        row["mask_valid"] = (
            mask.dtype == np.uint8
            and mask.shape == (height, width)
            and np.isfinite(mask).all()
            and set(np.unique(mask)).issubset({0, 255})
        )
        row["mask_width"] = int(mask.shape[1])
        row["mask_height"] = int(mask.shape[0])
        row["dimensions_match"] = mask.shape == (height, width)
        row["mask_empty"] = not bool(np.any(mask))
        if not row["mask_valid"] or row["mask_empty"]:
            raise ValueError("Garment extraction produced an invalid or empty mask.")

        run_root = RESULTS_ROOT / RUN_ID
        mask_dir = run_root / "garments" / "masks"
        extracted_dir = run_root / "garments" / "extracted"
        mask_dir.mkdir(parents=True, exist_ok=True)
        extracted_dir.mkdir(parents=True, exist_ok=True)
        mask_output = mask_dir / f"{image_path.stem}.png"
        if not cv2.imwrite(str(mask_output), mask):
            raise OSError(f"Could not save predicted mask: {mask_output}")
        rgba = cv2.cvtColor(source, cv2.COLOR_BGR2RGBA)
        rgba[:, :, 3] = mask
        x, y, crop_width, crop_height = cv2.boundingRect(cv2.findNonZero(mask))
        extracted_output = extracted_dir / f"{image_path.stem}.png"
        Image.fromarray(rgba[y:y + crop_height, x:x + crop_width]).save(extracted_output)
        row["mask_output"] = str(mask_output.relative_to(TEST_ROOT))
        row["extracted_output"] = str(extracted_output.relative_to(TEST_ROOT))
        add_mask_metrics(row, mask, image_path, GARMENT_REFERENCES)
        row["foreground_fraction"] = round(float(np.mean(mask >= 128)), 6)
        row["processing_success"] = True
    except Exception as err:
        row["failure_reason"] = f"{type(err).__name__}: {err}"
    finally:
        if row["processing_time_seconds"] is None:
            row["processing_time_seconds"] = round(time.perf_counter() - start, 6)
    return row


def save_results(rows: list[dict]) -> Path | None:
    if not rows:
        print("No test images found; no evaluation CSV was written.")
        return None
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    results_file = RESULTS_ROOT / "evaluation_results.csv"
    previous_rows = []
    if results_file.exists():
        with results_file.open(newline="", encoding="utf-8") as file:
            previous_rows = list(csv.DictReader(file))
        for row in previous_rows:
            if not row.get("run_id"):
                row["run_id"] = "baseline-before-run-history"
    all_rows = previous_rows + rows
    fieldnames = sorted({key for row in all_rows for key in row})
    with results_file.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)
    return results_file


def print_summary(rows: list[dict]) -> None:
    for component in ("pose_detection", "person_segmentation", "garment_extraction"):
        component_rows = [row for row in rows if row["component"] == component]
        if not component_rows:
            print(f"{component}: no images")
            continue
        successful = sum(row["processing_success"] for row in component_rows)
        average_time = sum(
            row["processing_time_seconds"] for row in component_rows
        ) / len(component_rows)
        print(
            f"{component}: {successful}/{len(component_rows)} processed, "
            f"mean {average_time:.4f}s"
        )
        if component == "pose_detection":
            positive = [row for row in component_rows if not row["expected_no_person"]]
            valid = sum(row.get("valid_pose_detection", False) for row in positive)
            expected_empty = [row for row in component_rows if row["expected_no_person"]]
            rejected = sum(
                row.get("no_person_correctly_rejected", False) for row in expected_empty
            )
            print(f"  valid poses: {valid}/{len(positive)} positive examples")
            print(f"  no-person correctly rejected: {rejected}/{len(expected_empty)}")
            keypoint_rows = [
                row for row in positive if row.get("keypoint_pck_0_2") is not None
            ]
            if keypoint_rows:
                correct_points = sum(
                    row["keypoint_pck_correct"] for row in keypoint_rows
                )
                visible_points = sum(row["keypoint_visible"] for row in keypoint_rows)
                print(
                    f"  PCK@0.2: {correct_points}/{visible_points} visible keypoints "
                    f"({correct_points / visible_points:.2%}); "
                    "normalizer: reference keypoint bounding-box diagonal"
                )
        elif component == "person_segmentation":
            empty_rows = [
                row for row in component_rows
                if row.get("expected_no_person") and row["processing_success"]
            ]
            if empty_rows:
                false_foreground = sum(
                    row["foreground_fraction"] for row in empty_rows
                ) / len(empty_rows)
                print(
                    f"  mean false foreground on empty scenes: "
                    f"{false_foreground:.2%} ({len(empty_rows)} images)"
                )
            scored_rows = [
                row for row in component_rows if row.get("iou") is not None
            ]
            if scored_rows:
                for metric in ("iou", "dice", "precision", "recall"):
                    mean_metric = sum(row[metric] for row in scored_rows) / len(scored_rows)
                    print(f"  mean {metric}: {mean_metric:.4f} ({len(scored_rows)} references)")


def print_previous_run_comparison(rows: list[dict], results_file: Path) -> None:
    with results_file.open(newline="", encoding="utf-8") as file:
        history = list(csv.DictReader(file))
    prior_run_ids = list(dict.fromkeys(
        row["run_id"] for row in history
        if row.get("run_id") and row["run_id"] != RUN_ID
    ))
    if not prior_run_ids:
        print("No previous evaluation run is available for comparison yet.")
        return

    previous_run_id = prior_run_ids[-1]
    previous_rows = [row for row in history if row["run_id"] == previous_run_id]
    print(f"Comparison: current run vs {previous_run_id}")
    for component in ("pose_detection", "person_segmentation", "garment_extraction"):
        current = [row for row in rows if row["component"] == component]
        previous = [row for row in previous_rows if row["component"] == component]
        if not current or not previous:
            continue
        if {row["image"] for row in current} != {row["image"] for row in previous}:
            print(f"  {component}: skipped (image sets differ)")
            continue

        current_times = [float(row["processing_time_seconds"]) for row in current]
        previous_times = [float(row["processing_time_seconds"]) for row in previous]
        current_time = sum(current_times) / len(current_times)
        previous_time = sum(previous_times) / len(previous_times)
        if component == "pose_detection":
            current_label_versions = {row.get("pose_label_version") for row in current}
            previous_label_versions = {row.get("pose_label_version") for row in previous}
            if current_label_versions != previous_label_versions:
                print(f"  {component}: skipped (pose label manifest changed)")
                continue
            current_positive = [row for row in current if not row["expected_no_person"]]
            previous_positive = [row for row in previous if row["expected_no_person"] != "True"]
            current_valid = sum(row.get("valid_pose_detection", False) for row in current_positive)
            previous_valid = sum(row.get("valid_pose_detection") == "True" for row in previous_positive)
            current_empty = [row for row in current if row["expected_no_person"]]
            previous_empty = [row for row in previous if row["expected_no_person"] == "True"]
            current_rejected = sum(row.get("no_person_correctly_rejected", False) for row in current_empty)
            previous_rejected = sum(
                row.get("no_person_correctly_rejected") == "True" for row in previous_empty
            )
            quality = (
                f"valid poses {current_valid}/{len(current_positive)} "
                f"vs {previous_valid}/{len(previous_positive)}; "
                f"no-person rejected {current_rejected}/{len(current_empty)} "
                f"vs {previous_rejected}/{len(previous_empty)}"
            )
        else:
            current_valid = sum(row.get("mask_valid", False) for row in current)
            previous_valid = sum(row.get("mask_valid") == "True" for row in previous)
            current_iou = [float(row["iou"]) for row in current if row.get("iou") not in (None, "")]
            previous_iou = [float(row["iou"]) for row in previous if row.get("iou") not in (None, "")]
            iou_text = (
                f"; mean IoU {sum(current_iou) / len(current_iou):.3f} "
                f"vs {sum(previous_iou) / len(previous_iou):.3f}"
                if current_iou and previous_iou
                else "; IoU comparison unavailable (matching reference masks are missing)"
            )
            quality = (
                f"valid masks {current_valid}/{len(current)} "
                f"vs {previous_valid}/{len(previous)}{iou_text}"
            )
        print(
            f"  {component}: {quality}; mean time "
            f"{current_time:.4f}s vs {previous_time:.4f}s"
        )


def main() -> None:
    print(f"Evaluation run: {RUN_ID}")
    pose_images = discover_images(POSE_IMAGES)
    segmentation_images = discover_images(SEGMENTATION_IMAGES)
    garment_images = discover_images(GARMENT_IMAGES)
    pose_labels = load_pose_labels()
    validate_pose_labels(pose_images, pose_labels)
    keypoint_annotations = None
    if KEYPOINTS_FILE.exists():
        keypoint_annotations = load_keypoint_annotations(pose_images, pose_labels)
    else:
        print(f"Pose keypoint metrics unavailable; annotate with {KEYPOINTS_FILE.relative_to(PROJECT_ROOT)}.")

    print(
        f"Discovered: pose={len(pose_images)}, "
        f"segmentation={len(segmentation_images)}, garments={len(garment_images)}"
    )

    rows = (
        [
            evaluate_pose(
                path,
                pose_labels,
                keypoint_annotations.get(path.name) if keypoint_annotations else None,
            )
            for path in pose_images
        ]
        + [evaluate_segmentation(path, pose_labels) for path in segmentation_images]
        + [evaluate_garment(path) for path in garment_images]
    )
    print_summary(rows)
    results_file = save_results(rows)
    if results_file:
        print(f"Results saved: {results_file.relative_to(PROJECT_ROOT)}")
        print_previous_run_comparison(rows, results_file)
    failures = sum(not row["processing_success"] for row in rows)
    reference_errors = [
        row for row in rows if row.get("reference_mask_error")
    ]
    print(
        "Previous evaluation rows are retained in the CSV. Mask metrics are blank unless a "
        "same-named reference mask exists under "
        "tests/segmentation/reference_masks or tests/garment-extraction/reference_masks."
    )
    if reference_errors:
        print(
            f"{len(reference_errors)} invalid reference mask(s); inspect the CSV "
            "reference_mask_error column."
        )
    if failures:
        print(f"{failures} component execution failure(s); inspect the CSV failure_reason column.")
        raise SystemExit(1)
    if reference_errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
