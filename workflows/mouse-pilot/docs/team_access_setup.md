# Shared Codex session

The agreed interface is one tmux session on the existing CPU VM. The custom server and operator-token approach has been withdrawn.

## Join

On each teammate's laptop, using their existing Brev access:

```bash
brev shell chrna-controller
```

Then on the VM:

```bash
tmux attach -t chrna-codex
```

Everyone sees and controls the same Codex session. Take turns typing. To observe without sending keystrokes, use `tmux attach -r -t chrna-codex`.

Detach without stopping Codex: press **Ctrl-b**, release, then **d**. Closing SSH also leaves the session running. A VM reboot stops tmux; the saved Codex task can be resumed afterward.

## Current setup

- Brev organization: London-AI-Brev.
- VM: chrna-controller.
- Shared terminal: chrna-codex, owned by the existing `ubuntu` SSH user.
- Saved Codex task: 01a0ba08-d9ef-7a23-9451-e72327b577d8.
- Shared workspace: /home/ubuntu/workspace/chrna. /srv/chrna-team/project is a compatibility symlink to the same files.
- Uses the team API login already configured, kept in its existing private Linux account; teammates do not need new application logins or copies of the API key.
- The root-owned Codex installation is available as /usr/local/bin/codex.
- Custom WebSocket service disabled and removed; operator transport tokens and signing key deleted. No credential packages were exported.
- No SSH grants were changed. Teammates need existing Brev access to the VM as `ubuntu` to attach to this terminal.
- For live scientific processing and GPU status, read START_HERE.md and the latest run records; this setup document does not track job status.

The previous design's setup and token-export prompts are obsolete; do not use them.

## Canonical launcher

The shared Codex task launches and resumes with `/home/ubuntu/workspace/chrna` as its working root.
Its launcher is `scripts/shared_codex.sh` in that project. It resumes the existing task and retains the runner account's authentication and installed plugins.

Join the existing `chrna-codex` tmux session for normal use. Do not run a second copy of the launcher while the shared task is active.
The old `/srv/chrna-team/project` link exists only for previously installed tools and detached jobs with embedded paths; it is not a second project.
