"""Speeds up lookups on your 390k STOPS_AT relationships.   python -m scripts.create_indexes"""
from app import db

db.connect()
db.run("CREATE INDEX station_code IF NOT EXISTS FOR (s:Station) ON (s.code)")
db.run("CREATE INDEX train_number IF NOT EXISTS FOR (t:Train) ON (t.number)")
print("Indexes ready.")
db.close()
