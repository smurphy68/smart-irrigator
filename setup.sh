#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

sudo tee /etc/systemd/system/git-sync.service > /dev/null << EOF
[Unit]
Description=Git repo polling sync
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=$SCRIPT_DIR/git-sync.sh
User=$USER
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

chmod +x "$SCRIPT_DIR/git-sync.sh"
sudo systemctl daemon-reload
sudo systemctl enable git-sync
sudo systemctl start git-sync

echo "Done. Run 'sudo systemctl status git-sync' to verify."