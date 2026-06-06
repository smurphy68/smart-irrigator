# setup.sh
#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Write the sync script
cat > /home/pi/scripts/git-sync.sh << EOF
#!/bin/bash
REPO="$SCRIPT_DIR"
BRANCH="main"
INTERVAL=300

while true; do
    cd "\$REPO"
    git fetch origin
    LOCAL=\$(git rev-parse HEAD)
    REMOTE=\$(git rev-parse origin/\$BRANCH)
    if [ "\$LOCAL" != "\$REMOTE" ]; then
        echo "\$(date): Change detected, pulling..."
        git pull
    fi
    sleep \$INTERVAL
done
EOF

chmod +x /home/pi/scripts/git-sync.sh
mkdir -p /home/pi/scripts

# Write the systemd service
sudo tee /etc/systemd/system/git-sync.service > /dev/null << EOF
[Unit]
Description=Git repo polling sync
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/home/pi/scripts/git-sync.sh
User=pi
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable git-sync
sudo systemctl start git-sync

echo "Done. git-sync is running and will start on every boot."