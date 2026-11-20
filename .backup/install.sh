#!/usr/bin/env bash
# Install the daily backup timer for the current user (Linux, systemd).
set -euo pipefail
script="$(dirname "$(readlink -f "$0")")/backup.sh"
unit_dir="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
mkdir -p "$unit_dir"
cat > "$unit_dir/agents-skills-backup.service" <<EOF
[Unit]
Description=Back up ~/.claude/skills to GitHub

[Service]
Type=oneshot
ExecStart=$script
EOF
cat > "$unit_dir/agents-skills-backup.timer" <<EOF
[Unit]
Description=Daily backup of ~/.claude/skills

[Timer]
OnCalendar=daily
Persistent=true
RandomizedDelaySec=900

[Install]
WantedBy=timers.target
EOF
systemctl --user daemon-reload
systemctl --user enable --now agents-skills-backup.timer
echo "Timer installed. Check with: systemctl --user list-timers agents-skills-backup.timer"
