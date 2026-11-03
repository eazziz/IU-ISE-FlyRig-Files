"""Shared helpers for the FlyRig camera scripts. Uses only the standard library."""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
EXPERIMENTS_DIR = REPO_ROOT / "experiments"
RUN_ID_RE = re.compile(r"^\d{4}-\d{2}-\d{2}_\d{3}$")
APP_NAME_RE = re.compile(r"^(?P<base>.*?)_?(?P<stamp>\d{4}_\d{2}_\d{2}T\d{2}_\d{2}_\d{2}_\d{3}Z)$")
VIDEO_SUFFIXES = {".mp4", ".mov", ".webm", ".avi", ".mkv", ".m4v"}
GAP_FACTOR = 1.5

LIGHT_COLUMNS = [
    "time_ms", "led1", "led2", "led3", "led4", "amplitude",
    "frequency", "pulse_width", "odor_l", "odor_r",
]


def die(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def require_ffprobe() -> None:
    if shutil.which("ffprobe") is None:
        die("ffprobe was not found. On a Mac, install it with: brew install ffmpeg")


def _ffprobe_json(args: list[str]) -> dict:
    command = ["ffprobe", "-v", "error", *args, "-of", "json"]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        die(f"ffprobe could not read the video: {result.stderr.strip()}")
    return json.loads(result.stdout)


def _fraction(value: str | None) -> float | None:
    if not value or value in {"0/0", "N/A"}:
        return None
    if "/" in value:
        top, bottom = value.split("/", 1)
        return float(top) / float(bottom) if float(bottom) else None
    return float(value)


def probe_video(path: Path) -> dict:
    data = _ffprobe_json([
        "-select_streams", "v:0",
        "-show_entries",
        "stream=codec_name,width,height,avg_frame_rate,r_frame_rate:format=format_name,duration,size",
        str(path),
    ])
    if not data.get("streams"):
        die(f"No video stream found in {path}")
    stream = data["streams"][0]
    container = data.get("format", {})
    duration = container.get("duration")
    return {
        "codec": stream.get("codec_name"),
        "width": stream.get("width"),
        "height": stream.get("height"),
        "container": container.get("format_name"),
        "container_duration_seconds": float(duration) if duration not in (None, "N/A") else None,
        "container_average_fps": _fraction(stream.get("avg_frame_rate")),
        "size_bytes": path.stat().st_size,
    }


def read_frame_times_ms(path: Path) -> list[float]:
    """Return each frame's presentation time in milliseconds, in display order."""
    data = _ffprobe_json([
        "-select_streams", "v:0",
        "-show_entries", "frame=best_effort_timestamp_time,pts_time",
        str(path),
    ])
    times = []
    for frame in data.get("frames", []):
        value = frame.get("best_effort_timestamp_time") or frame.get("pts_time")
        if value not in (None, "N/A"):
            times.append(float(value) * 1000.0)
    if not times:
        die(f"No frame timestamps could be read from {path}")
    return times


def analyze_timing(times_ms: list[float]) -> dict:
    deltas = [later - earlier for earlier, later in zip(times_ms, times_ms[1:])]
    summary = {
        "frame_count": len(times_ms),
        "first_frame_ms": round(times_ms[0], 3),
        "last_frame_ms": round(times_ms[-1], 3),
        "duration_seconds": round((times_ms[-1] - times_ms[0]) / 1000.0, 3),
        "average_fps": None,
        "median_frame_interval_ms": None,
        "min_frame_interval_ms": None,
        "max_frame_interval_ms": None,
        "gap_threshold_ms": None,
        "out_of_order_frames": sum(1 for delta in deltas if delta <= 0),
        "gap_count": 0,
        "estimated_missing_frames": 0,
        "gaps": [],
    }
    if not deltas:
        return summary

    median = statistics.median(deltas)
    threshold = median * GAP_FACTOR
    span = times_ms[-1] - times_ms[0]
    gaps = []
    missing_total = 0
    for index, delta in enumerate(deltas):
        if median > 0 and delta > threshold:
            missing = max(round(delta / median) - 1, 1)
            missing_total += missing
            gaps.append({
                "after_frame": index,
                "before_frame": index + 1,
                "at_ms": round(times_ms[index], 3),
                "gap_ms": round(delta, 3),
                "estimated_missing_frames": missing,
            })
    summary.update({
        "average_fps": round((len(times_ms) - 1) * 1000.0 / span, 3) if span > 0 else None,
        "median_frame_interval_ms": round(median, 3),
        "min_frame_interval_ms": round(min(deltas), 3),
        "max_frame_interval_ms": round(max(deltas), 3),
        "gap_threshold_ms": round(threshold, 3),
        "gap_count": len(gaps),
        "estimated_missing_frames": missing_total,
        "gaps": gaps,
    })
    return summary


def write_frame_timestamps(path: Path, times_ms: list[float]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["frame_number", "time_ms", "delta_ms"])
        previous = None
        for number, time_ms in enumerate(times_ms):
            delta = "" if previous is None else f"{time_ms - previous:.3f}"
            writer.writerow([number, f"{time_ms:.3f}", delta])
            previous = time_ms


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_app_csv(path: Path) -> tuple[str | None, list[dict], dict]:
    """Read the CSV FlyRig saves: base filename, cue table, 'end', then metadata."""
    base_name = None
    cues: list[dict] = []
    metadata: dict[str, str] = {}
    mode = "header"
    with path.open(newline="", encoding="utf-8-sig") as handle:
        for row in csv.reader(handle):
            if not row or not any(cell.strip() for cell in row):
                continue
            first = row[0].strip()
            if mode == "header":
                if first == "Base filename":
                    base_name = row[1].strip() if len(row) > 1 else None
                elif first.startswith("Time (sec)"):
                    mode = "cues"
            elif mode == "cues":
                if first == "end":
                    mode = "between"
                    continue
                cells = [cell.strip() for cell in row] + [""] * 10
                try:
                    time_ms = float(cells[0]) * 1000.0
                except ValueError:
                    die(f"Could not read this cue row in {path.name}: {row}")
                cues.append({
                    "time_ms": f"{time_ms:g}",
                    "led1": cells[1], "led2": cells[2], "led3": cells[3], "led4": cells[4],
                    "amplitude": cells[5], "frequency": cells[6], "pulse_width": cells[7],
                    "odor_l": cells[8], "odor_r": cells[9],
                })
            elif mode == "between":
                if first == "Metadata":
                    mode = "metadata"
            elif mode == "metadata":
                metadata[first] = row[1].strip() if len(row) > 1 else ""
    return base_name, cues, metadata


def write_light_commands(path: Path, cues: list[dict]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=LIGHT_COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(cues)


def split_app_name(stem: str) -> tuple[str, dt.datetime | None]:
    match = APP_NAME_RE.match(stem)
    if not match:
        return stem, None
    stamp = dt.datetime.strptime(match.group("stamp"), "%Y_%m_%dT%H_%M_%S_%fZ")
    return match.group("base"), stamp


def find_app_csv(video: Path) -> Path | None:
    """Find the CSV saved with a video.

    The app stamps the video and CSV names separately, so their times can differ
    by a few milliseconds. Accept the nearest CSV with the same base name.
    """
    exact = video.with_suffix(".csv")
    if exact.exists():
        return exact
    base, stamp = split_app_name(video.stem)
    if stamp is None:
        return None
    best = None
    best_gap = 5.0
    for candidate in video.parent.glob("*.csv"):
        other_base, other_stamp = split_app_name(candidate.stem)
        if other_stamp is None or other_base != base:
            continue
        gap = abs((other_stamp - stamp).total_seconds())
        if gap <= best_gap:
            best, best_gap = candidate, gap
    return best


def next_run_id(date: str) -> str:
    highest = 0
    if EXPERIMENTS_DIR.exists():
        for folder in EXPERIMENTS_DIR.glob(f"{date}_*"):
            suffix = folder.name.rsplit("_", 1)[-1]
            if folder.is_dir() and suffix.isdigit():
                highest = max(highest, int(suffix))
    return f"{date}_{highest + 1:03d}"


def git_output(*args: str) -> str | None:
    if shutil.which("git") is None:
        return None
    result = subprocess.run(["git", "-C", str(REPO_ROOT), *args], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None
