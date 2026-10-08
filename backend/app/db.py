from neo4j import GraphDatabase
from . import config

_driver = None


def connect():
    global _driver
    _driver = GraphDatabase.driver(config.NEO4J_URI, auth=(config.NEO4J_USER, config.NEO4J_PASSWORD))
    _driver.verify_connectivity()


def close():
    global _driver
    if _driver:
        _driver.close()
        _driver = None


def run(query: str, **params) -> list[dict]:
    if _driver is None:
        raise RuntimeError("Neo4j driver is not connected")
    with _driver.session(database=config.NEO4J_DATABASE) as session:
        return [r.data() for r in session.run(query, **params)]
