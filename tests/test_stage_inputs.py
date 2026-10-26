"""Synthetic, offline safety tests for staging personal shot media into ComfyUI."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from unittest import mock
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "env" / "stage_inputs.py"
SPEC = importlib.util.spec_from_file_location("bench_stage_inputs", SCRIPT)
stage = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(stage)


class InputStageSafetyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.shot = self.root / "source"
        self.shot.mkdir()
        self.comfy = self.root / "comfy"
        self.comfy.mkdir()
        for i, name in enumerate(stage.FILES):
            (self.shot / name).write_bytes(("synthetic-pixels-%d" % i).encode())

    def test_copy_is_create_only_and_preserves_source_bytes(self):
        targets = stage.stage_inputs(self.comfy, self.shot, copy=True)
        self.assertEqual(len(targets), 4)
        for name in stage.FILES:
            source = self.shot / name
            target = self.comfy / "input" / name
            self.assertEqual(target.read_bytes(), source.read_bytes())
            self.assertFalse(target.is_symlink())
        with self.assertRaises(FileExistsError):
            stage.stage_inputs(self.comfy, self.shot, copy=True)
        self.assertEqual(targets[0].read_bytes(), (self.shot / stage.FILES[0]).read_bytes())

    def test_symlink_stage_remains_idempotent(self):
        targets = stage.stage_inputs(self.comfy, self.shot)
        self.assertTrue(all(x.is_symlink() for x in targets))
        self.assertEqual(stage.stage_inputs(self.comfy, self.shot), targets)

    def test_missing_final_asset_causes_zero_staging_side_effects(self):
        (self.shot / stage.FILES[-1]).unlink()
        with self.assertRaises(FileNotFoundError):
            stage.stage_inputs(self.comfy, self.shot, copy=True)
        self.assertFalse((self.comfy / "input").exists())

    def test_conflicting_final_destination_is_detected_before_first_copy(self):
        dest = self.comfy / "input"
        dest.mkdir()
        protected = dest / stage.FILES[-1]
        protected.write_bytes(b"existing-protected-user-asset")
        with self.assertRaises(FileExistsError):
            stage.stage_inputs(self.comfy, self.shot, copy=True)
        self.assertEqual(protected.read_bytes(), b"existing-protected-user-asset")
        self.assertFalse((dest / stage.FILES[0]).exists())

    def test_competing_create_is_not_overwritten(self):
        original = stage._exclusive_copy
        contender = self.comfy / "input" / stage.FILES[0]

        def racing_copy(source, target):
            target.write_bytes(b"other-process-won")
            return original(source, target)

        with mock.patch.object(stage, "_exclusive_copy", side_effect=racing_copy):
            with self.assertRaises(FileExistsError):
                stage.stage_inputs(self.comfy, self.shot, copy=True)
        self.assertEqual(contender.read_bytes(), b"other-process-won")

    def test_stream_failure_removes_only_own_incomplete_file(self):
        target = self.comfy / "input" / stage.FILES[0]

        def failing_copy(reader, writer, length):
            writer.write(b"partial-data")
            raise OSError("fabricated disk error")

        with mock.patch.object(stage.shutil, "copyfileobj", side_effect=failing_copy):
            with self.assertRaisesRegex(OSError, "fabricated disk error"):
                stage.stage_inputs(self.comfy, self.shot, copy=True)
        self.assertFalse(target.exists())
        self.assertEqual((self.shot / stage.FILES[0]).read_bytes(), b"synthetic-pixels-0")

    def test_symlinked_comfy_input_directory_is_not_followed(self):
        external = self.root / "external"
        external.mkdir()
        (self.comfy / "input").symlink_to(external, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, "symlinked"):
            stage.stage_inputs(self.comfy, self.shot, copy=True)
        self.assertEqual(list(external.iterdir()), [])

    def test_dangling_destination_symlink_cannot_be_overwritten(self):
        dest = self.comfy / "input"
        dest.mkdir()
        marker = dest / stage.FILES[0]
        marker.symlink_to(self.root / "missing-target")
        with self.assertRaises(FileExistsError):
            stage.stage_inputs(self.comfy, self.shot, copy=True)
        self.assertTrue(marker.is_symlink())


if __name__ == "__main__":
    unittest.main()
