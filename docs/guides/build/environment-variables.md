# Environment variables

epresso supports per-environment configuration with a
`.env.development` / `.env.preview` / `.env.production` split.

## Selecting an environment

```bash
epresso build --env <name>      # explicit flag
EPRESSO_ENV=<name> epresso build # or the env var
```

Defaults: `epresso dev` → `development`; `epresso build` / `preview` / `check` →
`production`. The active environment is available in templates as `{{ env }}`.

## Per-environment config: `site.<env>.toml`

`site.<env>.toml` is **deep-merged** over `site.toml`, so a per-environment file
can override the URL, toggles, API keys, etc.:

```toml
# site.staging.toml
[site]
url = "https://staging.example.com"

[search]
enabled = true
```

## Dotenv vars: `.env.<env>`

A dotenv-style file `.env.<env>` (`KEY=VALUE`) is loaded and exposed:

```bash
# .env.production
API_URL=https://api.example.com
FEATURE_X=true
```

Values are trimmed and optional surrounding quotes stripped. These are available:

* to content loaders / plugins via `os.environ` and
* to templates via `{{ env_vars.KEY }}`.

## In templates

```jinja
Environment: {{ env }}
API: {{ env_vars.API_URL }}
```

## Notes

* `EPRESSO_DEBUG=scope1,scope2,*` turns on **debug logging** for matching log
  scopes (`build`, `render`, `content`, `cli`, `server`).
  `EPRESSO_DEBUG=render epresso build` shows a per-route ``[render] render …``
  line for every page; `*` enables debug everywhere.
* `EPRESSO_LOG=<path>` additionally **appends every log line to a file** (plain
  text, no color) while still printing to the console — handy for CI or
  capturing `EPRESSO_DEBUG` output to disk.
* `load_env_file(root, env)` returns the vars as a dict without mutating
  `os.environ`; the site exposes them to templates as `env_vars`.
* epresso is single-locale for now; i18n is reserved for a future release.
