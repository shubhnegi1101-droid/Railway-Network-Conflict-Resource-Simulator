"""Lists every station between two stations, so you can pick SCOPE_FROM / SCOPE_TO.
Run from backend/:  python -m scripts.find_corridor DDN SRE
"""
import sys
from app import db, repository

frm, to = (sys.argv[1:3] + ["DDN", "SRE"])[:2] if len(sys.argv) < 3 else sys.argv[1:3]
db.connect()
codes = repository.corridor(frm.upper(), to.upper())
names = {r["id"]: r["name"] for r in db.run(repository.Q_STATIONS, codes=codes)}
print(f"{len(codes)} stations between {frm} and {to}:")
for c in codes:
    print(f"  {c:6} {names.get(c, '')}")
print("\nSCOPE_STATIONS=" + ",".join(codes))
db.close()
