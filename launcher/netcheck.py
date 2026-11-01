"""Network helpers for the online mode, with no widgets: firewall inspection/repair for the game's programs and a UDP probe of the room server."""
import json
import os
import re
import socket
import struct
import subprocess
import sys
import time

NO_WINDOW = getattr(subprocess, "CREATE_NO_WINDOW", 0)
# the server's NAT-check answers a 16-byte ">IIII"(type, 0, 0, 0) request with the same type (types 0x65 and 0x67)
PROBE_TYPE = 0x65
SERVER_PORTS = (1223, 1224, 10025, 33335)
RELAY_PORTS = "27100-27387"


def _ps(script, timeout=25):
    if sys.platform != "win32":
        return ""
    full = "[Console]::OutputEncoding=[Text.Encoding]::UTF8; " + script
    out = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", full],
        capture_output=True, timeout=timeout, creationflags=NO_WINDOW,
    )
    return out.stdout.decode("utf-8", "replace")


def inspect_rules(exe_paths):
    """Inbound firewall rules that name one of `exe_paths`: [{Name, Action, Enabled, Profile, Program, Proto}], or None if it cannot be read."""
    paths = [os.path.normpath(p).lower() for p in exe_paths if p]
    if not paths or sys.platform != "win32":
        return []
    quoted = ",".join("'" + p.replace("'", "''") + "'" for p in paths)
    script = (
        f"$paths=@({quoted}); $out=@(); "
        "Get-NetFirewallApplicationFilter | ForEach-Object { $p=[string]$_.Program; "
        "if($p -and ($paths -contains $p.ToLower())){ $r=$_ | Get-NetFirewallRule; $pf=$r | Get-NetFirewallPortFilter; "
        "$out += [pscustomobject]@{Name=$r.DisplayName;Dir=[string]$r.Direction;Action=[string]$r.Action;"
        "Enabled=[string]$r.Enabled;Profile=[string]$r.Profile;Program=$p;Proto=[string]$pf.Protocol} } }; "
        "ConvertTo-Json -InputObject @($out) -Compress"
    )
    try:
        text = _ps(script).strip()
        data = json.loads(text) if text else []
    except Exception:
        return None
    return [r for r in data if str(r.get("Dir", "")).lower() == "inbound"]


def analyze_rules(rules, exe_paths):
    """Problems per program: a Block rule (it beats every Allow) or no Allow rule covering Private and Public.

    Returns a list of (path, kind, detail) with kind 'block' or 'missing'; empty when all is well.
    """
    problems = []
    for exe in exe_paths:
        if not exe:
            continue
        key = os.path.normpath(exe).lower()
        mine = [r for r in rules if os.path.normpath(str(r.get("Program", ""))).lower() == key and str(r.get("Enabled")).lower() == "true"]
        blocks = [r for r in mine if str(r.get("Action")).lower() == "block"]
        if blocks:
            problems.append((exe, "block", ", ".join(sorted({str(b.get("Profile")) for b in blocks}))))
            continue
        covered = set()
        for r in mine:
            if str(r.get("Action")).lower() != "allow" or str(r.get("Proto")).lower() not in ("udp", "any", "17"):
                continue
            prof = str(r.get("Profile")).lower()
            if "any" in prof or "all" in prof:
                covered |= {"private", "public"}
            else:
                covered |= {x.strip() for x in prof.split(",")}
        if not {"private", "public"} <= covered:
            problems.append((exe, "missing", "Private+Public" if not covered else ", ".join(sorted(covered))))
    return problems


RESULT_FILE = "mh3u_fw_result.txt"


def rule_names(group, exe_paths):
    """Names of the rules this launcher makes (netsh's `add rule` has no group argument, so the name is all that ties them)."""
    return [f"{group} UDP {p}" for p in SERVER_PORTS] + [f"{group} UDP relay"] + [f"{group} {os.path.basename(p)}" for p in exe_paths if p]


def enable_lines(group, exe_paths, enable):
    flag = "yes" if enable else "no"
    return [f'netsh advfirewall firewall set rule name="{n}" new enable={flag} >nul 2>&1' for n in rule_names(group, exe_paths)]


