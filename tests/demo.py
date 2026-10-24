#!/usr/bin/env python3
"""Records the README's GIF: a real dsh-romeo run, typed in a shell, drawn like a terminal.

    python3 tests/demo.py record --dir /tmp/dsh-demo     # runs it for real (launches a model job)
    python3 tests/demo.py render                         # draws img/dsh-romeo.gif from the recording

`record` types the command in a bash prompt inside /tmp/dsh-demo (a small project with a failing
test), keeps a snapshot of the screen every few seconds until the shell prompt comes back, and saves
them in tests/demo-frames.json. While the model loads (minutes), frames are kept less often and shown
briefly, so the GIF stays short. `render` turns the snapshots into img/dsh-romeo.gif.
Needs pyte and Pillow (pip install pyte pillow).
"""

import argparse
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tui import Term, render_png, save_gif  # noqa: E402

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRAMES = os.path.join(REPO, "tests", "demo-frames.json")
COMMAND = 'dsh-romeo --launch headless "Run the tests with python3 -m unittest, fix the bug, run them again"'


def record(args):
    env = {"PS1": "\\[\\e[1;32m\\]~/stats\\[\\e[0m\\] $ ", "HISTFILE": "/dev/null", "COLORTERM": "truecolor",
           "BASH_SILENCE_DEPRECATION_WARNING": "1"}
    t = Term(["bash", "--noprofile", "--norc", "-i"], cols=args.cols, rows=args.rows, env=env, cwd=args.dir)
    frames = []   # (seconds since start, shown for ms, screen)
    start = time.time()

    def shot(ms):
        frames.append((round(time.time() - start, 1), ms, t.snapshot()))

    t.sleep(1.0)
    shot(900)
    for i, ch in enumerate(COMMAND):          # typed, a few characters per frame
        t.send(ch)
        t.sleep(0.03)
        if i % 3 == 2:
            shot(70)
    shot(600)
    t.send("enter")
    last = ""
    deadline = time.time() + args.timeout * 60
    while time.time() < deadline:
        t.sleep(2.0)
        text = t.text()
        lines = [line for line in t.lines() if line]
        prompt_back = " ready " in text and lines[-1] == "~/stats $"
        loading = "Ctrl-C stops waiting" in text
        if text != last:
            # Loading: one frame every 20 s of real time, 0.5 s each in the GIF.
            if not loading or not frames or time.time() - start - frames[-1][0] >= 20:
                shot(500 if loading else 900)
            last = text
        if prompt_back:
            break
    shot(8000)
    t.close()
    with open(FRAMES, "w") as f:
        json.dump(frames, f)
    print("%d frames, %.0f s recorded -> %s" % (len(frames), time.time() - start, FRAMES))


def render(args):
    with open(FRAMES) as f:
        frames = json.load(f)
    # The model loads for minutes: keep at most 10 of those frames, evenly spaced.
    loading = [i for i, (_, ms, _) in enumerate(frames) if ms == 500]
    if len(loading) > 10:
        keep = {loading[round(k * (len(loading) - 1) / 9)] for k in range(10)}
        frames = [f for i, f in enumerate(frames) if i not in loading or i in keep]
    # macOS's /bin/bash greets with a notice about zsh (older recordings): not part of the demo.
    notice = ("The default interactive shell is now zsh", "To update your account to use zsh", "For more details, please visit")

    def without_notice(cells):
        text = ["".join(c[0] for c in row) for row in cells]
        last = max((i for i, line in enumerate(text) if line.startswith(notice)), default=-1)
        return cells[last + 1:]

    frames = [(t, ms, without_notice(cells)) for t, ms, cells in frames]
    height = max(len(cells) for _, _, cells in frames)
    blank = [[" ", "default", "default", False, False, False]] * len(frames[0][2][0])
    frames = [(t, ms, cells + [blank] * (height - len(cells))) for t, ms, cells in frames]
    images = [render_png([[tuple(c) for c in row] for row in cells]) for _, _, cells in frames]
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    save_gif(images, args.out, [ms for _, ms, _ in frames])
    print("%s: %d frames, %d KB" % (args.out, len(images), os.path.getsize(args.out) // 1024))


def main():
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("record")
    r.add_argument("--dir", default="/tmp/dsh-demo")
    r.add_argument("--cols", type=int, default=118)
    r.add_argument("--rows", type=int, default=30)
    r.add_argument("--timeout", type=float, default=45, help="minutes")
    d = sub.add_parser("render")
    d.add_argument("--out", default=os.path.join(REPO, "img", "dsh-romeo.gif"))
    args = p.parse_args()
    record(args) if args.cmd == "record" else render(args)


if __name__ == "__main__":
    main()
