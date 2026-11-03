# Data format

Proposed format for the team to review. It fills in the log and timestamp
formats marked TBD on the block chart.

Each run lives in `experiments/<experiment_id>/`. IDs look like `2026-11-03_001`
(date plus run number). Runs are never overwritten, so a retry gets a new ID.

| File | Pushed? | Contents |
|---|---|---|
| `<id>.mp4` | **No** | Video exactly as the app saved it |
| `frame_timestamps.csv` | Yes | Time of every frame |
| `video_info.json` | Yes | Checksum, resolution, codec, frame count, and timing summary |
| `light_commands.csv` | Yes | Light commands scheduled by the protocol |
| `app_output.csv` | Yes | Unchanged copy of the CSV saved by the app |
| `settings.json` | Yes | Who ran it, camera settings, app version, and app metadata |
| `notes.md` | Yes | Purpose, chamber contents, and anything unusual |
| `analysis/` | **No** | Cropped videos and tracking output, until the team decides otherwise |

## `frame_timestamps.csv`

```text
frame_number,time_ms,delta_ms
0,0.000,
1,33.000,33.000
2,67.000,34.000
```

- `frame_number`: Starts at 0, in display order.
- `time_ms`: Time since the start of the video file.
- `delta_ms`: Time since the previous frame.

These times are extracted from the MP4. The app copies the video stream into the
MP4 without re-encoding it, so the browser recorder's frame times are preserved.

They show when the recorder handled each frame, not the moment the camera sensor
exposed it. They are good for finding gaps and uneven timing, but need to be
checked against the sync LED before being used for precise latency measurements.

## Timing gaps

`video_info.json` flags any frame interval over 1.5 times the median as a gap,
and estimates the missing frames from its length. `check_run.py` also warns when
the measured frame rate is over 5% away from the requested rate.

## `light_commands.csv`

```text
time_ms,led1,led2,led3,led4,amplitude,frequency,pulse_width,odor_l,odor_r
5000,1,1,1,1,50,40,5,,
```

This comes from the cue table the app saves, so **it is the plan, not a record of
what happened**:

- `time_ms` counts from the start of the cue list, not the start of the video.
- Commands sent from **Manual Control** are not included.
- A run without cues has only the header row.

## Lining up video and light

The frame times and cue times use different clocks, so they can't be compared
directly. To line them up:

1. Find the first frame where the IR sync LED is on.
2. Look up that frame's `time_ms` in `frame_timestamps.csv`.
3. Treat that as the time of the stimulus onset.
4. Measure behavior relative to that frame.

An automated LED detector is a good next script to add.

## Storage

Each video exists only on the computer that recorded it unless someone copies
it. Before real experiments, agree on a backup location, because Git can't
restore these files.
