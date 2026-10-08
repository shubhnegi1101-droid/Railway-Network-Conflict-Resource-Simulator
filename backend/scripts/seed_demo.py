"""Optional: load the demo network into Neo4j (MERGE only, nothing is deleted).
Run from backend/:  python -m scripts.seed_demo
"""
from app import db
from app.demo_data import STATIONS, TRACKS, TRAINS

db.connect()
for s in STATIONS:
    db.run("MERGE (s:Station {id:$id}) SET s.name=$name", id=s.id, name=s.name)
for t in TRACKS:
    db.run("""MATCH (a:Station {id:$a}), (b:Station {id:$b})
              MERGE (a)-[r:TRACK {id:$id}]->(b) SET r.length_km=$len, r.single_track=$single""",
           a=t.a, b=t.b, id=t.id, len=t.length_km, single=t.single_track)
for t in TRAINS:
    db.run("""MERGE (t:Train {id:$id}) SET t.name=$id, t.priority=$p, t.speed_kmh=$v,
              t.departure_min=$d, t.dwell_min=$w""", id=t.id, p=t.priority, v=t.speed_kmh, d=t.departure_min, w=t.dwell_min)
    for seq, st in enumerate(t.route):
        db.run("""MATCH (t:Train {id:$tid}), (s:Station {id:$sid})
                  MERGE (t)-[v:VISITS {seq:$seq}]->(s)""", tid=t.id, sid=st, seq=seq)
db.close()
print("Demo data loaded.")
