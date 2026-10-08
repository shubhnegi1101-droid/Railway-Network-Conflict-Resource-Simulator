from neo4j import GraphDatabase

URI = "bolt://localhost:7687"
USERNAME = "neo4j"
PASSWORD = "password"

driver = GraphDatabase.driver(
    URI,
    auth=(USERNAME, PASSWORD)
)

BATCH_SIZE = 5000


def get_batch(tx, skip):
    result = tx.run("""
        MATCH (t:Train)-[r1:STOPS_AT]->(s1:Station)
        MATCH (t)-[r2:STOPS_AT]->(s2:Station)
        WHERE r2.sequence = r1.sequence + 1
        RETURN t.number AS train,
               r1.day AS day,
               r1.sequence AS sequence,
               r1.departure AS start_time,
               r2.arrival AS end_time,
               s1.code AS s1,
               s2.code AS s2
        ORDER BY t.number, r1.day, r1.sequence
        SKIP $skip
        LIMIT $limit
    """, skip=skip, limit=BATCH_SIZE)

    return [record.data() for record in result]


def create_batch(tx, batch):
    tx.run("""
        UNWIND $batch AS x

        MERGE (ts:TrackSection {
            id: CASE
                WHEN x.s1 < x.s2
                THEN x.s1 + '-' + x.s2
                ELSE x.s2 + '-' + x.s1
            END
        })

        MATCH (s1:Station {code: x.s1})
        MATCH (s2:Station {code: x.s2})
        MATCH (t:Train {number: x.train})

        MERGE (s1)-[:CONNECTS_TO]->(ts)
        MERGE (ts)-[:CONNECTS_TO]->(s2)

        MERGE (t)-[u:USES_TRACK]->(ts)

        SET u.day = x.day,
            u.start_time = x.start_time,
            u.end_time = x.end_time,
            u.sequence = x.sequence
    """, batch=batch)


skip = 5000

with driver.session() as session:

    while True:

        batch = session.execute_read(get_batch, skip)

        if not batch:
            break

        session.execute_write(create_batch, batch)

        skip += len(batch)

        print(f"Processed {skip} segments")

driver.close()

print("TRACK CREATION COMPLETED")