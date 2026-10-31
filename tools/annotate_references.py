import argparse
import csv
from pathlib import Path

import cv2
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
POSE_IMAGES = ROOT / "tests" / "pose-detection" / "pose_detection_10_test_photos"
GARMENT_IMAGES = ROOT / "tests" / "garment-extraction" / "inputs"
POSE_LABELS = ROOT / "tests" / "pose-detection" / "pose_labels.csv"
PERSON_MASKS = ROOT / "tests" / "segmentation" / "reference_masks"
GARMENT_MASKS = ROOT / "tests" / "garment-extraction" / "reference_masks"
KEYPOINTS_FILE = ROOT / "tests" / "pose-detection" / "keypoint_annotations.csv"
KEYPOINTS = (
    ("nose", "Nose"),
    ("left_shoulder", "Subject's left shoulder"),
    ("right_shoulder", "Subject's right shoulder"),
    ("left_hip", "Subject's left hip"),
    ("right_hip", "Subject's right hip"),
)


def read_pose_labels() -> dict[str, bool]:
    with POSE_LABELS.open(newline="", encoding="utf-8") as file:
        labels = {}
        for row in csv.DictReader(file):
            value = row["has_person"].strip().lower()
            if value not in {"true", "false"}:
                raise ValueError(f"Invalid has_person label for {row['image']}: {value!r}.")
            if row["image"] in labels:
                raise ValueError(f"Duplicate pose label for {row['image']}.")
            labels[row["image"]] = value == "true"
    image_names = {path.name for path in POSE_IMAGES.glob("*.jpg")}
    if set(labels) != image_names:
        raise ValueError(
            f"Pose label manifest mismatch; missing={sorted(image_names - set(labels))}, "
            f"unknown={sorted(set(labels) - image_names)}."
        )
    return labels


def preview_mask(image: np.ndarray, polygons: list[tuple[list[tuple[int, int]], int]],
                 active: list[tuple[int, int]], fill: int) -> np.ndarray:
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    overlay = image.copy()
    for points, value in polygons:
        cv2.fillPoly(mask, [np.asarray(points, dtype=np.int32)], value)
    for points, value in polygons:
        color = (30, 210, 50) if value else (20, 30, 230)
        cv2.polylines(overlay, [np.asarray(points, dtype=np.int32)], True, color, 2)
    if len(active) > 1:
        cv2.polylines(
            overlay, [np.asarray(active, dtype=np.int32)], False, (0, 220, 255), 1
        )
    for point in active:
        cv2.circle(overlay, point, 3, (0, 220, 255), -1)
    overlay[mask > 0] = (
        overlay[mask > 0] * 0.45 + np.array([35, 220, 55]) * 0.55
    ).astype(np.uint8)
    fill_name = "WHITE" if fill else "BLACK"
    cv2.putText(
        overlay, f"Fill: {fill_name} | B toggle | Right-click close | S save | Q quit",
        (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255, 255, 255), 1,
    )
    return overlay


def save_empty_person_mask(image_path: Path) -> None:
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not decode image: {image_path}")
    output_path = PERSON_MASKS / f"{image_path.stem}.png"
    mask = np.zeros(image.shape[:2], dtype=np.uint8)
    if output_path.exists():
        existing = cv2.imread(str(output_path), cv2.IMREAD_GRAYSCALE)
        if existing is None or existing.shape != mask.shape or np.any(existing):
            raise ValueError(f"Existing no-person reference mask is invalid: {output_path}")
        return
    PERSON_MASKS.mkdir(parents=True, exist_ok=True)
    if not cv2.imwrite(str(output_path), mask):
        raise OSError(f"Could not save empty reference mask: {output_path}")
    print(f"Saved visually verified empty-scene reference: {output_path.relative_to(ROOT)}")


