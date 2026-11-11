#!/usr/bin/env python3
"""Check that the museum's catalogue matches its rooms.

Every directory under exhibits/ must have a README.md, a row in the README's
exhibit table, a row in PLANTED.md and a "Directory:" line in the README whose
file list names exactly the files the directory holds (README.md aside). Rows
or file names that point at nothing fail too. Standard library only.

Usage: python3 scripts/check-museum.py   (from the repository root)
"""

import re
import sys
from pathlib import Path

root = Path(__file__).resolve().parent.parent
readme = (root / "README.md").read_text(encoding="utf-8")
planted = (root / "PLANTED.md").read_text(encoding="utf-8")
errors = []

rooms = sorted(p.name for p in (root / "exhibits").iterdir() if p.is_dir())
if not rooms:
    errors.append("exhibits/ is empty")

table = set(re.findall(r"^\| (\d\d) \| \[([^\]]+)\]\(\./exhibits/(\d\d-[^)]+)\) \|", readme, re.M))
table_dirs = {d for _, _, d in table}
for num, name, d in table:
    if d != f"{num}-{name}":
        errors.append(f"README table: row {num} {name} links to exhibits/{d}")

planted_rows = {f"{n}-{m}" for n, m in re.findall(r"^\| (\d\d) \| ([a-z0-9-]+) \|", planted, re.M)}

listed = {}
for m in re.finditer(r"^Directory: \[`exhibits/([^`]+)`\]\(\./exhibits/([^)]+)\)(.*)$", readme, re.M):
    d, link, rest = m.groups()
    if d != link:
        errors.append(f"README: Directory line shows exhibits/{d} but links to exhibits/{link}")
    listed[d] = set(re.findall(r"`([^`]+)`", rest))

for d in rooms:
    files = {
        p.relative_to(root / "exhibits" / d).as_posix()
        for p in (root / "exhibits" / d).rglob("*")
        if p.is_file()
    }
    if "README.md" not in files:
        errors.append(f"exhibits/{d}: no README.md")
    files.discard("README.md")
    if d not in table_dirs:
        errors.append(f"exhibits/{d}: missing from the README exhibit table")
    if d not in planted_rows:
        errors.append(f"exhibits/{d}: missing from PLANTED.md")
    if d not in listed:
        errors.append(f"exhibits/{d}: no 'Directory:' line in the README")
        continue
    for f in sorted(listed[d] - files):
        errors.append(f"exhibits/{d}: README lists `{f}`, which does not exist")
    for f in sorted(files - listed[d]):
        errors.append(f"exhibits/{d}: `{f}` is not listed in the README")

for d in sorted((table_dirs | planted_rows | set(listed)) - set(rooms)):
    errors.append(f"exhibits/{d}: catalogued but there is no such directory")

if errors:
    print("\n".join(errors))
    sys.exit(1)
print(f"ok: {len(rooms)} exhibits, catalogue and rooms match")
