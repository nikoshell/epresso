# Type checking & tooling

epresso is **Python**, so there is no TypeScript layer — types come from Python
type hints plus Pydantic.

- **Content typing** — collection entries are validated against a Pydantic schema
  (`content.config.py`), so the shape of every entry is enforced.
- **Component props** — a `.ep` frontmatter declares `class Props(BaseModel)`, and
  the framework validates props against it before rendering.
- **Frontmatter / routes** — page and component frontmatter is real Python, so your
  editor type-checks it.
- **Static checks** — run `pyright` over your project for type checking and `ruff`
  for lint/format. (epresso itself ships pyright-clean.)

## Editor setup

Any Python-capable editor works. For `.ep` files, syntax highlighting comes from
the surrounding Markup + Python; see [Editor setup](../editor-setup).
