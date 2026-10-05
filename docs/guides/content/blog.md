---
order: 319
description: A blog with posts, archive, categories, pagination and RSS — MkDocs/Material blog posts work unchanged.
---

# Blog

The `epresso_blog` plugin turns a folder of Markdown posts into a blog: a
paginated index, an archive per year, a page per category and an RSS feed. It
reads Material for MkDocs blog posts as they are and builds the same URLs, so a
migrated blog keeps its links. The docs theme enables it.

```text
docs/
└── blog/
    ├── index.md          ← text above the post list (optional)
    ├── .authors.yml      ← author names / avatars (optional)
    └── posts/
        ├── hello.md
        └── hello/
            └── chart.png ← relative images work
```

A post:

```markdown
---
date: 2026-10-03          # a date, a datetime, or {created: …}
authors: [jo]
categories: [Release]
tags: [launch]
draft: false
slug: hello-world         # optional; default: from the title
---

# Hello world

The excerpt shown on the index.

<!-- more -->

The rest of the post.
```

`.authors.yml`:

```yaml
authors:
  jo:
    name: Jo Doe
    avatar: https://example.com/jo.png
    url: https://example.com
```

## Options

The option names and defaults are MkDocs' blog plugin's:

```toml
[plugin.epresso_blog]
blog_dir = "blog"                  # under the docs dir (content/ without epresso_docs)
post_url_format = "{date}/{slug}"  # /blog/2026/10/03/hello-world/; also {file}, {categories}
post_slugify = "title"             # or "file"
pagination_per_page = 10
archive = true                     # /blog/archive/2026/
categories = true                  # /blog/category/release/
authors_file = "{blog_dir}/.authors.yml"
draft = false                      # true: publish drafts in production too
rss = true                         # /blog/rss.xml
layout = "DocsPage"                # page layout (default DocsPage with epresso_docs, else Base)
```

In `docs.toml` the same keys go under `[blog]`; `epresso import mkdocs` fills
them in from the MkDocs `blog` plugin.

## Look

Pages render with the `BlogIndex`, `BlogPost`, `BlogMeta` and `BlogArchive`
components inside the `layout`. Ship a component with the same name in your
site's `components/` to replace one. In the docs theme the blog also gets a
"Blog" sidebar section: all posts and the ten newest.
