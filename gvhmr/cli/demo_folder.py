"""``gvhmr demo-folder`` — run the demo over every video in a folder (in-process)."""

from __future__ import annotations

from pathlib import Path

from rich.markup import escape

from gvhmr.utils.console import console, rule
from gvhmr.utils.pylogger import Log


def run(
    folder: Path,
    *,
    output_root: str | None = None,
    static_cam: bool = False,
    camera: str | None = None,
    use_dpvo: bool = False,
    f_mm: int | None = None,
    f_px: float | None = None,
    render_scale: float | None = None,
    no_render: bool = False,
    smplx: bool = False,
) -> list[tuple[Path, str]]:
    """Returns the ``(video, error)`` pairs that failed; one failure doesn't stop the rest."""
    from gvhmr.cli.demo import run as run_demo

    folder = Path(folder)
    videos = sorted([*folder.glob("*.mp4"), *folder.glob("*.MP4")])
    Log.info(f"Found [gvhmr]{len(videos)}[/] videos in [muted]{folder}[/]")
    failed: list[tuple[Path, str]] = []
    for k, video in enumerate(videos, 1):
        rule(f"[{k}/{len(videos)}] {escape(video.name)}")
        try:
            run_demo(
                video,
                output_root=output_root,
                static_cam=static_cam,
                camera=camera,
                use_dpvo=use_dpvo,
                f_mm=f_mm,
                f_px=f_px,
                render_scale=render_scale,
                no_render=no_render,
                smplx=smplx,
            )
        except Exception as e:
            console.print_exception()
            msg = f"{type(e).__name__}: {e}"
            Log.warning(f"[warn]failed[/] {escape(video.name)}: {escape(msg)} — continuing")
            failed.append((video, msg))
        else:
            continue
        # Outside the except, so the traceback (whose frames pin the failed run's GPU tensors) is gone —
        # otherwise the next video OOMs on a small card.
        _release_gpu_memory()

    if failed:
        rule(f"{len(failed)}/{len(videos)} failed")
        for video, msg in failed:
            Log.warning(f"{escape(video.name)}: {escape(msg)}")
    return failed


def _release_gpu_memory() -> None:
    import gc

    import torch

    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
