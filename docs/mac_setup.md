# Mac setup

These notes come from getting FlyRig 1.7.0 to install on an Apple Silicon Mac.
Update them if your setup ends up different.

## The app

The app's old dependencies fail to build with very new versions of Node, and with
spaces in the folder path. Use a path without spaces and an older Node version:

```bash
conda create -n flyrig -c conda-forge nodejs=18 python=3.11 -y
conda activate flyrig
cd PATH/TO/CCIS-2020-011-FlyRig
rm -rf node_modules
npm install
npm start
```

Run `conda activate flyrig` in each new terminal before starting the app. The app
uses `npm start`, as it has no `dev` script.

## This repo

```bash
brew install ffmpeg
python3 -m unittest discover tests
```

The tests should all pass. The app downloads its own copy of FFmpeg for saving
video, but the scripts in this repo need `ffprobe` installed separately.
