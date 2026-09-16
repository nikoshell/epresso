# PR documentation previews

Two workflows implement per-PR documentation previews while leaving the
production deployment (`deploy-docs.yml`) untouched:

| Workflow | Trigger | Privilege | Role |
|----------|---------|-----------|------|
| `preview-docs.yml` | `pull_request` (opened/synchronize/reopened/closed) | read-only token, **no secrets** | Build the PR's docs, upload static artifact |
| `preview-publish.yml` | `workflow_run` on "Docs Preview Build" | base-repo token + `DOCS_PREVIEW_TOKEN` | Publish/remove the preview, comment on the PR |

`workflow_run` always runs the **default-branch** definition of the publishing
workflow, so a fork PR can never execute code next to the deployment token.

## Required GitHub configuration

### 1. Dedicated preview repository

Previews must not be published into the production Pages site (that would
overwrite `/epresso/`), so create a separate repository, e.g.:

```
nikoshell/epresso-preview
```

* Enable **Pages** → *Deploy from a branch* → branch `gh-pages`, folder `/`.
* The published layout is one directory per PR:

```
gh-pages/
  pr-123/   → https://nikoshell.github.io/epresso-preview/pr-123/
  pr-124/   → https://nikoshell.github.io/epresso-preview/pr-124/
```

### 2. Repository variables

Settings → Secrets and variables → Actions → **Variables**:

| Variable | Example | Meaning |
|----------|---------|---------|
| `DOCS_PREVIEW_REPO` | `nikoshell/epresso-preview` | Target repo for previews |
| `DOCS_PREVIEW_URL` | `https://nikoshell.github.io/epresso-preview` | Base URL previews are served from (no trailing slash) |
| `DOCS_PREVIEW_BRANCH` | `gh-pages` | Target branch (optional; default `gh-pages`) |

The PR base path is derived from the URL's path plus `/pr-<number>/`. For
`https://nikoshell.github.io/epresso-preview` that is
`/epresso-preview/pr-123/`, and the workflow sets
`EPRESSO_BASE=/epresso-preview/pr-123/` so all root-relative URLs resolve.

### 3. Secret

Settings → Secrets and variables → Actions → **Secrets**:

| Secret | Scope | Purpose |
|--------|-------|---------|
| `DOCS_PREVIEW_TOKEN` | `contents: write` **only** on the preview repo | Push the `gh-pages` branch |

Use a fine-grained PAT scoped to the single preview repository, or a GitHub App
installation token. Do **not** grant it write access to the source repository.

## Behaviour

* **Opened / synchronize / reopened** — builds from `pull_request.head.sha`
  (the PR's actual source), publishes to `pr-<n>/`, and creates or updates one
  PR comment.
* **Additional pushes** — rebuild and update the same `pr-<n>/` directory and
  edit the existing comment (matched by the `<!-- docs-preview -->` marker).
* **Closed / merged** — removes only `pr-<n>/` and deletes that PR's comment.
  Other PRs' directories are untouched.
* **Concurrency** — `docs-preview-<n>` (build) and `docs-preview-publish-<n>`
  cancel superseded runs for the same PR; cross-PR pushes retry with rebase.

## Security model

* The build workflow runs untrusted PR code with `contents: read` and no
  secrets.
* The publish workflow never checks out or runs PR code; it only downloads the
  static artifact and copies it into the preview repo.
* The claimed PR number from the artifact is validated against the trusted
  `workflow_run.head_sha` via the API, so a tampered artifact cannot target
  another PR's directory.
* Symlinks and nested `.git` directories are stripped from the artifact before
  publishing.

### Known limitations

* `workflow_run` only triggers for workflows that exist on the **default
  branch**, so previews activate after this lands on `main`.
* If the preview repo's Pages URL shares an origin with production
  (`<owner>.github.io`), a preview could run same-origin JavaScript. Prefer a
  **custom domain** for `DOCS_PREVIEW_URL` to isolate preview and production
  origins.
* The preview comment uses the issues API; `issues: write` is granted only in
  the trusted publish workflow.

## Development docs (`dev/`)

`epresso-dev` has no Pages site of its own, so `docs-dev.yml` publishes its
`main` docs to the preview repository under `dev/`:

```
https://<preview-host>/dev/      ← epresso-dev main
https://<preview-host>/pr-123/   ← pull request #123
```

It runs directly on `push` to `main` (trusted code, so no build/publish split),
and is skipped in the production repository (see the guard in `docs-dev.yml`;
override the repo name with the `DEV_REPO` variable if needed).

The production `deploy-docs.yml` is likewise guarded to run only in the
production repository (`PRODUCTION_REPO` variable, default `nikoshell/epresso`),
so pushes to `epresso-dev` no longer trigger a failing Pages deploy there.
