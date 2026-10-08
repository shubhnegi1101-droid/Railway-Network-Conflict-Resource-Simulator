"""Builds a network from rows shaped like YOUR Neo4j data (no database needed).   python -m tests.test_repository"""
from app import repository
from app.evaluation import Evaluator
from app.models import SolveParams
from app.os_scheduler import os_schedule
from app.scenario import make_scenario
from app.schedule import Network
from app.models import Station

def stops(num, name, items):
    return [dict(number=num, name=name, code=c, arr=a, dep=d, day=1, rid=i * 10 + hash(num) % 7)
            for i, (c, a, d) in enumerate(items)]

rows = (stops("12001", "Shatabdi Express", [("A", "None", "08:00:00"), ("B", "08:20:00", "08:20:00"), ("C", "08:45:00", "08:47:00"), ("D", "09:10:00", "None")])
      + stops("54001", "Dehradun Passenger", [("D", "None", "08:05:00"), ("C", "08:25:00", "08:27:00"), ("B", "08:50:00", "08:50:00"), ("A", "09:10:00", "None")])
      + stops("14001", "Intercity Express", [("A", "None", "08:10:00"), ("B", "08:32:00", "08:33:00"), ("C", "08:58:00", "None")]))

trains = repository.build_trains(rows)
tracks = repository.build_tracks(trains, double_min=99)
net = Network([Station(id=c, name=c) for c in "ABCD"], tracks, trains)
print("trains", [(t.id, t.priority, t.route) for t in net.trains.values()])
p = SolveParams(disturb_count=2, headway_min=3)
scn = make_scenario(net, p)
ev = Evaluator(scn, p)
b = ev.evaluate(scn.zero_holds())
a = ev.evaluate(os_schedule(scn, p))
print("disturbance", scn.delays, "| before", len(b.conflicts), "conflicts | after OS", len(a.conflicts))
assert len(a.conflicts) == 0
print("OK")
