#!/usr/bin/env bash
# Commit and push any change in ~/.claude/skills. Run by the systemd user timer.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."
# Also keep a copy of the list of installed plugins (just that file, not the plugins themselves).
plugins_list="$HOME/.claude/plugins/installed_plugins.json"
if [ -f "$plugins_list" ]; then
  mkdir -p .plugins
  cp "$plugins_list" .plugins/installed_plugins.json
fi
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
if git remote get-url origin >/dev/null 2>&1; then
  # The weekly cloud review may have pushed improvements: bring them in first, so the push is not
  # rejected and the improved skills land in ~/.claude/skills too.
  if git ls-remote --exit-code --heads origin main >/dev/null 2>&1 && ! git pull -q --rebase origin main; then
    git rebase --abort 2>/dev/null || true
    echo "Could not merge changes from GitHub; nothing pushed. Resolve with: git -C $PWD pull --rebase origin main" >&2
    exit 1
  fi
  # Push whenever the remote is behind (also retries a push that failed while offline).
  git push -q origin HEAD:main && echo "Pushed."
fi
