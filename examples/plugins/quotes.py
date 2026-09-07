"""Example plugin: contribute a content collection at build time.

Demonstrates ``register_collection`` — the before_load capability that plugs a
new collection (from a loader) into the same store as ``content.config.py``. This
is epresso's answer to Astro's content-layer loaders: reusable data sources
(remote APIs, feeds, CSV) become collections templates can read with
``get_collection`` / ``get_entry``.
"""

from epresso.plugins import Plugin


def quotes(items: list[dict]) -> Plugin:
    """Register a ``quotes`` collection from a static list of {id, data} entries.

    A realistic loader would ``fetch`` a remote source; the shape returned here
    is identical: an iterable of ``{"id": ..., "data": ...}`` records.
    """

    def before_load(caps):
        caps.register_collection("quotes", loader=lambda: list(items))

    return Plugin(name="quotes", hooks={"before_load": before_load})
