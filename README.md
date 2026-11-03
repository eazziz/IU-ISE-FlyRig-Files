# FlyRig Camera

Shared workspace for the camera side of our FlyRig capstone project: the IR
camera, video recording, IR sync LED, and experiment files.

The FlyRig app itself lives in its [own repository](https://github.com/CC-IS/CCIS-2020-011-FlyRig).
Hardware and build instructions are on the [FlyRig wiki](https://github.com/hoopfere/FlyRig/wiki).

## The one rule

**Videos stay on the computer that recorded them. Everything else gets pushed.**

`.gitignore` blocks video files, and each run stores the video's size, details,
and checksum so a teammate can confirm they have the right file.

## Start here

| To do this | Read this |
|---|---|
| Record and add a run | [docs/first_video.md](docs/first_video.md) |
| See who owns what and what's left | [docs/blocks.md](docs/blocks.md) |
| Understand each saved file | [docs/data_format.md](docs/data_format.md) |
| Avoid known app problems | [docs/app_notes.md](docs/app_notes.md) |
| Set up the app on a Mac | [docs/mac_setup.md](docs/mac_setup.md) |

## Everyday workflow

```bash
git pull
python3 scripts/add_run.py ~/FlyRigRecordings/YOUR_VIDEO.mp4 --operator YOUR_NAME --camera "CAMERA NAME" --requested-fps 30
# Fill in experiments/<id>/notes.md
git add .
python3 scripts/check_run.py
git commit -m "Add run <id>"
git push
```

The scripts need Python 3.9 or newer and `ffprobe`, which comes with FFmpeg
(`brew install ffmpeg`). To test them, run `python3 -m unittest discover tests`.

## Layout

```text
docs/         Setup notes, data format, and app notes
experiments/  One folder per run; videos stay local
scripts/      add_run.py and check_run.py
tests/        End-to-end test using a generated video
```
