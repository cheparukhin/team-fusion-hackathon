#!/usr/bin/env bash
set -euo pipefail
umask 077

project_dir="${1:-$HOME/workspace/chimeric-rna-prioritization}"
export PATH="$HOME/.local/bin:$PATH"
mkdir -p "$HOME/.local/bin" "$HOME/workspace"

if ! command -v codex >/dev/null 2>&1; then
  installer=$(mktemp)
  curl -fsSL https://chatgpt.com/codex/install.sh -o "$installer"
  sh "$installer"
  rm -f "$installer"
fi

if ! command -v brev >/dev/null 2>&1; then
  temp_dir=$(mktemp -d)
  curl -fsSL https://github.com/brevdev/brev-cli/releases/download/v0.6.335/brev-cli_0.6.335_linux_amd64.tar.gz -o "$temp_dir/brev.tar.gz"
  printf '%s  %s\n' '89d778e6f1e5e52495f3e0f10393f1666a1b16d180001b13faec6f906955e6f8' "$temp_dir/brev.tar.gz" | sha256sum -c -
  tar -xzf "$temp_dir/brev.tar.gz" -C "$temp_dir"
  install -m 0755 "$temp_dir/brev" "$HOME/.local/bin/brev"
  rm -rf "$temp_dir"
fi

if ! command -v uv >/dev/null 2>&1; then
  installer=$(mktemp)
  curl -LsSf https://astral.sh/uv/install.sh -o "$installer"
  sh "$installer"
  rm -f "$installer"
fi

if [ ! -d "$project_dir/.git" ]; then
  git clone https://github.com/cheparukhin/chimeric-rna-prioritization.git "$project_dir"
fi
cd "$project_dir"
if [ "$(cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns 2>/dev/null || true)" = 1 ]; then
  bash scripts/install_codex_apparmor.sh
fi
if [ ! -x .venv/bin/python ]; then
  uv venv --python 3.12 .venv
fi
uv pip install --python .venv/bin/python -r requirements-lock.txt
uv pip install --python .venv/bin/python -e . --no-deps
.venv/bin/chrna build
.venv/bin/pytest -q
.venv/bin/chrna benchmark
codex --version
brev --version
printf 'Project ready at %s\n' "$project_dir"
printf 'Codex and Brev authentication must be established separately. No credentials are bundled.\n'
