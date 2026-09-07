"""Example plugin: expose a configurable template global + filter.

Demonstrates the *factory* construction style — a function that takes options
and returns a :class:`epresso.plugins.Plugin`. Use it from a project ``plugins.py``
(or, if installed as a package, from a dotted path) to add a ``greeting`` global
and a ``shout`` filter to every template.
"""

from epresso.plugins import Plugin


def greeter(*, text: str = "hello", shout: bool = False) -> Plugin:
    """Return a plugin exposing ``{{ greeting() }}`` and ``{{ s | shout }}``."""

    def on_setup(caps):
        caps.add_global("greeting", lambda: text.upper() if shout else text)
        caps.add_filter("shout", lambda s: str(s).upper())

    return Plugin(name="greeter", hooks={"on_setup": on_setup})
