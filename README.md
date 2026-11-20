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
