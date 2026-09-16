"""``python -m epresso`` — same CLI as the ``epresso`` console script.

Mostly here so profilers can wrap it directly::

    python -m cProfile -s tottime -m epresso build themes/docs
    py-spy record -o perf.svg -- python -m epresso build themes/docs
"""

from .cli import main

if __name__ == "__main__":
    main()