def fix_lines(group, exe_paths, result_file=None):
    """netsh lines (run elevated) that leave one Allow rule per program on every profile, plus the server ports, and no Block rules.

    What netsh answers to the `add` lines goes to `result_file`, to see why a rule did not get made.
    """
    out = f'>> "{result_file}" 2>&1' if result_file else ">nul 2>&1"
    lines = []
    for name in rule_names(group, exe_paths):
        lines.append(f'netsh advfirewall firewall delete rule name="{name}" >nul 2>&1')
    for p in exe_paths:
        if p:
            # the rules Windows made from its "allow access" window (Allow or Block) for this very program
            lines.append(f'netsh advfirewall firewall delete rule name=all dir=in program="{p}" >nul 2>&1')
    for port in SERVER_PORTS:
        lines.append(
            f'netsh advfirewall firewall add rule name="{group} UDP {port}" dir=in action=allow '
            f"protocol=UDP localport={port} profile=any {out}"
        )
    lines.append(
        f'netsh advfirewall firewall add rule name="{group} UDP relay" dir=in action=allow '
        f"protocol=UDP localport={RELAY_PORTS} profile=any {out}"
    )
    for p in exe_paths:
        if p and os.path.isfile(p):
            lines.append(
                f'netsh advfirewall firewall add rule name="{group} {os.path.basename(p)}" dir=in action=allow '
                f'program="{p}" enable=yes profile=any {out}'
            )
    return lines


def describe(problems):
    out = []
    for exe, kind, detail in problems:
        name = os.path.basename(exe)
        if kind == "block":
            out.append(f"{name}: hay una regla de BLOQUEO en el firewall (anula cualquier permiso)")
        else:
            out.append(f"{name}: sin permiso de entrada en redes privadas y públicas (Radmin cuenta como pública)")
    return out


def network_profiles():
    """[(adapter, category)] of the connected networks (Radmin VPN usually shows as Public)."""
    try:
        text = _ps("ConvertTo-Json -InputObject @(Get-NetConnectionProfile | ForEach-Object { [pscustomobject]@{A=$_.InterfaceAlias;C=[string]$_.NetworkCategory} }) -Compress", 15).strip()
        return [(d["A"], d["C"]) for d in json.loads(text)] if text else []
    except Exception:
        return []


def udp_probe(host, port=10025, timeout=1.5, tries=3):
    """Ask the room server's NAT-check on `host` (UDP) and wait for its 16-byte answer: (ok, round-trip ms)."""
    req = struct.pack(">IIII", PROBE_TYPE, 0, 0, 0)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.settimeout(timeout)
            for _ in range(tries):
                t0 = time.perf_counter()
                try:
                    s.sendto(req, (host, port))
                    data, _addr = s.recvfrom(64)
                except socket.timeout:
                    continue
                except OSError:
                    # an ICMP "port unreachable" from a PC with nothing listening comes back as a reset on Windows
                    return False, 0
                if len(data) == 16 and struct.unpack(">I", data[:4])[0] == PROBE_TYPE:
                    return True, max(1, round((time.perf_counter() - t0) * 1000))
    except OSError:
        pass
    return False, 0


def ping_ms(host):
    """Average ICMP round trip in ms, or 0 when the PC does not answer pings (many firewalls drop them)."""
    try:
        proc = subprocess.run(["ping", "-n", "2", "-w", "2000", host], capture_output=True, text=True, timeout=12, creationflags=NO_WINDOW)
        times = [int(x) for x in re.findall(r"(?:tiempo|time)[=<] *([0-9]+) *ms", proc.stdout or "", re.I)]
        return max(1, round(sum(times) / len(times))) if proc.returncode == 0 and times else 0
    except Exception:
        return 0


def traversal_results(log_path, limit=5):
    """The last NAT-traversal lines of the room server's log: a pair of players that never shows up there never connected."""
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lines = [ln.rstrip() for ln in f if "report_nat_traversal_result" in ln]
        return lines[-limit:]
    except OSError:
        return []
