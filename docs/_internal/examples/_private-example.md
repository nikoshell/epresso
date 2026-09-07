---
title: Private example
description: A page marked private via its `_`-prefixed filename; shown only in development/preview, hidden from production.
---

# Private example

Files (or directories) prefixed with `_` are **private**: the docs theme treats
them as not-ready-for-publication and excludes them from production builds while
keeping them available in `development`/`preview`.

A private page is useful for:

- draft release notes and in-progress guides you want to review rendered;
- internal/team-only notes that shouldn't ship;
- showcase pages like the [typography example](./_typography.md) used to test
  Markdown styling before it goes public.
