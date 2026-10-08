import json
from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password"

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

TRAINS_FILE = "../dataset/trains.json"
STATIONS_FILE = "../dataset/stations.json"
SCHEDULES_FILE = "../dataset/schedules.json"


# =========================
# Load files
# =========================

print("Loading trains...")
with open(TRAINS_FILE, "r") as f:
    trains_data = json.load(f)

print("Loading stations...")
with open(STATIONS_FILE, "r") as f:
    stations_data = json.load(f)

print("Loading schedules...")
with open(SCHEDULES_FILE, "r") as f:
    schedules_data = json.load(f)

print(f"Trains: {len(trains_data['features'])}")
print(f"Stations: {len(stations_data['features'])}")
print(f"Schedules: {len(schedules_data)}")


# =========================
# Neo4j connection
# =========================

def create_constraints(tx):

    tx.run("""
        CREATE CONSTRAINT train_number_unique IF NOT EXISTS
        FOR (t:Train)
        REQUIRE t.number IS UNIQUE
    """)

    tx.run("""
        CREATE CONSTRAINT station_code_unique IF NOT EXISTS
        FOR (s:Station)
        REQUIRE s.code IS UNIQUE
    """)


# =========================
# Import stations in batch
# =========================

def import_stations(tx, stations):

    tx.run("""
        UNWIND $stations AS s
        MERGE (station:Station {code: s.code})
        SET station.name = s.name
    """, stations=stations)


# =========================
# Import trains in batch
# =========================

def import_trains(tx, trains):

    tx.run("""
        UNWIND $trains AS t

        MERGE (train:Train {number: t.number})

        SET train.name = t.name,
            train.distance = t.distance,
            train.duration_m = t.duration

        FOREACH (x IN CASE
            WHEN t.from_code IS NOT NULL
            THEN [1] ELSE []
        END |
            MERGE (s1:Station {code: t.from_code})
            SET s1.name = t.from_name
            MERGE (train)-[:STARTS_AT]->(s1)
        )

        FOREACH (x IN CASE
            WHEN t.to_code IS NOT NULL
            THEN [1] ELSE []
        END |
            MERGE (s2:Station {code: t.to_code})
            SET s2.name = t.to_name
            MERGE (train)-[:ENDS_AT]->(s2)
        )
    """, trains=trains)


# =========================
# Import schedules in batch
# =========================

def import_schedules(tx, schedules):

    tx.run("""
        UNWIND $schedules AS s

        MATCH (train:Train {number: s.train_number})
        MATCH (station:Station {code: s.station_code})

        MERGE (train)-[r:STOPS_AT {
            day: s.day,
            sequence: s.sequence
        }]->(station)

        SET r.arrival = s.arrival,
            r.departure = s.departure
    """, schedules=schedules)


# =========================
# Prepare station data
# =========================

print("Preparing stations...")

stations = []

for feature in stations_data["features"]:

    p = feature["properties"]

    code = p.get("code") or p.get("station_code")
    name = p.get("name") or p.get("station_name")

    if code:
        stations.append({
            "code": code,
            "name": name
        })


# =========================
# Prepare train data
# =========================

print("Preparing trains...")

trains = []

for feature in trains_data["features"]:

    p = feature["properties"]

    number = str(p.get("number", ""))

    if not number:
        continue

    trains.append({
        "number": number,
        "name": p.get("name"),
        "from_code": p.get("from_station_code"),
        "from_name": p.get("from_station_name"),
        "to_code": p.get("to_station_code"),
        "to_name": p.get("to_station_name"),
        "distance": p.get("distance"),
        "duration": p.get("duration_m")
    })


# =========================
# Prepare schedules
# =========================

# =========================
# Prepare schedules
# =========================

print("Preparing schedules...")

schedules = []

# Keep separate sequence for each train + day
sequence_counter = {}

for s in schedules_data:

    train_number = str(s.get("train_number", ""))
    station_code = s.get("station_code")
    day = s.get("day")

    if not train_number or not station_code or day is None:
        continue

    key = (train_number, day)

    if key not in sequence_counter:
        sequence_counter[key] = 1
    else:
        sequence_counter[key] += 1

    schedules.append({
        "train_number": train_number,
        "station_code": station_code,
        "day": day,
        "sequence": sequence_counter[key],
        "arrival": s.get("arrival"),
        "departure": s.get("departure")
    })


print(f"Valid schedules: {len(schedules)}")


# =========================
# Start import
# =========================

with driver.session() as session:

    print("Creating constraints...")
    session.execute_write(create_constraints)

    print("Importing stations...")
    session.execute_write(import_stations, stations)

    print("Importing trains...")
    session.execute_write(import_trains, trains)


    # -------------------------
    # Batch schedules
    # -------------------------

    BATCH_SIZE = 5000

    total = len(schedules)

    print("Importing schedules...")

    for start in range(0, total, BATCH_SIZE):

        batch = schedules[start:start + BATCH_SIZE]

        session.execute_write(
            import_schedules,
            batch
        )

        completed = min(start + BATCH_SIZE, total)

        print(
            f"Schedules imported: "
            f"{completed}/{total}"
        )


driver.close()

print()
print("==============================")
print("IMPORT COMPLETED SUCCESSFULLY")
print("==============================")