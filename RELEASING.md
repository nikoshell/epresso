# Release flow: private → public

Two repositories back epresso:

| Repo | Remote name | Purpose |
|------|-------------|---------|
| `nikoshell/epresso-dev` | `origin` | **Private** — full development history, feature branches, PRs, issues, CI, WIP, sensitive/internal notes. Normal Git workflow. |
| `nikoshell/epresso` | `public` | **Public** — only released, squashed snapshots + tags (`v1.0.0`, …). Clean history, public docs. |

```
epresso-dev (private)
   ↓ development / PRs / commits / CI
   ↓ release process
   ↓ squash → clean snapshot + tag vX.Y.Z
epresso (public)
```

## Remotes

```bash
git remote -v
# origin   -> git@github.com:nikoshell/epresso-dev.git   (private)
# public   -> git@github.com:nikoshell/epresso.git       (public)
```

`origin` stays the private remote for day-to-day work. `public` is only touched
by the release script.

## Doing a release

From the private repo, run the release script. It builds ONE clean squashed
commit (tree == the source ref's tree) on the public history and tags it.

```bash
# Dry-run first (no network writes):
./scripts/release-public.sh main 1.0.0 -c     # -c runs the production docs build

# First / migration release — start public history clean here:
./scripts/release-public.sh main 1.0.0 --root --push --force

# Later releases append a single snapshot on top of the public history:
./scripts/release-public.sh main 1.1.0 --push
```

What the script does:

1. Resolves the source ref's **tree** (the whole snapshot).
2. (Optional `-c`) runs `epresso build themes/docs` as a production preflight.
3. Creates **one** commit whose parent is the previous public release (or a root
   commit with `--root`), so public history is `v1.0.0 → v1.1.0 → …` — private
   per-commit history never ships.
4. Tags `v<version>` and (with `--push`) publishes `public/main` + the tag.

## Ground rules

- **Publish only publishable trees.** The snapshot is exactly the `src-ref`
  tree — anything committed there (internal docs, secrets, WIP) becomes public.
  Keep private-only content on `dev`/feature branches or out of the release
  branch's tree.
- **Public never receives internal PRs/issues** — those live in the private repo.
- **Tags are the contract.** `v1.0.0`, `v1.1.0` on the public repo point at clean
  snapshots only.
- Migration note: the existing `public/main` already contains unreleased commit
  history. The first release replaces it with a single clean snapshot
  (`--root --force`). Do that only once, deliberately.

## Optional: public deploy

If the public repo deploys the docs (GitHub Pages on `public/main`), then every
release pushed here rebuilds and ships the public site automatically.
