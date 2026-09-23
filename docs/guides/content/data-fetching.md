---
order: 314
---

# Data fetching

Content collections are loaded from disk (glob) or from a **loader** function,
which can fetch remote/derived data at build time.

## Python loader

Pass `loader=` to `define_collection`. The function returns an iterable of
`{"id", "data", "body"}` dicts:

```python
def fetch_authors():
    resp = requests.get("https://api.example.com/authors").json()
    return [{"id": a["id"], "data": a} for a in resp]

authors = define_collection("authors", loader=fetch_authors, schema=Author)
```

The loader may be `async` (epresso awaits it). Entries are validated against the
schema and get a content digest for incremental builds.

## Remote data

Loaders run at build time, so you can pull from any HTTP API, database, or
service — the data is fetched once and baked into the static site.

## Environment-aware

Loaders/plugins see environment variables via `os.environ` and the per-env
dotenv files — see [Environment variables](../build/environment-variables.md.

## See also

- [Content collections](content-collections.md — the collection model
