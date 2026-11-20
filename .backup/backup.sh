#!/usr/bin/env bash
# Commit and push any change in ~/.claude/skills. Run by the systemd user timer.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."
git add -A
if git diff --cached --quiet; then
  echo "No changes."
else
  # This repository is public: refuse to publish anything that looks like a credential.
  if git diff --cached -U0 | grep -E '^\+' | grep -Eq 'gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9_-]{30,}|AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----'; then
    echo "Possible secret in the changes; nothing committed. Review with: git -C $PWD diff --cached" >&2
    git reset -q
    exit 1
  fi
  git commit -q -m "Automatic backup $(date '+%Y-%m-%d %H:%M')"
  echo "Committed."
fi
# Push whenever the remote is behind (also retries a push that failed while offline).
if git remote get-url origin >/dev/null 2>&1; then
  git push -q origin main && echo "Pushed."
fi
