#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
project_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$project_root"

# The Ubuntu controller uses an application-specific AppArmor allowance for
# a root-owned Codex binary, so the normal bubblewrap sandbox can run.
# Network access is required for public scientific tools and Brev management.
runtime_roots=$(python3 -c 'import json; from pathlib import Path; print(json.dumps([str(Path.home()/".brev"), str(Path.home()/".ssh")]))')
exec codex -c 'sandbox_mode="workspace-write"' \
  -c "sandbox_workspace_write.writable_roots=$runtime_roots" \
  -c sandbox_workspace_write.network_access=true "$@"
