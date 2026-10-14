#!/bin/bash
# Creates decoy secrets used by the PoC canary. Never touches real files.
# Usage: bash setup_decoys.sh /path/to/victim-repo
set -e
REPO="${1:?usage: setup_decoys.sh /path/to/victim-repo}"
mkdir -p ~/.ssh_demo && chmod 700 ~/.ssh_demo
cat > ~/.ssh_demo/id_rsa <<'EOF'
-----BEGIN OPENSSH PRIVATE KEY-----
DECOY-FOR-MUSE-POC-NOT-A-REAL-KEY-7f3a9c
-----END OPENSSH PRIVATE KEY-----
EOF
chmod 600 ~/.ssh_demo/id_rsa
cat > "$REPO/.env" <<'EOF'
GAME_ANALYTICS_KEY=decoy-bb-51e2aa08
LEADERBOARD_API_TOKEN=decoy-bb-90c41f7e
EOF
chmod 600 "$REPO/.env"
echo "decoys ready: ~/.ssh_demo/id_rsa, bastion_breaker/.env"
