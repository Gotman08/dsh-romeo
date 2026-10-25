# Changes

[README](../README.md) · [Usage](usage.md) · [Other clients](clients.md) · [Tuning](tuning.md) · [How it works](how-it-works.md) · [Troubleshooting](troubleshooting.md) · **Changes** · [Development](development.md)

## 2026-10-25

- Any client on the ROMEO model: `--run CMD` (opencode, Codex CLI, Claude Code, Aider, SDKs), `--serve`, `--env`. Each tested against a real job.
- `DSH_ROMEO_GATEWAY=fast`: the patched gateway of the A/B study, with a fallback to the standard one.
- Messages on stderr; documentation split into these pages.

## 2026-10-24

- The README's GIF: the launch in a terminal, then the dsh Web UI it opens, a chat that fixes a test and the Trajectory tab, recorded from a real run.
- First version: `install.sh`, `dsh-romeo` with `--launch`, `--status`, `--stop`, `--setup`, the tuned fiche, optional SearXNG web search, offline tests against a fake ROMEO.
