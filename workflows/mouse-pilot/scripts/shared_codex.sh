#!/bin/sh
# Resume the existing shared task; authentication remains in the runner account.
set -eu
project=/home/ubuntu/workspace/chrna
if [ "$(id -un)" != chrna-runner ]; then
    exec sudo -u chrna-runner -H "$project/scripts/shared_codex.sh" "$@"
fi
cd "$project"
exec /usr/local/bin/codex resume 01a0ba08-d9ef-7a23-9451-e72327b577d8 \
    --cd "$project" -m gpt-6-astra -c model_reasoning_effort=medium \
    --sandbox danger-full-access --ask-for-approval never "$@"
