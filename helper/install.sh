#!/bin/bash
# Installs (or updates) the Hutch drawers helper for this Mac user and starts it at login.
set -e
BASE="$HOME/Library/Application Support/HutchHelper"
REPO="$BASE/repo"
mkdir -p "$BASE"
if [ -d "$REPO/.git" ]; then git -C "$REPO" pull --ff-only -q; else git clone -q https://github.com/Blank428/hutch-drawers.git "$REPO"; fi
PL="$HOME/Library/LaunchAgents/com.hutchdrawers.helper.plist"
mkdir -p "$HOME/Library/LaunchAgents"
cat > "$PL" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key><string>com.hutchdrawers.helper</string>
  <key>ProgramArguments</key>
  <array><string>/usr/bin/python3</string><string>$REPO/helper/helper.py</string></array>
  <key>EnvironmentVariables</key>
  <dict><key>PATH</key><string>/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string></dict>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
  <key>StandardOutPath</key><string>$BASE/helper.log</string>
  <key>StandardErrorPath</key><string>$BASE/helper.log</string>
</dict>
</plist>
PLIST
launchctl bootout "gui/$(id -u)" "$PL" 2>/dev/null || true
launchctl bootstrap "gui/$(id -u)" "$PL"
echo "Hutch helper installed at $REPO/helper"
