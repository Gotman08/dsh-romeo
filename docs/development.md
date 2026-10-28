# Development

[README](../README.md) · [Usage](usage.md) · [Other clients](clients.md) · [Tuning](tuning.md) · [How it works](how-it-works.md) · [Troubleshooting](troubleshooting.md) · [Changes](changes.md) · **Development**

```bash
tests/run.sh                                          # offline tests against a fake ROMEO
bash tests/install.sh                                 # private npm prefix / WSL regression tests
dsh-romeo --run python3 tests/clients/openai_sdk.py   # the real endpoint through the OpenAI SDK
python tests/demo.py record                           # records a real run for the GIF (launches a model job)
python tests/demo.py render                           # draws img/dsh-romeo.gif
```

For an opt-in check against an already-running real ROMEO model, use
`dsh-romeo --run python tests/clients/live_smoke.py windows` on Windows or
`dsh-romeo --run python3 tests/clients/live_smoke.py wsl` inside WSL. This
standard-library client checks `/models`, an actual tool call with preserved
arguments, and an SSE streamed answer using the tool result. It prints a JSON
summary without the API key. It does not submit or cancel a job; requests use
the model already served by the gateway.

Native Windows, with Node.js and Python on PATH:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tests\windows.ps1
pwsh -NoProfile -File tests\windows.ps1
```

`tests/windows.ps1` compiles `fake-windows-ssh.cs` with the Windows .NET Framework
compiler. It tests native argv/stdin, a detached loopback tunnel, reuse/cleanup,
PID identity checks, a real local HTTP gateway, the dsh/opencode overlays,
environment/exit-code propagation, npm shims, and installer reruns with a fake
npm that rejects writes outside an explicit prefix. It intercepts persistent
PATH registration; no real account configuration is changed. The workflow in
`.github/workflows/offline.yml` runs Bash on Linux/macOS and PowerShell 5.1/7 on
Windows. These tests never connect to ROMEO or submit jobs.

- `tests/run.sh`: `bin/dsh-romeo` against `tests/fake-romeo/bin`: a fake `ssh` that runs the remote commands here, fake `romeollmtool`, `squeue`, `scancel` and gateway (`gateway.py`, 503 until a job has "loaded"), and a fake `dsh` and `codex` that record how they were started. When dsh is installed, the overlay is also composed by the real dsh. Then `bash -n` and `shellcheck` on the scripts. No network, no GPU.
- `tests/clients/openai_sdk.py`: a tool call, then a streamed answer, with the official OpenAI SDK (`pip install openai`).
- `tests/demo.py`: runs bash in a pseudo-terminal, types `dsh-romeo --launch` and keeps the screen while the model loads; a stand-in `open` first in `PATH` catches the URL dsh web hands to the browser; Playwright's Chromium opens it, types the task in the chat, keeps a screenshot every second until the agent is done, then opens the Trajectory tab and one record. The token of the URL is masked. Needs `pyte`, `Pillow` and `playwright` (`python -m playwright install chromium`).
- `tests/tui.py` (driving a program in a pseudo-terminal and drawing its screen) comes from [RSV](https://github.com/wolf75222/RSV).
