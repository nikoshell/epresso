"""Enable the local example plugins for this demo site.

epresso loads this file automatically (alongside any ``[plugins]`` dotted paths
in ``site.toml``). Building plugins with a *factory* here is how you pass per-
plugin options — something a bare dotted-path string cannot carry.

The modules live one directory up (``examples/plugins/``), so we put that on
``sys.path``. For a real project, ``pip install``/``uv add`` the plugin package
instead and reference it from ``site.toml``.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from greeter import greeter  # noqa: E402
from quotes import quotes  # noqa: E402
from watermark import watermark  # noqa: E402

# Each module-level Plugin instance is discovered by epresso.
greeting = greeter(text="hello from a plugin", shout=True)
the_mark = watermark()
the_quotes = quotes(
    [
        {"id": "one", "data": {"text": "First, make it deterministic.", "author": "epresso"}},
        {"id": "two", "data": {"text": "Then make it incremental.", "author": "epresso"}},
    ]
)
