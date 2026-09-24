from __future__ import annotations

import importlib

import pytest

import gvhmr.cli.demo as demo

demo_folder = importlib.import_module("gvhmr.cli.demo_folder")


def test_one_failing_video_does_not_abort_the_batch(tmp_path, monkeypatch):
    for name in ["a.mp4", "b[ID].mp4", "c.mp4"]:
        (tmp_path / name).touch()
    seen = []

    def fake_run(video, **_):
        seen.append(video.name)
        if video.name == "b[ID].mp4":
            raise RuntimeError("no person detected")

    monkeypatch.setattr(demo, "run", fake_run)
    failed = demo_folder.run(tmp_path)
    assert seen == ["a.mp4", "b[ID].mp4", "c.mp4"]
    assert [(v.name, msg) for v, msg in failed] == [("b[ID].mp4", "RuntimeError: no person detected")]


def test_all_videos_ok_returns_no_failures(tmp_path, monkeypatch):
    (tmp_path / "a.mp4").touch()
    monkeypatch.setattr(demo, "run", lambda video, **_: None)
    assert demo_folder.run(tmp_path) == []


@pytest.mark.parametrize(("failed", "code"), [([], 0), ([("x.mp4", "boom")], 1)])
def test_cli_exit_code_reflects_failures(tmp_path, monkeypatch, failed, code):
    from typer.testing import CliRunner

    from gvhmr.cli import app

    monkeypatch.setattr(demo_folder, "run", lambda *a, **k: failed)
    assert CliRunner().invoke(app, ["demo-folder", str(tmp_path)]).exit_code == code
