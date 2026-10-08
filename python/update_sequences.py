import json
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password"

SCHEDULES_FILE = "../dataset/schedules.json"

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

print("Loading schedules...")

with open(SCHEDULES_FILE, "r") as f:
    schedules_data = json.load(f)

updates = []
sequence_counter = {}

for s in schedules_data:

    train_number = str(s.get("train_number", ""))
    station_code = s.get("station_code")
    day = s.get("day")

    if not train_number or not station_code or day is None:
        continue

    key = (train_number, day)

    sequence_counter[key] = sequence_counter.get(key, 0) + 1

    updates.append({
        "train_number": train_number,
        "station_code": station_code,
        "day": day,
        "sequence": sequence_counter[key]
    })

print(f"Prepared {len(updates)} schedule records")


def update_batch(tx, batch):

    tx.run("""
        UNWIND $batch AS s

        MATCH (train:Train {number: s.train_number})
        MATCH (station:Station {code: s.station_code})

        MATCH (train)-[r:STOPS_AT]->(station)
        WHERE r.day = s.day

        SET r.sequence = s.sequence
    """, batch=batch)


BATCH_SIZE = 5000

with driver.session() as session:

    for start in range(0, len(updates), BATCH_SIZE):

        batch = updates[start:start + BATCH_SIZE]

        session.execute_write(update_batch, batch)

        print(
            f"Updated {min(start + BATCH_SIZE, len(updates))}"
            f"/{len(updates)}"
        )

driver.close()

print("SEQUENCE UPDATE COMPLETED")