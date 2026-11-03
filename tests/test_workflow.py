"""End-to-end test using a generated video. Run: python3 -m unittest discover tests"""
import csv
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP_CSV = (
    "Base filename,first_video\n"
    "Time (sec),LED1,LED2,LED3,LED4,Amplitude,Frequency,Pulse width,Odor_L,Odor_R\n"
    "1,1,1,1,1,50,40,5,,\n"
    "2,0,0,0,0,0,0,0,,\n"
    "end\n\nMetadata\n"
    '"Genotype","test flies"\n'
)
STAMP = "2026_11_03T20_00_00_{}Z"


@unittest.skipUnless(shutil.which("ffmpeg") and shutil.which("ffprobe"), "ffmpeg is required")
class WorkflowTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name) / "path with spaces"
        self.repo = base / "repo"
        self.repo.mkdir(parents=True)
        shutil.copytree(REPO / "scripts", self.repo / "scripts", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy(REPO / ".gitignore", self.repo / ".gitignore")
        (self.repo / "experiments").mkdir()
        self.git("init", "-q")

        self.recordings = base / "recordings"
        self.recordings.mkdir()
        self.video = self.recordings / f"first_video_{STAMP.format('123')}.mp4"
        # 3 seconds at 30 fps with frames 30-34 removed, leaving a 200 ms gap.
        subprocess.run([
            "ffmpeg", "-v", "error", "-f", "lavfi", "-i", "testsrc=size=320x240:rate=30:duration=3",
            "-vf", "select='not(between(n,30,34))'", "-fps_mode", "passthrough",
            "-pix_fmt", "yuv420p", str(self.video),
        ], check=True)
        # The app stamps the CSV separately, so its name can differ slightly.
        (self.recordings / f"first_video_{STAMP.format('125')}.csv").write_text(APP_CSV)

    def tearDown(self):
        self.temp.cleanup()

    def git(self, *args):
        return subprocess.run(["git", *args], cwd=self.repo, capture_output=True, text=True, check=True).stdout

    def script(self, name, *args, check=True):
        return subprocess.run(
            [sys.executable, str(self.repo / "scripts" / name), *args],
            cwd=self.repo, capture_output=True, text=True, check=check,
        )

    def add_run(self, run_id="2026-11-03_001"):
        self.script("add_run.py", str(self.video), "--id", run_id, "--operator", "Test", "--camera", "Test camera")
        return self.repo / "experiments" / run_id

    def test_gap_and_light_commands_are_recorded(self):
        run = self.add_run()
        timing = json.loads((run / "video_info.json").read_text())["timing"]
        self.assertEqual(timing["frame_count"], 85)
        self.assertEqual(timing["gap_count"], 1)
        self.assertEqual(timing["estimated_missing_frames"], 5)
        self.assertEqual(timing["gaps"][0]["after_frame"], 29)
        self.assertAlmostEqual(timing["gaps"][0]["gap_ms"], 200, delta=1)

        with (run / "light_commands.csv").open(newline="") as handle:
            commands = list(csv.DictReader(handle))
        self.assertEqual([row["time_ms"] for row in commands], ["1000", "2000"])
        settings = json.loads((run / "settings.json").read_text())
        self.assertEqual(settings["app"]["base_filename"], "first_video")
        self.assertEqual(settings["app_metadata"], {"Genotype": "test flies"})

    def test_git_tracks_everything_except_the_video(self):
        run = self.add_run()
        self.assertTrue((run / "2026-11-03_001.mp4").is_file())
        self.git("add", ".")
        tracked = self.git("ls-files").splitlines()
        self.assertFalse([name for name in tracked if name.endswith(".mp4")])
        for name in ("frame_timestamps.csv", "light_commands.csv", "settings.json",
                     "video_info.json", "notes.md", "app_output.csv"):
            self.assertIn(f"experiments/2026-11-03_001/{name}", tracked)
        self.assertEqual(self.script("check_run.py").returncode, 0)

    def test_force_added_video_fails_the_check(self):
        run = self.add_run()
        self.git("add", "-f", str(run / "2026-11-03_001.mp4"))
        result = self.script("check_run.py", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("video is staged or tracked", result.stdout)

    def test_clone_without_video_only_warns(self):
        run = self.add_run()
        (run / "2026-11-03_001.mp4").unlink()
        result = self.script("check_run.py")
        self.assertIn("video is not on this computer", result.stdout)

    def test_wrong_frame_rate_warns(self):
        self.script("add_run.py", str(self.video), "--id", "2026-11-03_001", "--requested-fps", "60")
        result = self.script("check_run.py")
        self.assertIn("60.0 fps was requested", result.stdout)

    def test_altered_video_fails_the_check(self):
        run = self.add_run()
        with (run / "2026-11-03_001.mp4").open("ab") as handle:
            handle.write(b"changed")
        self.assertEqual(self.script("check_run.py", check=False).returncode, 1)

    def test_existing_run_is_not_overwritten(self):
        self.add_run()
        result = self.script("add_run.py", str(self.video), "--id", "2026-11-03_001", check=False)
        self.assertEqual(result.returncode, 1)
        self.assertIn("never overwritten", result.stderr)

    def test_next_id_increments(self):
        self.add_run("2026-11-03_001")
        self.script("add_run.py", str(self.video), "--id", "2026-11-03_002")
        sys.path.insert(0, str(self.repo / "scripts"))
        try:
            import importlib
            import flyrig_lib
            importlib.reload(flyrig_lib)
            self.assertEqual(flyrig_lib.next_run_id("2026-11-03"), "2026-11-03_003")
        finally:
            sys.path.pop(0)
            sys.modules.pop("flyrig_lib", None)


if __name__ == "__main__":
    unittest.main()
