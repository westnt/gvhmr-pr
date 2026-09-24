from __future__ import annotations

import importlib
import sys
import types

import pytest
from hydra import compose, initialize_config_module
from hydra.errors import OverrideParseException

from gvhmr.cli.demo import _even_render_size, _quoted_override
from gvhmr.configs import register_store_gvhmr

BRACKETED = "clip [ID], take=1: 'x' \"y\""


def test_bare_override_with_brackets_is_what_breaks_hydra():
    register_store_gvhmr()
    with initialize_config_module(version_base="1.3", config_module="gvhmr.configs"):
        with pytest.raises(OverrideParseException):
            compose(config_name="demo", overrides=["video_name=title[ID]"])


def test_quoted_overrides_round_trip_hydra_syntax_chars():
    register_store_gvhmr()
    with initialize_config_module(version_base="1.3", config_module="gvhmr.configs"):
        cfg = compose(
            config_name="demo",
            overrides=[_quoted_override("video_name", BRACKETED), _quoted_override("output_root", "out/[batch]")],
        )
    assert cfg.video_name == BRACKETED
    assert cfg.output_root == "out/[batch]"


@pytest.mark.parametrize(
    ("w", "h", "scale"),
    [(1080, 1082, 0.5), (1080, 1920, 1.0), (1081, 1919, 1.0), (1280, 720, 0.33), (3, 3, 0.1)],
)
def test_even_render_size(w, h, scale):
    for got, src in zip(_even_render_size(w, h, scale), (w, h)):
        assert got % 2 == 0
        assert got == 2 or abs(got - src * scale) <= 1  # nearest even, floored at the 2px minimum


def test_even_render_size_keeps_even_sources_exact():
    assert _even_render_size(1080, 1920, 1.0) == (1080, 1920)
    assert _even_render_size(1080, 1920, 0.5) == (540, 960)


@pytest.fixture
def tracker_module(monkeypatch):
    try:
        import ultralytics  # noqa: F401
    except ImportError:  # CI's base install has no preproc extra; the tracker only needs the YOLO name
        monkeypatch.setitem(sys.modules, "ultralytics", types.SimpleNamespace(YOLO=None))
        monkeypatch.delitem(sys.modules, "gvhmr.utils.preproc.tracker", raising=False)
    return importlib.import_module("gvhmr.utils.preproc.tracker")


def test_no_person_detected_raises_clear_error(tracker_module, monkeypatch):
    monkeypatch.setattr(tracker_module, "get_video_lwh", lambda _: (3, 640, 480))
    tracker = object.__new__(tracker_module.Tracker)
    monkeypatch.setattr(tracker, "track", lambda _: [[], [], []], raising=False)
    with pytest.raises(RuntimeError, match="no person detected in empty.mp4"):
        tracker.get_one_track("empty.mp4")
