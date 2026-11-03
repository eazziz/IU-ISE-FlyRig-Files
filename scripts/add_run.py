#!/usr/bin/env python3
"""Add a FlyRig recording to experiments/ and generate its shareable files.

Example:
    python3 scripts/add_run.py ~/FlyRigRecordings/first_video_2026_11_03T20_00_00_000Z.mp4 \
        --operator Edred --run-type practice --camera "edred Camera"
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import shutil
from pathlib import Path

import flyrig_lib as lib

NOTES_TEMPLATE = """# Notes for {run_id}

Purpose:

What was in each chamber:

Anything unusual:
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video", type=Path, help="Video saved by the FlyRig app")
    parser.add_argument("--app-csv", type=Path, help="CSV saved with the video (found automatically if omitted)")
    parser.add_argument("--id", dest="run_id", help="Experiment ID, such as 2026-11-03_001 (next number today if omitted)")
    parser.add_argument("--operator", help="Who ran the recording")
    parser.add_argument("--run-type", default="practice", choices=["practice", "calibration", "experiment"])
    parser.add_argument("--camera", help="Camera source shown in the app")
    parser.add_argument("--requested-fps", type=float, help="Framerate entered in the app")
    parser.add_argument("--exposure", help="Exposure setting used, if known")
    parser.add_argument("--brightness", help="Brightness setting used, if known")
    parser.add_argument("--move", action="store_true", help="Move the video instead of copying it")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    lib.require_ffprobe()

    video = args.video.expanduser().resolve()
    if not video.is_file():
        lib.die(f"Video not found: {video}")
    if video.suffix.lower() not in lib.VIDEO_SUFFIXES:
        lib.die(f"Unsupported video type: {video.suffix}")

    app_csv = args.app_csv.expanduser().resolve() if args.app_csv else lib.find_app_csv(video)
    if args.app_csv and not app_csv.is_file():
        lib.die(f"App CSV not found: {app_csv}")

    now = dt.datetime.now().astimezone()
    run_id = args.run_id or lib.next_run_id(now.strftime("%Y-%m-%d"))
    if not lib.RUN_ID_RE.match(run_id):
        lib.die(f"Experiment ID must look like 2026-11-03_001, not {run_id}")

    run_dir = lib.EXPERIMENTS_DIR / run_id
    if run_dir.exists():
        lib.die(f"{run_dir} already exists. Runs are never overwritten, so use a new ID.")

    # Read everything before creating the folder, so a bad file leaves nothing behind.
    print(f"Reading {video.name} ...")
    video_details = lib.probe_video(video)
    times_ms = lib.read_frame_times_ms(video)
    timing = lib.analyze_timing(times_ms)
    checksum = lib.sha256_of(video)
    base_name, cues, app_metadata = lib.parse_app_csv(app_csv) if app_csv else (None, [], {})

    run_dir.mkdir(parents=True)
    video_name = f"{run_id}{video.suffix.lower()}"
    if args.move:
        shutil.move(str(video), run_dir / video_name)
    else:
        shutil.copy2(video, run_dir / video_name)
    if app_csv:
        shutil.copy2(app_csv, run_dir / "app_output.csv")

    lib.write_frame_timestamps(run_dir / "frame_timestamps.csv", times_ms)
    lib.write_light_commands(run_dir / "light_commands.csv", cues)

    video_info = {
        "experiment_id": run_id,
        "video_filename": video_name,
        "sha256": checksum,
        **video_details,
        "timestamp_source": "video_presentation_timestamps",
        "timing": timing,
    }
    (run_dir / "video_info.json").write_text(json.dumps(video_info, indent=2) + "\n")

    settings = {
        "experiment_id": run_id,
        "created_at": now.isoformat(timespec="seconds"),
        "run_type": args.run_type,
        "operator": args.operator,
        "original_filename": video.name,
        "app": {"name": "FlyRig", "version": "1.7.0", "base_filename": base_name},
        "camera": {
            "source": args.camera,
            "requested_fps": args.requested_fps,
            "exposure": args.exposure,
            "brightness": args.brightness,
        },
        "light_command_count": len(cues),
        "app_metadata": app_metadata,
        "repo_commit": lib.git_output("rev-parse", "--short", "HEAD"),
    }
    (run_dir / "settings.json").write_text(json.dumps(settings, indent=2) + "\n")
    (run_dir / "notes.md").write_text(NOTES_TEMPLATE.format(run_id=run_id))

    print(f"\nAdded {run_id}")
    print(f"  Folder: {run_dir}")
    print(f"  Frames: {timing['frame_count']} over {timing['duration_seconds']} s")
    print(f"  Average rate: {timing['average_fps']} fps")
    print(f"  Median frame interval: {timing['median_frame_interval_ms']} ms")
    print(f"  Timing gaps: {timing['gap_count']} (about {timing['estimated_missing_frames']} missing frames)")
    print(f"  Light commands: {len(cues)}")
    if not app_csv:
        print("  App CSV: not found, so light_commands.csv has only its header")
    print(f"\nNext: fill in notes.md, then run: python3 scripts/check_run.py {run_id}")


if __name__ == "__main__":
    main()
