# SPDX-License-Identifier: AGPL-3.0-only
"""The gamepad button remapper, without widgets: the table of what each button counts as, and the listener that tells which button is
pressed.

The table works on the buttons of the Wii U GamePad that the game gets (after the Xbox / Nintendo layout turned the pad's own buttons
into them): `B>A` means that when the player presses the button the game would take as B, it gets A. The engine (`MH3U_PAD_MAP`,
`padmap.rs` of mh3u-rt) applies it; `mh3u-tools.exe pad-listen` reports the real button pressed, so the launcher can ask for it.
"""

import json
import os
import queue
import subprocess
import threading

# every button that can be mapped, in the order the engine lists them: (name for the engine and the file, id of the controller picture)
BUTTONS = [
    ("A", "A"),
    ("B", "B"),
    ("X", "X"),
    ("Y", "Y"),
    ("L", "L"),
    ("R", "R"),
    ("ZL", "ZL"),
    ("ZR", "ZR"),
    ("PLUS", "plus"),
    ("MINUS", "minus"),
    ("HOME", "home"),
    ("UP", "up"),
    ("DOWN", "down"),
    ("LEFT", "left"),
    ("RIGHT", "right"),
    ("L3", "lstick"),
    ("R3", "rstick"),
]
NAMES = [n for n, _ in BUTTONS]
NAME_OF_ID = {i: n for n, i in BUTTONS}
ID_OF_NAME = dict(BUTTONS)

# how a button is written on the screen (the controller's own signs where it has them)
SHORT = {"PLUS": "+", "MINUS": "−", "HOME": "⌂", "UP": "↑", "DOWN": "↓", "LEFT": "←", "RIGHT": "→", "L3": "LS", "R3": "RS"}


def short(name):
    return SHORT.get(name, name)


class PadMap:
    """For each button of the pad, the buttons it presses (its own by default; none = turned off)."""

    def __init__(self, table=None):
        self.to = {n: {n} for n in NAMES}
        if table:
            self.load(table)

    # ---- reading ------------------------------------------------------------------------------
    def targets_of(self, source):
        return set(self.to[source])

    def sources_of(self, target):
        """The buttons of the pad that press `target`, in the usual order."""
        return [n for n in NAMES if target in self.to[n]]

    def is_default(self):
        return all(self.to[n] == {n} for n in NAMES)

    # ---- changing -----------------------------------------------------------------------------
    def assign(self, source, target):
        """The button `source` presses `target` (only that), and `target` is pressed by no other button: the player asked for this
        button to be that one's."""
        for n in NAMES:
            self.to[n].discard(target)
        self.to[source] = {target}

    def clear_target(self, target):
        """Nothing presses `target` any more."""
        for n in NAMES:
            self.to[n].discard(target)

    def reset(self):
        self.to = {n: {n} for n in NAMES}

    # ---- the file, the config and the engine ----------------------------------------------------
    def to_dict(self):
        """Only what is not as usual: {button: [buttons it presses]} (an empty list is a button turned off)."""
        return {n: [t for t in NAMES if t in self.to[n]] for n in NAMES if self.to[n] != {n}}

    def load(self, table):
        """From such a dict. Names that are not buttons are left out; anything that is not a dict is ignored. Returns whether it was
        all understood."""
        ok = isinstance(table, dict)
        if not ok:
            return False
        self.reset()
        for source, targets in table.items():
            s = str(source).strip().upper()
            if s not in self.to or not isinstance(targets, (list, tuple)):
                ok = False
                continue
            wanted = {str(t).strip().upper() for t in targets}
            if not wanted <= set(NAMES):
                ok = False
            self.to[s] = wanted & set(NAMES)
        return ok

    def to_env(self):
        """The value of MH3U_PAD_MAP ('' when nothing is changed): `B>A,A>B,ZL>`."""
        return ",".join(f"{n}>{'+'.join(t for t in NAMES if t in self.to[n])}" for n in NAMES if self.to[n] != {n})

    def to_json(self):
        return json.dumps({"format": "mh3u-pad-map", "version": 1, "map": self.to_dict()}, indent=2)

    @classmethod
    def from_json(cls, text):
        """A PadMap from an exported file, or None if it is not one."""
        try:
            data = json.loads(text)
        except (ValueError, TypeError):
            return None
        if not isinstance(data, dict) or data.get("format") != "mh3u-pad-map" or not isinstance(data.get("map"), dict):
            return None
        m = cls()
        m.load(data["map"])
        return m


def parse_listener_line(line):
    """What a line of `pad-listen` says: ('down', 'A'), ('up', 'A'), ('pad', 'name of a pad') or None."""
    line = line.strip()
    for kind in ("down", "up"):
        if line.startswith(kind + " "):
            name = line[len(kind) + 1 :].strip().upper()
            return (kind, name) if name in NAMES else None
    for start in ("gamepad connected: ", "gamepad: ", "[hid] gamepad read from the device: "):
        if line.startswith(start):
            name = line[len(start) :].strip()
            if start.startswith("[hid]") and " (" in name:
                name = name.rsplit(" (", 1)[0]
            return ("pad", name) if name else None
    return None


class PadListener:
    """Runs `mh3u-tools.exe pad-listen` and collects what it says. Use `poll()` from the interface's timer; it never blocks."""

    def __init__(self, exe, layout="xbox", seconds=600):
        self.exe = exe
        self.layout = layout
        self.seconds = seconds
        self.proc = None
        self.events = queue.Queue()

    @property
    def running(self):
        return self.proc is not None and self.proc.poll() is None

    def start(self):
        if self.running:
            return True
        if not self.exe or not os.path.isfile(self.exe):
            return False
        env = dict(os.environ)
        env["MH3U_PAD_LAYOUT"] = self.layout
        env.pop("MH3U_PAD_MAP", None)  # the listener says what the pad gives, not what the map makes of it
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            self.proc = subprocess.Popen(
                [self.exe, "pad-listen", "--seconds", str(self.seconds)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                env=env,
                creationflags=flags,
                text=True,
                encoding="utf-8",
                errors="replace",
                bufsize=1,
            )
        except OSError:
            self.proc = None
            return False
        for stream in (self.proc.stdout, self.proc.stderr):
            threading.Thread(target=self._read, args=(stream,), daemon=True).start()
        return True

    def _read(self, stream):
        try:
            for line in stream:
                event = parse_listener_line(line)
                if event:
                    self.events.put(event)
        except (OSError, ValueError):
            pass

    def poll(self):
        out = []
        while True:
            try:
                out.append(self.events.get_nowait())
            except queue.Empty:
                return out

    def stop(self):
        proc, self.proc = self.proc, None
        if proc and proc.poll() is None:
            try:
                proc.kill()
                proc.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                pass
        for stream in (proc.stdout, proc.stderr) if proc else ():
            try:
                stream.close()
            except (OSError, ValueError):
                pass
