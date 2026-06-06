#!/bin/bash
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BRANCH="main"
INTERVAL=300

while true; do
    cd "$REPO"
    git fetch origin
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/$BRANCH)
    if [ "$LOCAL" != "$REMOTE" ]; then
        echo "$(date): Change detected, pulling..."
        git pull
    fi
    sleep $INTERVAL
done