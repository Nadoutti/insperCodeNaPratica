#!/bin/bash
set -e

# Fix permissions for the app directory when using volume mounts
chown -R appuser:appuser /app 2>/dev/null || true

# Execute the command as appuser
exec gosu appuser "$@"
