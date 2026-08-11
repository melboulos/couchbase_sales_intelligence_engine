#!/bin/bash
# =====================================================
# ENVIRONMENT SETUP
# Couchbase Sales Intelligence Engine
#
# IMPORTANT: run this with `source setup.sh` (or `. setup.sh`),
# NOT `./setup.sh`. Executing it directly runs it in a subshell -
# the venv gets created and activated inside that subshell only,
# then vanishes the instant the script exits, leaving your actual
# terminal completely unaffected. Sourcing runs it in your CURRENT
# shell, so the activation actually sticks around afterward.
# =====================================================

if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    echo "ERROR: this script was executed, not sourced."
    echo "Run it as:  source setup.sh"
    echo "Not as:     ./setup.sh"
    exit 1
fi

if [ ! -f "venv/bin/activate" ]; then
    echo "No venv found - creating one..."
    python3 -m venv venv
else
    echo "Existing venv found - reusing it."
fi

source venv/bin/activate
echo "venv activated: $(which python3)"

if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install -q -r requirements.txt
    echo "Dependencies installed."
else
    echo "WARNING: no requirements.txt found in this directory - skipping install."
fi

echo ""
echo "--- Environment checks ---"

if [ -n "$SERPER_API_KEY" ]; then
    echo "SERPER_API_KEY: set (from shell environment)"
elif [ -f ".env" ]; then
    echo "SERPER_API_KEY: not in shell env, but a .env file exists -"
    echo "  scripts using load_dotenv() will pick it up automatically."
else
    echo "SERPER_API_KEY: NOT SET, and no .env file found"
    echo "  Set it via a .env file (recommended, persists across sessions):"
    echo '    echo '"'"'SERPER_API_KEY="your-key-here"'"'"' > .env'
    echo "  Or export it manually (only lasts this terminal session):"
    echo '    export SERPER_API_KEY="your-key-here"'
fi

if command -v aws >/dev/null 2>&1; then
    echo "AWS CLI: found"
else
    echo "AWS CLI: not found on PATH (only matters if you invoke Bedrock outside boto3)"
fi

echo ""
echo "Setup complete. venv is active in this shell."
