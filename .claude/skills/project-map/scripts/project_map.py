"""Live map of the capstone project folder.

Run from the project root:
    python .claude/skills/project-map/scripts/project_map.py tree
    python .claude/skills/project-map/scripts/project_map.py subckt [NAME]
    python .claude/skills/project-map/scripts/project_map.py meas [FILTER]
    python .claude/skills/project-map/scripts/project_map.py check
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))
NET = os.path.join(ROOT, "hspice", "sub_system.net")
TB = os.path.join(ROOT, "hspice", "sub_system_tb.sp")
MT0 = os.path.join(ROOT, "hspice", "result", "sub_system_tb.mt0")
SKIP_DIRS = {".git", "__pycache__", "node_modules"}

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def rel(p):
    return os.path.relpath(p, ROOT).replace("\\", "/")


def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f}{unit}" if unit == "B" else f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}TB"


def cmd_tree():
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = sorted(d for d in dirnames if d not in SKIP_DIRS)
        depth = rel(dirpath).count("/") + (0 if dirpath == ROOT else 1)
        if dirpath != ROOT:
            print("  " * (depth - 1) + rel(dirpath).split("/")[-1] + "/")
        for f in sorted(filenames):
            size = os.path.getsize(os.path.join(dirpath, f))
            print("  " * depth + f"{f}  ({human(size)})")


def parse_subckts():
    """Return list of (name, pins, start_line, end_line)."""
    out, cur = [], None
    with open(NET, encoding="utf-8", errors="replace") as fh:
        for i, line in enumerate(fh, 1):
            s = line.strip()
            m = re.match(r"\.SUBCKT\s+(\S+)\s*(.*)", s, re.I)
            if m:
                cur = [m.group(1), m.group(2).split(), i, None]
            elif re.match(r"\.ENDS\b", s, re.I) and cur:
                cur[3] = i
                out.append(tuple(cur))
                cur = None
    return out


def cmd_subckt(name=None):
    subs = parse_subckts()
    if name:
        subs = [s for s in subs if s[0].upper() == name.upper()]
        if not subs:
            sys.exit(f"no .SUBCKT named {name} in {rel(NET)}")
        n, pins, a, b = subs[0]
        print(f"{rel(NET)}:{a}-{b}  {n} ({' '.join(pins)})\n")
        with open(NET, encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()[a - 1:b]
        sys.stdout.write("".join(lines))
        return
    w = max(len(s[0]) for s in subs)
    for n, pins, a, b in subs:
        print(f"{n:<{w}}  L{a:>3}-{b:<3}  ({' '.join(pins)})")


def parse_mt0():
    """HSPICE .mt0: header lines, then names block, then values block."""
    with open(MT0, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    title = next((l for l in lines if l.startswith(".TITLE")), "")
    body = [l for l in lines if l and not l.startswith(("$", ".TITLE"))]
    tokens = " ".join(body).split()
    num = re.compile(r"^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$")
    first_val = next(i for i, t in enumerate(tokens) if num.match(t))
    names, vals = tokens[:first_val], tokens[first_val:]
    return title, list(zip(names, vals))


def cmd_meas(flt=None):
    title, pairs = parse_mt0()
    print(f"# {rel(MT0)}\n# {title}")
    for n, v in pairs:
        if flt and flt.lower() not in n.lower():
            continue
        print(f"{n:<22} = {v}")


def cmd_check():
    ok = True
    with open(TB, encoding="utf-8", errors="replace") as fh:
        tb = fh.read()
    m = re.search(r"\.MEAS\s+TRAN\s+PFM_REV\s+PARAM\s*=\s*'?(\d+)", tb, re.I)
    tb_rev = m.group(1) if m else None
    mt_rev = None
    if os.path.exists(MT0):
        mt_rev = dict(parse_mt0()[1]).get("pfm_rev")
        mt_rev = str(int(float(mt_rev))) if mt_rev else None
    print(f"PFM_REV  tb={tb_rev}  mt0={mt_rev}")
    if tb_rev != mt_rev:
        ok = False
        print("  !! result/ was not produced by the current tb (rerun on cad04)")
    for f in ("lis", "mt0", "tr0"):
        p = os.path.join(ROOT, "hspice", "result", f"sub_system_tb.{f}")
        if os.path.exists(p) and os.path.getmtime(p) < os.path.getmtime(NET):
            ok = False
            print(f"  !! {rel(p)} is older than sub_system.net")
    # stale path references to the old per-version layout
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if not f.endswith((".md", ".py", ".sp")):
                continue
            p = os.path.join(dirpath, f)
            if "project-map" in p:
                continue
            with open(p, encoding="utf-8", errors="replace") as fh:
                for i, line in enumerate(fh, 1):
                    if re.search(r"(result|archive)/v\d+", line):
                        ok = False
                        print(f"  stale path  {rel(p)}:{i}: {line.strip()}")
    print("OK" if ok else "issues found")


def main():
    args = sys.argv[1:]
    cmd = args[0] if args else "tree"
    rest = args[1] if len(args) > 1 else None
    {"tree": cmd_tree, "subckt": lambda: cmd_subckt(rest),
     "meas": lambda: cmd_meas(rest), "check": cmd_check}.get(
        cmd, lambda: sys.exit(__doc__))()


if __name__ == "__main__":
    main()
