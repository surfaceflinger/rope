import argparse
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from deepface import DeepFace

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".webp"}
MIN_FACE_SIZE = 150
ATTRIBUTES = ["gender", "race", "emotion"]


def get_image_info(path: str) -> tuple[datetime | None, tuple[int, int]]:
    import PIL.Image
    import PIL.ExifTags
    try:
        img = PIL.Image.open(path)
        size = img.size  # (width, height)
        exif = img._getexif() or {}
        tags = {PIL.ExifTags.TAGS.get(k, ""): v for k, v in exif.items()}
        raw = tags.get("DateTimeOriginal") or tags.get("DateTime")
        dt = datetime.strptime(raw, "%Y:%m:%d %H:%M:%S") if raw else None
        return dt, size
    except Exception:
        return None, (0, 0)


def period_key(dt: datetime, months: int) -> str:
    start = (dt.month - 1) // months * months + 1
    return f"{dt.year}-{start:02d}..{min(start + months - 1, 12):02d}"


def new_stats() -> dict:
    return {
        "ages": [],
        "counts": {a: defaultdict(int) for a in ATTRIBUTES},
        "scores": {a: defaultdict(list) for a in ATTRIBUTES},
    }


def record_face(stats: dict, face: dict) -> None:
    stats["ages"].append(float(face["age"]))
    for a in ATTRIBUTES:
        stats["counts"][a][face[f"dominant_{a}"]] += 1
        for k, v in face[a].items():
            stats["scores"][a][k].append(float(v))


def analyze_image(path: str, all_stats: dict, period_stats: dict[str, dict], months: int) -> None:
    print(f"\n{'=' * 60}")
    print(f"File: {path}")

    dt, (img_w, img_h) = get_image_info(path)
    if dt:
        print(f"Date: {dt.strftime('%Y-%m-%d %H:%M')}")

    print('=' * 60)
    try:
        try:
            results = DeepFace.analyze(img_path=path, actions=["age", "gender", "race", "emotion"])
        except ValueError:
            results = DeepFace.analyze(img_path=path, actions=["age", "gender", "race", "emotion"],
                                       enforce_detection=False)

        # drop faces that are much smaller than the largest (reflections, artifacts)
        # also drop faces touching image edges (likely reflections/crops)
        results.sort(key=lambda f: f["region"]["w"], reverse=True)
        max_w = results[0]["region"]["w"]
        threshold = max(MIN_FACE_SIZE, max_w * 0.5)

        def is_edge_face(f: dict) -> bool:
            if f["region"]["w"] == max_w:
                return False
            r = f["region"]
            margin = 5
            return r["x"] <= margin or r["y"] <= margin or \
                (img_w and r["x"] + r["w"] >= img_w - margin) or \
                (img_h and r["y"] + r["h"] >= img_h - margin)

        real_faces = [f for f in results if f["region"]["w"] >= threshold and not is_edge_face(f)]
        if not real_faces:
            real_faces = results[:1]
        skipped = len(results) - len(real_faces)

        for i, face in enumerate(real_faces):
            if len(real_faces) > 1:
                print(f"\n--- Face {i + 1} ---")
            print(f"  Age      : {face['age']}")
            print(f"  Gender   : {face['dominant_gender']} ({face['gender']})")
            print(f"  Race     : {face['dominant_race']} ({face['race']})")
            print(f"  Emotion  : {face['dominant_emotion']} ({face['emotion']})")
            r = face["region"]
            print(f"  Region   : x={r['x']}, y={r['y']}, w={r['w']}, h={r['h']}")

            record_face(all_stats, face)
            if dt:
                key = period_key(dt, months)
                if key not in period_stats:
                    period_stats[key] = new_stats()
                record_face(period_stats[key], face)

        if skipped:
            print(f"  (skipped {skipped} face(s) with region < {MIN_FACE_SIZE}px)")
    except Exception as e:
        print(f"  Error: {e}")


def print_summary(stats: dict, label: str = "SUMMARY") -> None:
    n = len(stats["ages"])
    if n == 0:
        return

    print(f"\n{'=' * 60}")
    print(f"{label} ({n} faces)")
    print('=' * 60)

    print(f"\n  Average age: {sum(stats['ages']) / n:.1f}")

    for a in ATTRIBUTES:
        print(f"\n  {a.title()} distribution:")
        for k, count in sorted(stats["counts"][a].items(), key=lambda x: -x[1]):
            print(f"    {k:20s}: {count:4d} ({100 * count / n:.1f}%)")
        print(f"\n  Average {a} confidence:")
        for k in sorted(stats["scores"][a]):
            avg = sum(stats["scores"][a][k]) / n
            print(f"    {k:20s}: {avg:.1f}%")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze faces in images using DeepFace")
    parser.add_argument("directory", help="Directory containing images")
    parser.add_argument("-m", "--months", type=int, default=4,
                        help="Number of months per period for trend analysis (default: 4)")
    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"Error: '{directory}' is not a directory")
        raise SystemExit(1)

    images = sorted(p for p in directory.rglob("*") if p.suffix.lower() in IMAGE_EXTENSIONS and p.is_file())

    if not images:
        print(f"No images found in '{directory}'")
        raise SystemExit(0)

    print(f"Found {len(images)} image(s) in '{directory}'")
    print(f"(filtering out detected faces smaller than {MIN_FACE_SIZE}px)")

    all_stats = new_stats()
    period_stats: dict[str, dict] = {}

    for img in images:
        analyze_image(str(img), all_stats, period_stats, args.months)

    print_summary(all_stats, "OVERALL SUMMARY")

    if period_stats:
        periods = sorted(period_stats)
        col = 14

        print(f"\n\n{'=' * 60}")
        print(f"TRENDS BY {args.months}-MONTH PERIODS")
        print('=' * 60)

        def row(label: str, values: list[str]) -> str:
            return f"  {label:20s}" + "".join(f"  {v:>{col}s}" for v in values)

        print(row("", periods))
        print(row("faces", [str(len(period_stats[p]["ages"])) for p in periods]))
        print(row("avg age", [
            f"{sum(period_stats[p]['ages']) / len(period_stats[p]['ages']):.1f}"
            for p in periods
        ]))

        print()
        all_genders = sorted({g for p in periods for g in period_stats[p]["counts"]["gender"]})
        for g in all_genders:
            print(row(g, [
                f"{100 * period_stats[p]['counts']['gender'].get(g, 0) / len(period_stats[p]['ages']):.0f}%"
                for p in periods
            ]))
            print(row(f"  avg {g.lower()}", [
                f"{sum(period_stats[p]['scores']['gender'].get(g, [])) / len(period_stats[p]['ages']):.1f}%"
                for p in periods
            ]))

        print()
        all_emotions = sorted({e for p in periods for e in period_stats[p]["scores"]["emotion"]})
        for e in all_emotions:
            print(row(e, [
                f"{sum(period_stats[p]['scores']['emotion'].get(e, [])) / len(period_stats[p]['ages']):.1f}%"
                for p in periods
            ]))

    print()


if __name__ == "__main__":
    main()
