"""``--profile`` output: the cProfile record shape and its artifact filtering."""

import cProfile
from pathlib import Path

from epresso.cli import _frame_label, _print_profile


def _busy() -> int:
    return sum(i * i for i in range(2000))


def test_frame_label_passes_builtin_names_through():
    assert _frame_label("<built-in method builtins.len>") == "<built-in method builtins.len>"


def test_frame_label_renders_code_objects_as_path_line_name():
    label = _frame_label(_busy.__code__)
    assert label.endswith("(_busy)")
    assert label.startswith("tests/unit/test_cli_profile.py:")


def test_print_profile_ranks_by_self_time_and_hides_profiler_artifacts(capsys):
    prof = cProfile.Profile()
    prof.runcall(_busy)
    _print_profile(prof, Path("epresso-profile.pstats"), top=20)
    out = capsys.readouterr().out
    # getstats() leaks the profiler's own enable/disable bookkeeping as a frame.
    assert "_lsprof" not in out
    assert "(_busy)" in out
    assert "epresso-profile.pstats" in out
    assert "python -m pstats" in out
