# FlyRig Camera

Run data for the FlyRig capstone project. The app itself lives in its
[own repository](https://github.com/CC-IS/CCIS-2020-011-FlyRig).

**Videos stay on the computer that recorded them. Everything else gets pushed.**

```text
experiments/  One folder per run, created automatically by the app
scripts/      add_run.py and check_run.py
tests/        End-to-end test
```

## After recording

The app adds each run automatically. Fill in `experiments/<id>/notes.md`, then:

```bash
git add .
python3 scripts/check_run.py
git commit -m "Add run <id>"
git push
```
