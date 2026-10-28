# dsh-romeo

[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (dsh), DeepSeek's coding agent, on your computer, with DeepSeek-V4.1-Flash-1017 running on the GPUs of the [ROMEO](https://romeo.univ-reims.fr/) cluster: one command starts the model, opens the tunnel and opens dsh. The same model serves any other client: opencode, Codex, Claude Code, Aider, your editor.

![dsh-romeo --launch starts DeepSeek-V4.1-Flash on ROMEO and opens the dsh Web UI, where an agent fixes a failing test; then the Trajectory tab of that session](img/dsh-romeo.gif)

## Install

On your computer (macOS or Linux), once `ssh romeo` logs you into ROMEO without a password:

```bash
git clone https://github.com/wolf75222/dsh-romeo.git ~/dsh-romeo && ~/dsh-romeo/install.sh
```

Then run `dsh-romeo --launch`. To update: `cd ~/dsh-romeo && git pull && ./install.sh`.

## Use

| Command | |
|---|---|
| `dsh-romeo --launch` | starts the model on ROMEO (2 nodes, 8 GH200), waits until it answers, opens the dsh Web UI |
| `dsh-romeo` | opens the Web UI while the model job runs |
| `dsh-romeo --run opencode` | any other client: `codex`, `claude`, `aider`, `python3 my_agent.py`... |
| `dsh-romeo --serve` | only the model and the tunnel, for an editor or any OpenAI-compatible tool |
| `dsh-romeo --status` | the gateway, the model jobs, the tunnel |
| `dsh-romeo --stop` | stops the model job: it uses your project's GPU hours while it runs |

## Docs

[Usage](docs/usage.md) · [Other clients](docs/clients.md) · [Tuning](docs/tuning.md) · [How it works](docs/how-it-works.md) · [Troubleshooting](docs/troubleshooting.md) · [Changes](docs/changes.md) · [Development](docs/development.md)
