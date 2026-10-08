"""Prints every label, relationship type and sample properties in your Neo4j database.
Run from backend/:  python -m scripts.inspect_graph
"""
from app import db

db.connect()
for r in db.run("CALL db.labels() YIELD label RETURN label"):
    l = r["label"]
    n = db.run(f"MATCH (n:`{l}`) RETURN count(n) AS c")[0]["c"]
    print(f"\n(:{l})  count={n}")
    for x in db.run(f"MATCH (n:`{l}`) RETURN properties(n) AS p LIMIT 2"):
        print("   ", x["p"])
for r in db.run("CALL db.relationshipTypes() YIELD relationshipType RETURN relationshipType"):
    t = r["relationshipType"]
    print(f"\n[:{t}]")
    for x in db.run(f"MATCH (a)-[r:`{t}`]->(b) RETURN labels(a)[0] AS src, labels(b)[0] AS dst, count(*) AS c"):
        print("   ", x)
    for x in db.run(f"MATCH ()-[r:`{t}`]->() RETURN properties(r) AS p LIMIT 2"):
        print("    props:", x["p"])
db.close()
