#!/usr/bin/env bash
# release-public.sh — publish a CLEAN public snapshot from the private repo.
#
#   private (epresso-dev)  →  release process  →  public (epresso)
#
# The public repo keeps only released snapshots + tags. Each release is ONE
# squashed commit whose tree equals the source ref's tree, tagged v<version>.
# Private per-commit history never reaches the public remote.
#
# Usage:
#   release-public.sh <src-ref> <version> [options]
#
#   src-ref   branch/commit/tag in THIS repo whose tree becomes the release.
#             (Only publish from a branch whose tree contains NO private-only
#             content — the snapshot is exactly this tree.)
#   version   e.g. 1.0.0  (tag becomes v1.0.0)
#
# Options:
#   -r, --root    First/migration release: make a ROOT commit (no public parent)
#                 so public history starts clean here. Requires --push --force.
#   -p, --push    Publish (default is dry-run).
#   -f, --force   Allow replacing public/main (use --force-with-lease).
#   -c, --check   Preflight: run the production docs build on the snapshot first.
set -euo pipefail

SRC_REF="${1:?usage: release-public.sh <src-ref> <version> [-r] [-c] [-p] [-f]}"
VERSION="${2:?usage: release-public.sh <src-ref> <version> [-r] [-c] [-p] [-f]}"
shift 2

PUSH=0; FORCE=0; ROOT=0; CHECK=0
for a in "$@"; do
  case "$a" in
    -p|--push) PUSH=1 ;;
    -f|--force) FORCE=1 ;;
    -r|--root) ROOT=1 ;;
    -c|--check) CHECK=1 ;;
    *) echo "unknown option: $a" >&2; exit 2 ;;
  esac
done

git rev-parse --verify "${SRC_REF}^{commit}" >/dev/null 2>&1 || { echo "bad src-ref: $SRC_REF" >&2; exit 2; }
SRC_TREE=$(git rev-parse "${SRC_REF}^{tree}")

if [ "$CHECK" = 1 ]; then
  echo "== preflight: production docs build =="
  uv run --project . --extra dev epresso build themes/docs
fi

echo "== resolving public remote =="
git fetch public >/dev/null 2>&1 || true
PUB_BASE=""
if [ "$ROOT" = 0 ]; then
  PUB_BASE=$(git rev-parse --verify public/main^{commit} 2>/dev/null || echo "")
fi

MSG="Release v$VERSION"
if [ -n "$PUB_BASE" ]; then
  NEW=$(git commit-tree "$SRC_TREE" -p "$PUB_BASE" -m "$MSG")
  echo "snapshot commit: $NEW  (parent = public/main $PUB_BASE)"
else
  NEW=$(git commit-tree "$SRC_TREE" -m "$MSG")
  echo "snapshot commit: $NEW  (root — no public parent)"
fi

git tag -a "v$VERSION" "$NEW" -m "$MSG"
echo "tag: v$VERSION"
git show --stat --oneline --no-renames "$NEW" | head -20 || true  # SIGPIPE must not abort the push

if [ "$PUSH" = 1 ]; then
  # Destination is explicit (refs/heads/main) so pushing a raw commit works even
  # when the public repo is empty (no upstream to lease against yet).
  if [ "$FORCE" = 1 ]; then
    git push --force public "$NEW":refs/heads/main
  else
    git push public "$NEW":refs/heads/main   # fast-forward; fails if public diverged
  fi
  git push public "v$VERSION"
  echo "PUSHED public/main -> $NEW and tag v$VERSION"
else
  echo "DRY-RUN. Re-run with --push (add --force when replacing existing public history)."
fi