def annotate_mask(image_path: Path, output_dir: Path, allow_empty: bool) -> str:
    output_path = output_dir / f"{image_path.stem}.png"
    if output_path.exists():
        print(f"Already annotated, leaving unchanged: {output_path.relative_to(ROOT)}")
        return "saved"
    image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Could not decode image: {image_path}")

    polygons: list[tuple[list[tuple[int, int]], int]] = []
    active: list[tuple[int, int]] = []
    fill = 255
    window = f"Annotate mask — {image_path.name}"

    def on_mouse(event, x, y, flags, userdata):
        if event == cv2.EVENT_LBUTTONDOWN:
            active.append((x, y))
        elif event == cv2.EVENT_RBUTTONDOWN and len(active) >= 3:
            polygons.append((active.copy(), fill))
            active.clear()

    cv2.namedWindow(window, cv2.WINDOW_AUTOSIZE)
    cv2.setMouseCallback(window, on_mouse)
    print(
        f"\n{image_path.name}: left-click polygon vertices; right-click to close. "
        "B toggles white/black fill, U undoes, R clears, S saves, N skips, Q quits."
    )
    try:
        while True:
            cv2.imshow(window, preview_mask(image, polygons, active, fill))
            key = cv2.waitKey(30) & 0xFF
            if key == ord("b"):
                fill = 0 if fill == 255 else 255
            elif key == ord("u"):
                if active:
                    active.pop()
                elif polygons:
                    polygons.pop()
            elif key == ord("r"):
                active.clear()
                polygons.clear()
                fill = 255
            elif key == ord("s"):
                if active:
                    print("Close the current polygon with a right-click before saving.")
                    continue
                mask = np.zeros(image.shape[:2], dtype=np.uint8)
                for points, value in polygons:
                    cv2.fillPoly(mask, [np.asarray(points, dtype=np.int32)], value)
                if not allow_empty and not np.any(mask):
                    print("Garment masks cannot be empty; draw the garment boundary first.")
                    continue
                output_dir.mkdir(parents=True, exist_ok=True)
                if not cv2.imwrite(str(output_path), mask):
                    raise OSError(f"Could not save mask: {output_path}")
                print(f"Saved {output_path.relative_to(ROOT)}")
                return "saved"
            elif key == ord("n"):
                return "skipped"
            elif key == ord("q"):
                return "quit"
    finally:
        cv2.destroyWindow(window)


def save_keypoint_rows(rows: list[dict[str, str]]) -> None:
    existing: dict[tuple[str, str], dict[str, str]] = {}
    if KEYPOINTS_FILE.exists():
        with KEYPOINTS_FILE.open(newline="", encoding="utf-8") as file:
            existing = {
                (row["image"], row["keypoint"]): row
                for row in csv.DictReader(file)
            }
    for row in rows:
        existing[(row["image"], row["keypoint"])] = row
    KEYPOINTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with KEYPOINTS_FILE.open("w", newline="", encoding="utf-8") as file:
        fields = (
            "image", "person_present", "keypoint", "x", "y", "status",
            "image_width", "image_height",
        )
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(existing.values())


