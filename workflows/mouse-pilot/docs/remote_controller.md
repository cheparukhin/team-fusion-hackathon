# Brev CPU controller

The first controller was provisioned as `chrna-controller`: x86_64, 4 vCPUs, 16 GiB RAM and a 50 GiB disk, with no GPU. The observed compute quote was USD 0.11904/hour. Storage was quoted separately at USD 0.12264/GiB/month. These are a dated setup record, not a promise of current pricing. Refresh quotes before any additional provisioning.

The project is at `/home/ubuntu/workspace/chimeric-rna-prioritization`. Codex CLI 0.155.1, Brev CLI 0.6.335, uv and the benchmark environment are installed. The data build, fourteen tests and development baseline reproduced on the CPU controller. No GPU job has run.

## Authentication

Authentication was verified for both Codex and Brev on the initial controller. For another instance, complete `codex login --device-auth` using the appropriate research/hackathon account, then use `brev login` and select the team's shared organization. Do not put credentials in the repo or copy them into public artifacts.

Verify `codex login status` and `brev org ls` before delegated work. Installation by itself does not establish a logged-in Codex agent or a running background task.

## Work on the controller

```bash
brev shell chrna-controller
cd ~/workspace/chimeric-rna-prioritization
source .venv/bin/activate
chrna build
pytest -q
chrna benchmark
bash scripts/controller_codex.sh
```

Codex should read AGENTS.md and follow the evidence and spending constraints. Keep the held-out partition reserved. Use the recorded development baselines as comparisons, not as neural-model results.

Ubuntu's default application policy initially blocked the namespace operations used by Codex's normal bubblewrap sandbox. `scripts/install_codex_apparmor.sh` installs the Codex package under a root-owned `/opt/chrna-codex/<version>` path and adds the documented application-specific `userns` permission for that exact executable. The global AppArmor namespace restriction stays enabled. This follows [Ubuntu's application-profile guidance](https://discourse.ubuntu.com/t/ubuntu-24-04-lts-noble-numbat-release-notes/39890). Reapply the setup after upgrading the standalone Codex package.

The launcher retains the normal workspace filesystem sandbox. It enables command network access and grants writes to this controller's Brev and SSH configuration directories for credential refresh and instance connections. It does not disable the sandbox or approval system. Read-only sandbox write denial and a Brev inventory query inside the normal network-enabled sandbox have been verified. A temporary read-only Landlock compatibility run was used for the recorded code review; the final launcher does not require that deprecated backend.

## GPU jobs

No GPU is necessary for the current baseline. When a concrete inference job is ready:

1. Read the live Brev GPU quote and the inventory of running project resources.
2. Include compute, known disk costs and other known charges in the hourly estimate.
3. Check the combined cost using `scripts/check_budget.py`; unknown prices must block launch.
4. Launch only the selected instance type, preferably far below the USD 100/hour ceiling.
5. Use one worker and a bounded job duration. Save results, then stop that GPU on success or failure.

The local policy is not a Brev billing cap. Do not modify unrelated team instances. The CPU remains available as a controller until explicitly stopped; it continues to incur its small charge.

Stop this project's CPU when no longer needed with `brev stop chrna-controller` after saving work. Stopped storage may still incur charges.
