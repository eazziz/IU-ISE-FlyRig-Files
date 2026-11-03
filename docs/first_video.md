# Your first video

This practice run needs only the app and a camera, not the control board. It
tests the file workflow, not the final rig. The app's "Please connect the
control board" message can be ignored for this run.

## 1. Install FFmpeg

```bash
brew install ffmpeg
ffprobe -version
```

## 2. Make a recordings folder

```bash
mkdir -p ~/FlyRigRecordings
```

Keep hyphens and periods out of this folder's full path. The app rewrites them
when it saves, which would point it at the wrong folder. See
[app_notes.md](app_notes.md).

## 3. Record

1. Start the app with `npm start`.
2. Open **Recording Options**.
3. Set **Time (seconds)** to `30`.
4. Set **File Base Name** to `first_video`.
5. Next to **Save location**, click **Set** and choose `FlyRigRecordings`. Do
   this even if the box already shows a path.
6. Click **Record** and wait for it to finish.
7. Wait for the app to say **Saved video file.**

You should see one `.mp4` and one `.csv` in the folder:

```bash
ls -lh ~/FlyRigRecordings
```

## 4. Add the run

From this repo's folder:

```bash
python3 scripts/add_run.py ~/FlyRigRecordings/first_video_*.mp4 \
  --operator YOUR_NAME \
  --run-type practice \
  --camera "CAMERA NAME FROM THE APP" \
  --requested-fps 30
```

For a 30-second recording at 30 fps, expect about 900 frames, a median frame
interval near 33 ms, and few or no gaps.

## 5. Add notes

Open `experiments/<id>/notes.md` and fill it in. Also say whether the pink and
green stripe from the live preview appears in the saved video.

## 6. Check before committing

```bash
git add .
python3 scripts/check_run.py
git status
```

`git status` should list the new run's files but no `.mp4`.

## 7. Push

```bash
git commit -m "Add first practice video"
git push
```

Teammates who pull will get the timing, settings, and notes, but not the video.
If they need to watch it, send it separately and compare its checksum with
`sha256` in `video_info.json` by running `shasum -a 256 FILE`.
