sudo tee /etc/systemd/system/irrigator.service > /dev/null << EOF

[Unit]
Description=Smart irrigator (I know I have spelled it wrong...)
After=network-online.target
Wants=network-online.target

[Service]
Environment=PYTHONUNBUFFERED=1
ExecStartPre=/usr/bin/pip install -r /home/van/Documents/smart-irrigator/smart-irrigator/requirements.txt --break-system-packages
ExecStart=/usr/bin/python3 /home/van/Documents/smart-irrigator/smart-irrigator/main.py
EnvironmentFile=/home/van/Documents/smart-irrigator/smart-irrigator/.env
User=van
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable irrigator
sudo systemctl start irrigator