# Blocks and ownership

Edred took over the camera blocks from Micah. Update this page if ownership
changes or a task is finished. The tasks below are a working interpretation of
the block chart, so check them against the team's requirements.

| Block | Owner | Purpose |
|---|---|---|
| Video Recorder | Edred | Record video and save frame timing |
| Data Output / Experiment Files | Edred | Keep each run's files together under one ID |
| IR Camera | Edred | Capture fly behavior over USB 2.0 |
| IR Sync LED | Edred | Mark the red-light onset in the video |
| Behavior Chamber / Arena | Roderick | Hold the flies |
| Camera Mount & Alignment | Roderick | Hold the camera in a repeatable position |
| Light-Tight Enclosure & Loading | Roderick | Block outside light |

## Video Recorder

- [ ] Record and add a first practice video
- [ ] Test start and stop with the app's controls
- [ ] Check timing over a full-length recording
- [ ] Find out whether the preview's pink and green stripe appears in saved video

## Data Output / Experiment Files

- [x] Draft file layout and formats
- [ ] Review [data_format.md](data_format.md) with the team and whoever analyzes the data
- [ ] Agree on where videos are backed up
- [ ] Decide whether to log the commands actually sent, not just the plan

## IR Camera

- [ ] Confirm we have the wiki's camera: ELP Sony IMX323 USB module, 2.8–12 mm lens
- [ ] Attach the IR filter over the lens
- [ ] Work out the camera mounting with Roderick
- [ ] Test image quality with the real camera under IR light
- [ ] Choose and record frame rate, exposure, and brightness

## IR Sync LED

- [ ] Wire the indicator LED to the control board
- [ ] Confirm which pin it uses
- [ ] Position it where the camera can see it
- [ ] Measure how closely it matches the red light
- [ ] Write a script that finds the LED onset frame

## Needs a decision

The [build guide](https://github.com/hoopfere/FlyRig/wiki/Building-FlyRig) says
the software runs most stably on Windows, though it can run on a Mac. We're using
a Mac, so test a full-length recording before committing to it for experiments.
