"""CI coverage for the ``cn`` / variant helpers.

Both modules ship a runnable self-check (``python -m epresso.classes`` /
``python -m epresso.variants``); calling ``main()`` here puts them in front of
pytest, so a regression fails CI instead of only a manual run.
"""

from epresso import classes, variants


def test_cn_self_check():
    assert classes.main() == 0


def test_variants_self_check():
    assert variants.main() == 0
