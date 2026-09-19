#!/usr/bin/env bash
set -euo pipefail

# Ubuntu 24.04's documented application-specific userns allowance lets Codex
# build its normal inner sandbox. Do not disable the host-wide AppArmor policy.
# The allowed executable and its resources are root-owned, not user-replaceable.
version=$("$HOME/.local/bin/codex" --version | awk '{print $2}')
[[ "$version" =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || { echo 'Unexpected Codex version'; exit 1; }
package="$HOME/.codex/packages/standalone/releases/${version}-x86_64-unknown-linux-musl"
destination="/opt/chrna-codex/$version"
test -x "$package/bin/codex"
test "$(uname -m)" = x86_64
command -v apparmor_parser >/dev/null

sudo -n mkdir -p "$destination"
sudo -n cp -a "$package/." "$destination/"
sudo -n chown -R root:root "$destination"
sudo -n chmod -R go-w "$destination"
sudo -n chmod -R a+rX "$destination"

profile=$(mktemp)
cat > "$profile" <<EOF
abi <abi/4.0>,
include <tunables/global>
profile chrna-codex "$destination/bin/codex" flags=(unconfined) {
  userns,
}
EOF
sudo -n apparmor_parser --skip-kernel-load "$profile"
sudo -n install -m 0644 "$profile" /etc/apparmor.d/chrna-codex
sudo -n apparmor_parser -r /etc/apparmor.d/chrna-codex
rm -f "$profile"
ln -sfn "$destination/bin/codex" "$HOME/.local/bin/codex"
"$HOME/.local/bin/codex" --version
printf 'Host namespace restriction remains: '
cat /proc/sys/kernel/apparmor_restrict_unprivileged_userns
