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
    with pytest.raises(SystemExit) as exc:
        demo_folder.run(tmp_path)
    assert exc.value.code == 1
    assert seen == ["a.mp4", "b[ID].mp4", "c.mp4"]


def test_all_videos_ok_returns_normally(tmp_path, monkeypatch):
    (tmp_path / "a.mp4").touch()
    monkeypatch.setattr(demo, "run", lambda video, **_: None)
    demo_folder.run(tmp_path)
