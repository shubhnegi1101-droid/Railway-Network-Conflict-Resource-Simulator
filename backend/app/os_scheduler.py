"""Layer: OS-style scheduling.

Analogy
  train        = process
  track block  = shared resource (mutex for single track, one lock per direction for double track)
  waiting      = time in the ready queue before the lock is granted
  policy       = queue ordering (FCFS, priority scheduling, shortest-job-first)

Trains are admitted one by one in policy order. Each train takes the earliest slot on every
block that does not collide with trains already admitted, so the result is conflict-free.
"""
from .models import SolveParams
from .schedule import Network, simulate


def _order(net: Network, policy: str):
    trains = list(net.trains.values())
    if policy == "fcfs":
        trains.sort(key=lambda t: (t.departure_min, t.id))
    elif policy == "priority":
        trains.sort(key=lambda t: (-t.priority, t.departure_min, t.id))
    elif policy == "sjf":
        free = {s.train_id: s.arrival - net.trains[s.train_id].departure_min for s in simulate(net)}
        trains.sort(key=lambda t: (free[t.id], t.id))
    else:
        raise ValueError(f"Unknown policy {policy}")
    return trains


def os_schedule(net: Network, params: SolveParams) -> dict[str, list[float]]:
    h = params.headway_min
    busy: dict[str, list[tuple[float, float]]] = {}
    holds = net.zero_holds()

    for tr in _order(net, params.policy):
        clock = net.start(tr)
        for i, (a, b) in enumerate(zip(tr.route, tr.route[1:])):
            trk = net.track_between(a, b)
            direction = 1 if trk.a == a else -1
            key = trk.id if trk.single_track else f"{trk.id}:{direction}"
            run = net.run_minutes(tr, i, trk)
            enter = clock
            for _ in range(10_000):  # wait until the block is free
                clash = next((q for q in busy.get(key, []) if enter < q[1] + h and q[0] < enter + run + h), None)
                if clash is None:
                    break
                enter = clash[1] + h
            holds[tr.id][i] = enter - clock
            busy.setdefault(key, []).append((enter, enter + run))
            clock = enter + run + net.dwell(tr, i)
    return holds
