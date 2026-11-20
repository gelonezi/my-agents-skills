Weekly review of my Claude Code skills backup in https://github.com/<you>/<your-repo>.
Standing rule for this repository: review each new or changed skill with /skill-creator:skill-creator
(if that skill isn't available, apply its guidelines: a clear, trigger-focused description in the frontmatter,
a concise SKILL.md, scripts in scripts/, no secrets), improve it, and push directly to main. No pull request.

The repository is a clone of ~/.claude/skills on my machine; a local timer commits there and pushes with
messages starting "Automatic backup". Each skill is a folder at the repository root, which is the layout
~/.claude/skills needs. Keep that layout.

Not skills, never review or edit them: .plugins/ (a verbatim copy of ~/.claude/plugins/installed_plugins.json,
overwritten by the timer), .backup/ (the backup scripts) and .gitignore.

Steps:
1. Check out main and pull. List commits on origin/main from the last 8 days whose message starts with
   "Automatic backup", and the skill folders they added or changed (ignore the paths listed above).
   Ignore commits made by review runs (messages starting "Review:").
2. If no skill folders changed, finish with a one-line summary saying so, and give the date of the most recent
   "Automatic backup" commit (if it is older than 30 days, say the local timer may have stopped). If
   .plugins/installed_plugins.json changed, say in one line which plugins were added, removed or updated.
3. For each changed skill, review and improve it as above. Keep changes conservative: never change what the
   skill does, only how clearly and reliably it is written. Update the skills table in README.md for new skills
   or changed descriptions.
4. Before committing, make sure no credential-looking strings are added (ghp_, github_pat_, sk-, AKIA,
   private keys).
5. Commit with a message starting "Review: <skill names>" and push to main. If the push is rejected,
   pull --rebase and retry; never force-push.
6. Finish with a short summary: which skills you reviewed and what you changed in each (one line each).
