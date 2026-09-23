---
order: 316
---

# RSS

epresso can emit an RSS/Atom feed from any content collection. It's configured
under `[seo.rss]` in `site.toml`:

```toml
[seo.rss]
enabled = true
collection = "blog"        # collection to publish
path = "/rss.xml"          # output path
title = "My blog"
description = "Posts and notes"
limit = 20                 # optional: cap entries (newest N)
url_template = "/{collection}/{id}/"   # how an entry's id maps to its URL
```

When enabled, epresso renders the feed at `path` from the chosen collection. Each
entry links to the URL derived from `url_template` (default `/{collection}/{id}/`).

## Entry order & metadata

Entries are included newest-first (by the collection's load order). The feed uses
each entry's `title`, `description`/excerpt, and `body`.

## Notes

- `url_template` is a static template — it must express the site's real URL scheme
  for a given collection. If your routes don't match `/{collection}/{id}/` (e.g. a
  theme that flattens or re-prefixes doc paths), a theme-owned feed *endpoint*
  (see [endpoints](endpoints.md) is the better fit.
