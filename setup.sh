#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# git-sync service
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

# irrigator service
sudo tee /etc/systemd/system/irrigator.service > /dev/null << EOF
[Unit]
Description=Smart irrigator
After=network-online.target
Wants=network-online.target

[Service]
ExecStartPre=/usr/bin/pip install -r $SCRIPT_DIR/requirements.txt --break-system-packages
ExecStart=/usr/bin/python3 $SCRIPT_DIR/main.py
EnvironmentFile=$SCRIPT_DIR/.env
User=$USER
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

chmod +x "$SCRIPT_DIR/git-sync.sh"
sudo systemctl daemon-reload
sudo systemctl enable git-sync irrigator
sudo systemctl start git-sync irrigator

echo "Done. Run 'sudo systemctl status git-sync irrigator' to verify."