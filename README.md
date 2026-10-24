# dsh-romeo

[DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness) (dsh), DeepSeek's coding agent, on your computer, with its model, DeepSeek-V4.1-Flash, running on the GPUs of the [ROMEO](https://romeo.univ-reims.fr/) cluster. One command starts the model, opens the tunnel and opens dsh.

![dsh-romeo launches DeepSeek-V4.1-Flash on ROMEO, then dsh fixes a failing test on the laptop](img/dsh-romeo.gif)

## Install

On your computer (macOS or Linux), once `ssh romeo` logs you into ROMEO without a password:

```bash
git clone https://github.com/wolf75222/dsh-romeo.git ~/dsh-romeo && ~/dsh-romeo/install.sh
```

It installs dsh if it is missing (`npm install -g @deepseek-ai/dsh`, Node.js 20 or later), asks which ROMEO project pays for the model jobs, links `dsh-romeo` in `~/.local/bin` and copies the model's fiche to `~/.romeollmtool/configs` on ROMEO. To update: `cd ~/dsh-romeo && git pull && ./install.sh`.

No `romeo` alias yet? Add it to `~/.ssh/config`:

```
Host romeo
    HostName romeo1.univ-reims.fr
    User <your ROMEO login>
    IdentityFile ~/.ssh/<your key registered on ROMEO>
```

## Use

| Command | |
|---|---|
| `dsh-romeo --launch` | starts the model (one job, 2 nodes, 8 GH200), waits until it answers (8 to 13 min in our tests), opens the dsh Web UI |
| `dsh-romeo` | opens the Web UI while the job runs |
| `dsh-romeo headless "run the tests and fix them"` | one task, the answer printed on stdout: for scripts |
| `dsh-romeo web --port 3000` | any dsh profile and argument pass through |
| `dsh-romeo --launch 3` | three jobs: the gateway spreads the agents over them |
| `dsh-romeo --status` | the gateway, the model jobs, the tunnel |
| `dsh-romeo --stop` | stops the model jobs and closes the tunnel |

The agents work on your computer, in the folder where you start dsh: only the model runs on ROMEO.

## What it does

- **The model.** Launches DeepSeek-V4.1-Flash with ROMEO's own tool, `romeollmtool`, from a fiche tuned for agents: 8 GPUs on 2 nodes (tensor parallelism), the full context of 1M tokens, 256K tokens of output and DSpark speculative decoding. On ROMEO it serves about 500 agents at once at 30 tokens/s each with 7 jobs. ROMEO's validated fiche also works: one node, 262K tokens of context, longer to load (`DSH_ROMEO_FICHE=deepseek-v4.1-flash-vllm`).
- **The gateway.** Keeps `romeollmtool`'s gateway running on the login node: one URL and one key for all your model jobs, requests spread over them.
- **Waits for the model** with a real one-token request, and shows where the job is meanwhile: in the queue and why, or loading.
- **The tunnel.** One SSH connection carries every command and the tunnel `127.0.0.1:11318` to the gateway, reused from one run to the next and reopened after your computer slept.
- **dsh.** Runs dsh with an overlay (`dsh --patch`) that adds the `romeo` provider and makes DeepSeek-V4.1-Flash the default model, with maximum reasoning. Your own dsh profiles are not modified. The gateway's key goes to dsh through its environment and is never written to disk.
- **Web search** (optional): `install.sh --search` runs [SearXNG](https://docs.searxng.org/) in Docker on `127.0.0.1:8888` and plugs it into dsh's `web_search` tool.

## Settings

`install.sh` writes them to `~/.config/dsh-romeo/config`; a variable set in the environment wins.

| Variable | Default | |
|---|---|---|
| `ROMEO_PROJECT` | asked | Slurm project code charged for the model jobs |
| `ROMEO_SSH_HOST` | `romeo` | ssh alias of a ROMEO login node |
| `DSH_ROMEO_FICHE` | `dsh-deepseek-v4.1-flash-1m` | `romeollmtool` fiche of the model |
| `DSH_ROMEO_TIME` | `08:00:00` | duration of a model job (24 h at most) |
| `DSH_ROMEO_EFFORT` | `max` | default reasoning effort: `none`, `low`, `high`, `max` |
| `DSH_ROMEO_PORT` | `11318` | local port of the tunnel |
| `DSH_ROMEO_SEARXNG_URL` | empty | SearXNG for web search, e.g. `http://127.0.0.1:8888` |

## Cost

A model job uses the GPU hours of your project for as long as it runs, even when no agent works: `dsh-romeo --stop` when you are done. It ends anyway after `DSH_ROMEO_TIME`. The gateway stops by itself 24 hours after the last `dsh-romeo`, and cancels your model jobs then.

## When something goes wrong

- **`cannot connect to 'romeo' over SSH`**: `ssh romeo hostname` must work without a password (see Install).
- **The job waits in the queue**: `dsh-romeo --status` says why (`Resources`: no free GPU nodes yet; `Priority`: other jobs first). Waiting can stop with Ctrl-C: the job stays in the queue and `dsh-romeo` picks it up later.
- **The job ends while loading**: read its log with `ssh romeo /apps/romeotools/romeollmtool/romeollmtool logs`. A node whose GPU memory is partly taken makes vLLM fail at start: `dsh-romeo --launch` again.
- **`cannot forward 127.0.0.1:11318`**: another program uses the port: set `DSH_ROMEO_PORT`.
- **dsh shows connection errors after your computer slept**: quit dsh and run `dsh-romeo` again; the tunnel is reopened and dsh keeps your sessions.

## Development

```bash
tests/run.sh                 # offline tests against a fake ROMEO (fake ssh, romeollmtool, squeue, gateway)
python3 tests/demo.py record # records a real run for the GIF (launches a model job), then:
python3 tests/demo.py render # draws img/dsh-romeo.gif
```

`tests/tui.py` (driving a program in a pseudo-terminal and drawing its screen) comes from [RSV](https://github.com/wolf75222/RSV).
