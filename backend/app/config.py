import os
from dotenv import load_dotenv

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "neo4j")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
CORS_ORIGINS = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",")]

SCOPE_FROM = os.getenv("SCOPE_FROM", "DDN").strip().upper()
SCOPE_TO = os.getenv("SCOPE_TO", "SRE").strip().upper()
SCOPE_STATIONS = [c.strip().upper() for c in os.getenv("SCOPE_STATIONS", "").split(",") if c.strip()]
DOUBLE_TRACK_MIN_TRAINS = int(os.getenv("DOUBLE_TRACK_MIN_TRAINS", "15"))
MAX_TRAINS = int(os.getenv("MAX_TRAINS", "120"))
