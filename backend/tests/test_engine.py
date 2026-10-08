"""Runs the whole algorithm stack WITHOUT Neo4j.   python -m tests.test_engine"""
from app.conflicts import detect
from app.demo_data import STATIONS, TRACKS, TRAINS
from app.evaluation import Evaluator
from app.models import SolveParams
from app.optimizer import anneal
from app.os_scheduler import os_schedule
from app.schedule import Network

net = Network(STATIONS, TRACKS, TRAINS)
p = SolveParams()
ev = Evaluator(net, p)
base = ev.evaluate(net.zero_holds())
print("planned   : conflicts", len(base.conflicts), "fitness", round(base.fitness, 1))
for pol in ("fcfs", "priority", "sjf"):
    h = os_schedule(net, SolveParams(policy=pol))
    e = ev.evaluate(h)
    print(f"os {pol:8}: conflicts", len(e.conflicts), "delay", round(sum(e.delays.values()), 1), "fitness", round(e.fitness, 1))
    assert len(e.conflicts) == 0
best, be, hist = anneal(net, ev, net.zero_holds(), p)
print("annealing : conflicts", len(be.conflicts), "delay", round(sum(be.delays.values()), 1), "fitness", round(be.fitness, 1))
assert be.fitness <= base.fitness
print("OK")
