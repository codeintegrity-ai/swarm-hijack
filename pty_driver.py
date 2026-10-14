#!/usr/bin/env python3
"""Drive a `muse` TUI session under a pseudo-terminal.

Used by the PoC to launch a realistic victim session (a developer working in
their terminal) from scripts/CI where no controlling tty exists.

Usage:
  python3 pty_driver.py --log /tmp/victim.tty.log --cwd /path/to/repo \
      [--env KEY=VAL ...] -- "prompt text" [extra muse args...]

The child gets a fresh pty as its controlling terminal. Output is mirrored to
--log. Exits when the child exits.
"""
import argparse
import os
import pty
import select
import signal
import subprocess
import sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--log", required=True)
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--env", action="append", default=[])
    ap.add_argument("--inject", action="append", default=[],
                    help="SECONDS:TEXT — type TEXT into the pty SECONDS after start; TEXT may contain \\n (sent as \\r, i.e. Enter)")
    ap.add_argument("--auto-approve", nargs="?", const=4.0, type=float, default=None,
                    metavar="DELAY",
                    help="watch the TUI for the network-approval menu and answer it like a human: "
                         "type '2' + Enter ('Yes, don't ask again this session') DELAY seconds after the "
                         "menu first appears. DELAY defaults to 4s. Up to --auto-approve-max approvals.")
    ap.add_argument("--auto-approve-max", type=int, default=6)
    ap.add_argument("cmd", nargs=argparse.REMAINDER, help="-- followed by argv; if the first token is a prompt it is passed to muse")
    args = ap.parse_args()

    cmd = args.cmd
    if cmd and cmd[0] == "--":
        cmd = cmd[1:]
    if not cmd:
        ap.error("no command given")

    env = dict(os.environ)
    for kv in args.env:
        k, _, v = kv.partition("=")
        env[k] = v

    pid, fd = pty.fork()
    if pid == 0:
        os.chdir(args.cwd)
        os.execvpe(cmd[0], cmd, env)

    import fcntl
    import struct
    import termios
    fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 80, 0, 0))

    logf = open(args.log, "wb", buffering=0)
    exit_status = 1
    pending = b""
    import time as _time
    started = _time.monotonic()
    injects = []
    for spec in args.inject:
        t, _, txt = spec.partition(":")
        try:
            injects.append((float(t), txt.replace("\\n", "\r").encode()))
        except ValueError:
            pass
    injects.sort()
    # auto-approve state: detect the network-approval menu in the TUI stream,
    # then answer it with option 2 ("Yes, don't ask again this session").
    MENU = b"Would you like to allow this network access?"
    aa_window = b""
    aa_pending_at = None   # monotonic time at which to type the key
    aa_cooldown_until = 0.0
    aa_count = 0
    try:
        while True:
            now = _time.monotonic() - started
            while injects and now >= injects[0][0]:
                os.write(fd, injects.pop(0)[1])
            if args.auto_approve is not None and aa_pending_at is not None:
                if _time.monotonic() >= aa_pending_at:
                    aa_pending_at = None
                    aa_cooldown_until = _time.monotonic() + 30
                    aa_count += 1
                    os.write(fd, b"2\r")
                    print(f"[pty_driver] auto-approve #{aa_count}: sent '2' + Enter", flush=True)
            try:
                r, _, _ = select.select([fd], [], [], 0.5)
            except select.error:
                break
            if fd in r:
                try:
                    data = os.read(fd, 65536)
                except OSError:
                    break
                if not data:
                    break
                logf.write(data)
                sys.stdout.buffer.write(data)
                sys.stdout.buffer.flush()
                if args.auto_approve is not None and aa_pending_at is None and \
                        _time.monotonic() >= aa_cooldown_until and \
                        aa_count < args.auto_approve_max:
                    aa_window = (aa_window + data)[-2048:]
                    if MENU in aa_window:
                        aa_pending_at = _time.monotonic() + args.auto_approve
                        print(f"[pty_driver] network-approval menu detected; will answer in {args.auto_approve:.0f}s", flush=True)
                # answer terminal device-status queries the TUI blocks on
                pending += data
                while b"\x1b[6n" in pending:
                    head, _, pending = pending.partition(b"\x1b[6n")
                    os.write(fd, b"\x1b[24;80R")
                while b"\x1b[c" in pending:
                    head, _, pending = pending.partition(b"\x1b[c")
                    os.write(fd, b"\x1b[?1;2c")
                if len(pending) > 4096:
                    pending = pending[-64:]
            done, status = os.waitpid(pid, os.WNOHANG)
            if done:
                exit_status = os.waitstatus_to_exitcode(status)
                # drain remaining pty output
                try:
                    while True:
                        data = os.read(fd, 65536)
                        if not data:
                            break
                        logf.write(data)
                except OSError:
                    pass
                break
    finally:
        try:
            os.kill(pid, signal.SIGHUP)
        except OSError:
            pass
        os.close(fd)
        logf.close()
    return exit_status


if __name__ == "__main__":
    sys.exit(main())
