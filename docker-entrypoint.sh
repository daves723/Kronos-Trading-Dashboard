#!/bin/bash
set -e

# Download Kronos weights if not present
if [ ! -d "/app/kronos_weights/models--NeoQuasar--Kronos-small" ]; then
    echo "Downloading Kronos model weights..."
    python -c "
from huggingface_hub import snapshot_download
snapshot_download('NeoQuasar/Kronos-small', local_dir='/app/kronos_weights/models--NeoQuasar--Kronos-small')
snapshot_download('NeoQuasar/Kronos-Tokenizer-base', local_dir='/app/kronos_weights/models--NeoQuasar--Kronos-Tokenizer-base')
"
fi

echo "Starting Kronos Dashboard on http://localhost:3456"
exec python server.py
