#!/usr/bin/env python3
"""Check experiment folders and confirm that no videos will be committed.

Run it after `git add .` and before `git commit`.

    python3 scripts/check_run.py                  # every run
    python3 scripts/check_run.py 2026-11-03_001   # one run
"""
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

import flyrig_lib as lib

REQUIRED_FILES = ["settings.json", "video_info.json", "frame_timestamps.csv", "light_commands.csv", "notes.md"]
GITHUB_WARNING_BYTES = 50 * 1024 * 1024
FPS_TOLERANCE = 0.05


def check_run(run_dir: Path) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if not lib.RUN_ID_RE.match(run_dir.name):
        errors.append("folder name is not a valid experiment ID")
    missing = [name for name in REQUIRED_FILES if not (run_dir / name).is_file()]
    errors.extend(f"missing {name}" for name in missing)
    if missing:
        return errors, warnings

    info = json.loads((run_dir / "video_info.json").read_text())
    settings = json.loads((run_dir / "settings.json").read_text())

    with (run_dir / "frame_timestamps.csv").open(newline="") as handle:
        rows = list(csv.DictReader(handle))
    frame_count = info.get("timing", {}).get("frame_count")
    if len(rows) != frame_count:
        errors.append(f"frame_timestamps.csv has {len(rows)} rows, but video_info.json says {frame_count}")
    if [int(row["frame_number"]) for row in rows] != list(range(len(rows))):
        errors.append("frame numbers are not consecutive")

    gaps = info.get("timing", {}).get("gap_count", 0)
    if gaps:
        warnings.append(f"{gaps} timing gap(s), about {info['timing']['estimated_missing_frames']} missing frames")
    if info.get("timing", {}).get("out_of_order_frames"):
        warnings.append("some frame timestamps do not increase")

    requested = settings.get("camera", {}).get("requested_fps")
    measured = info.get("timing", {}).get("average_fps")
    if requested and measured and abs(measured - requested) / requested > FPS_TOLERANCE:
        warnings.append(f"measured {measured} fps, but {requested} fps was requested")

    video = run_dir / info.get("video_filename", "")
    if not video.is_file():
        warnings.append("video is not on this computer (expected on a teammate's clone)")
    elif lib.sha256_of(video) != info.get("sha256"):
        errors.append("video checksum does not match video_info.json")

    if not settings.get("operator"):
        warnings.append("settings.json has no operator")
    if not settings.get("camera", {}).get("source"):
        warnings.append("settings.json has no camera source")
    if not (run_dir / "app_output.csv").is_file():
        warnings.append("no app_output.csv, so the app's saved settings were not recorded")

    notes = (run_dir / "notes.md").read_text()
    if "Purpose:\n\n" in notes:
        warnings.append("notes.md still has an empty Purpose")
    return errors, warnings


def check_git() -> list[str]:
    tracked = lib.git_output("ls-files")
    if tracked is None:
        print("Git check skipped: this folder is not a Git repo yet.")
        return []
    errors = []
    for name in filter(None, tracked.splitlines()):
        path = lib.REPO_ROOT / name
        if path.suffix.lower() in lib.VIDEO_SUFFIXES:
            errors.append(f"video is staged or tracked: {name} (run: git rm --cached \"{name}\")")
        elif path.is_file() and path.stat().st_size > GITHUB_WARNING_BYTES:
            errors.append(f"file is over 50 MB: {name}")
    return errors


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("run_ids", nargs="*", help="Experiment IDs to check (all if omitted)")
    args = parser.parse_args()

    if args.run_ids:
        run_dirs = [lib.EXPERIMENTS_DIR / run_id for run_id in args.run_ids]
    else:
        run_dirs = sorted(path for path in lib.EXPERIMENTS_DIR.iterdir() if path.is_dir())

    total_errors = 0
    for run_dir in run_dirs:
        if not run_dir.is_dir():
            print(f"{run_dir.name}: ERROR folder not found")
            total_errors += 1
            continue
        errors, warnings = check_run(run_dir)
        total_errors += len(errors)
        print(f"{run_dir.name}: {'FAILED' if errors else 'OK'}")
        for message in errors:
            print(f"  ERROR: {message}")
        for message in warnings:
            print(f"  warning: {message}")

    git_errors = check_git()
    total_errors += len(git_errors)
    for message in git_errors:
        print(f"Git ERROR: {message}")
    if not git_errors:
        print("Git: no videos or oversized files are staged or tracked.")

    if total_errors:
        print(f"\nFound {total_errors} error(s). Do not commit until they are fixed.")
        raise SystemExit(1)
    print("\nAll checks passed.")


if __name__ == "__main__":
    main()
