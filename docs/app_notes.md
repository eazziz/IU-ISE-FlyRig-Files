# FlyRig app notes

Found by reading the source of FlyRig 1.7.0. These haven't all been tested on
our rig. Paths are relative to the
[app repository](https://github.com/CC-IS/CCIS-2020-011-FlyRig).

## What the app saves

Each recording produces two files, named from the base name and the time:

- `<base>_<time>.mp4`: H.264 video with no audio.
- `<base>_<time>.csv`: Base name, cue table, and metadata.

It does not save a separate frame timestamp file, a record of the commands
actually sent, or the camera settings. `add_run.py` fills the first gap, and
`--camera`, `--requested-fps`, `--exposure`, and `--brightness` cover the last.

## Problems to work around

**Hyphens and periods in the save path get replaced.** The app replaces every `-`
and `.` with `_` across the whole save path, not just the filename
(`app/local/src/camera.js`, lines 162 and 170). Saving to a folder like
`~/flyrig-data` would point at `~/flyrig_data`, which probably doesn't exist.
Use a path without either character. The same rewrite changes a base name of
`2026-11-03_001` to `2026_11_03_001`, so use a simple base name and let
`add_run.py` assign the ID.

**The save location box can be misleading.** It shows your home folder at launch,
but the camera's save path stays blank until you change it
(`app/local/src/app.js`, lines 111 and 433–442). Without that change, files
should land in the folder the app was started from. Always click **Set**.

**Video and CSV names can differ slightly.** Each gets its own timestamp
(`camera.js`, lines 162 and 170). `add_run.py` allows for this by matching the
base name and nearest time within 5 seconds. Use `--app-csv` if it misses.

**Cue times don't start with the video.** **Run** starts the cue timer before it
starts recording (`app.js`, lines 392–400), and recording takes time to begin. A
cue at 5 seconds won't be at exactly 5 seconds in the video, which is why we
need the sync LED.

## Sync LED

The firmware already supports it. The indicator output is pin 4 or pin 3,
depending on the board (`arduino program/lightController/lightController.ino`,
line 18), and it goes high when a stimulation sequence starts.

It stays on for the whole stimulation block rather than flashing with each pulse.
Its rising edge marks the onset, and the falling edge should mark the end. Confirm
this on the bench, and record which pin your board uses.

## Power

From the [build guide](https://github.com/hoopfere/FlyRig/wiki/Building-FlyRig):
if the power supply is connected but the Metro Mini board isn't, the LEDs stay on
at full intensity. Connect the board first when flies are in the chamber.
