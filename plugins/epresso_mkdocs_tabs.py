"""Deprecated alias: ``epresso_mkdocs_tabs`` is now part of ``epresso_mkdocs``.

``plugins = ["epresso_mkdocs_tabs"]`` keeps working and enables the full MkDocs
syntax plugin (tabs, admonitions, attr_list, snippets, …).
"""

from __future__ import annotations

from epresso_mkdocs import epresso_mkdocs

content_tabs = epresso_mkdocs()