def annotate_keypoints(image_paths: list[Path], labels: dict[str, bool]) -> None:
    for image_path in image_paths:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Could not decode image: {image_path}")
        height, width = image.shape[:2]
        if not labels[image_path.name]:
            save_keypoint_rows([{
                "image": image_path.name,
                "person_present": "false",
                "keypoint": "",
                "x": "",
                "y": "",
                "status": "no_person",
                "image_width": str(width),
                "image_height": str(height),
            }])
            print(f"Recorded no-person keypoint label: {image_path.name}")
            continue

        existing_keys = _existing_keypoint_keys()
        if any((image_path.name, name) in existing_keys for name, _ in KEYPOINTS):
            print(f"Keypoints already exist; leaving unchanged: {image_path.name}")
            continue

        points: list[dict[str, str]] = []
        index = 0
        clicked_point: tuple[int, int] | None = None
        window = f"Annotate keypoints — {image_path.name}"

        def on_mouse(event, x, y, flags, userdata):
            nonlocal clicked_point
            if event == cv2.EVENT_LBUTTONDOWN:
                clicked_point = (x, y)

        cv2.namedWindow(window, cv2.WINDOW_AUTOSIZE)
        cv2.setMouseCallback(window, on_mouse)
        print(
            f"\n{image_path.name}: click the named landmark; press N if not "
            "reliably visible, U to redo the prior point, Q to quit."
        )
        try:
            while index < len(KEYPOINTS):
                display = image.copy()
                for row in points:
                    if row["status"] == "visible":
                        xy = (int(row["x"]), int(row["y"]))
                        cv2.circle(display, xy, 3, (0, 220, 255), -1)
                        cv2.putText(
                            display, row["keypoint"], (xy[0] + 4, xy[1] - 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.35, (0, 220, 255), 1,
                        )
                cv2.putText(
                    display, f"Click: {KEYPOINTS[index][1]} | N unavailable | U undo | Q quit",
                    (3, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.32, (255, 255, 255), 1,
                )
                cv2.imshow(window, display)
                key = cv2.waitKey(30) & 0xFF
                if clicked_point is not None:
                    name = KEYPOINTS[index][0]
                    points.append({
                        "image": image_path.name,
                        "person_present": "true",
                        "keypoint": name,
                        "x": str(clicked_point[0]),
                        "y": str(clicked_point[1]),
                        "status": "visible",
                        "image_width": str(width),
                        "image_height": str(height),
                    })
                    clicked_point = None
                    index += 1
                elif key == ord("n"):
                    name = KEYPOINTS[index][0]
                    points.append({
                        "image": image_path.name,
                        "person_present": "true",
                        "keypoint": name,
                        "x": "",
                        "y": "",
                        "status": "unavailable",
                        "image_width": str(width),
                        "image_height": str(height),
                    })
                    index += 1
                elif key == ord("u") and points:
                    points.pop()
                    index -= 1
                elif key == ord("q"):
                    return
                if index < len(KEYPOINTS):
                    print(f"Mark: {KEYPOINTS[index][1]}")
            save_keypoint_rows(points)
            print(f"Saved keypoints for {image_path.name}")
        finally:
            cv2.destroyWindow(window)


def _existing_keypoint_keys() -> set[tuple[str, str]]:
    if not KEYPOINTS_FILE.exists():
        return set()
    with KEYPOINTS_FILE.open(newline="", encoding="utf-8") as file:
        return {
            (row["image"], row["keypoint"])
            for row in csv.DictReader(file)
        }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Create local reference masks and pose keypoint annotations."
    )
    parser.add_argument(
        "task", nargs="?", choices=("person", "garment", "keypoints"),
        help="annotation type; omit to select interactively",
    )
    task = parser.parse_args().task
    if task is None:
        task = input("Annotate [person / garment / keypoints]? ").strip().lower()
        if task not in {"person", "garment", "keypoints"}:
            raise SystemExit("Choose person, garment, or keypoints.")

    if task == "person":
        labels = read_pose_labels()
        image_paths = sorted(POSE_IMAGES.glob("*.jpg"))
        for image_path in image_paths:
            if not labels[image_path.name]:
                save_empty_person_mask(image_path)
        for image_path in image_paths:
            if not labels[image_path.name]:
                continue
            result = annotate_mask(image_path, PERSON_MASKS, allow_empty=False)
            if result == "quit":
                break
    elif task == "garment":
        for image_path in sorted(GARMENT_IMAGES.glob("*")):
            if not image_path.is_file():
                continue
            if annotate_mask(image_path, GARMENT_MASKS, allow_empty=False) == "quit":
                break
    else:
        labels = read_pose_labels()
        annotate_keypoints(sorted(POSE_IMAGES.glob("*.jpg")), labels)


if __name__ == "__main__":
    main()
