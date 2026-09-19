# Shared science plugins — 19 September 2026

Installed for Linux account `chrna-runner`, Codex home `/var/lib/chrna-team/.codex` on `chrna-controller`.

| Plugin | Version | Source |
|---|---|---|
| NVIDIA BioNeMo Agent Toolkit | 0.1.0 | Official NVIDIA repository, pinned to `0e67a612e4045f007e38fa77adc8f3ebfc5616b6` |
| Rosalind Workbench | 0.2.5-research-preview | Existing local desktop bundle, installed through shared account's personal marketplace |
| Life Sciences Databases | 0.1.5 | Existing local desktop bundle, personal marketplace |
| Life Sciences Literature | 0.1.5 | Existing local desktop bundle, personal marketplace |
| Life Science Research | 1.0.3 (cache revision 1dc19589) | API-key curated marketplace |

NVIDIA source: https://github.com/NVIDIA-BioNeMo/bionemo-agent-toolkit

Validation: fresh Codex App Server `skills/list` loaded 134 skills without errors, including 31 BioNeMo, 50 Life Science Research, 44 Life Sciences Databases, and 3 Life Sciences Literature skills, plus 6 other skills. Rosalind's MCP server initializes and exposes `rosalind.open` and `rosalind.settings`; calling `rosalind.open` succeeded without an error. Raw verification is stored at `/var/lib/chrna-team/plugin-verification.json`.

Installed Ubuntu Node.js runtime to support Rosalind's bundled MCP server. No personal authentication files were copied. The scientific workflow was not changed.

Limitations:
- Rosalind Workbench is a graphical MCP app. A terminal session is not a verified UI host, and installing the bundle does not grant GPT-Rosalind model access.
- Neither NVIDIA_API_KEY nor NGC_API_KEY was present in the running shared agent's environment. Hosted NVIDIA inference is not verified. Local GPU execution has its own runtime and model prerequisites.
- The existing shared agent was actively running scientific work during installation. Its process was not terminated or restarted. Newly installed MCP tools may require a safe session restart; fresh-process skill loading was verified separately.
- Local-bundle plugins do not receive curated marketplace updates automatically.
