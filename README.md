# my-agents-skills

My personal skills for Claude Code, backed up automatically from `~/.claude/skills/`.

## Skills

| Skill | What it does |
|---|---|
| [steam-wallpapers-downloader](steam-wallpapers-downloader/SKILL.md) | Downloads a Steam game's trading card wallpapers, profile backgrounds, badges and emoticons from steamcardexchange.net, each file named after its card. |

## Restore on a new machine

```bash
git clone https://github.com/gelonezi/my-agents-skills.git ~/.claude/skills
~/.claude/skills/.backup/install.sh
```

If `~/.claude/skills` already exists, move its contents aside first, clone, then move them back.

## How the backup works

`.backup/install.sh` installs a systemd user timer that runs `.backup/backup.sh` once a day. The script
commits any change, pulls anything new from GitHub, and pushes. Because this repository is public, it refuses to
commit changes that look like credentials. Skills synced by the Claude desktop app (`synced/`) are ignored.

The script also copies `~/.claude/plugins/installed_plugins.json` (the list of installed plugins) into
`.plugins/`, so there is a record of which plugins and versions were installed. It is only a record:
to reinstall, add the plugins again with `/plugin`.

Every Monday a scheduled Claude task reviews the skills the timer backed up that week (with the skill-creator
guidelines), pushes any improvements here, and the next local run pulls them back into `~/.claude/skills`.

## Use this to back up your own skills

Any Claude Code user can copy this setup. You end up with a GitHub repository that holds your skills and your
plugin list, updated every day from your machine and reviewed by Claude every week. The local timer needs Linux
with systemd (on macOS or Windows, run `.backup/backup.sh` from launchd, cron or Task Scheduler instead).

**1. Create your repository.** Create an empty repository on GitHub (private if your skills mention anything
personal). Don't fork this one: you'd inherit my skills.

**2. Turn `~/.claude/skills` into a clone of it**, keeping the skills you already have:

```bash
mv ~/.claude/skills ~/.claude/skills.old        # skip if you have no skills yet
git clone https://github.com/<you>/<your-repo>.git ~/.claude/skills
cp -r ~/.claude/skills.old/. ~/.claude/skills/  # skip if you have no skills yet
```

**3. Copy the backup scripts** from this repository into yours:

```bash
cd ~/.claude/skills
mkdir -p .backup
for f in backup.sh install.sh weekly-review-prompt.md; do
  curl -fsSL "https://raw.githubusercontent.com/gelonezi/my-agents-skills/main/.backup/$f" -o ".backup/$f"
done
curl -fsSL https://raw.githubusercontent.com/gelonezi/my-agents-skills/main/.gitignore -o .gitignore
chmod +x .backup/*.sh
```

Read both scripts before running them: they commit and push everything in `~/.claude/skills`.

**4. Make sure `git push` works without a prompt** from that folder (an SSH remote or a credential helper),
because the timer runs unattended. Test it with `git push origin main`.

**5. Run the first backup and install the daily timer:**

```bash
~/.claude/skills/.backup/backup.sh     # first commit: your skills and ~/.claude/plugins/installed_plugins.json
~/.claude/skills/.backup/install.sh    # runs backup.sh every day from now on
systemctl --user list-timers agents-skills-backup.timer   # check the next run
```

If you log out often, run `loginctl enable-linger $USER` so the timer also runs when you're not logged in.

**6. (Optional) Add the weekly review.** On [claude.ai/code](https://claude.ai/code), connect GitHub and give
Claude access to your repository. Then create a scheduled task that runs weekly (for example Mondays at 9 AM)
in an environment with that repository, using the text of
[`.backup/weekly-review-prompt.md`](.backup/weekly-review-prompt.md) as its prompt, with your repository's URL
filled in. Each week Claude reviews the skills that changed, pushes improvements to `main`, and your next daily
backup pulls them into `~/.claude/skills`.

**Restoring on a new machine** is steps 2, 4 and 5 again. The plugin list in `.plugins/` shows what to
reinstall with `/plugin`.
