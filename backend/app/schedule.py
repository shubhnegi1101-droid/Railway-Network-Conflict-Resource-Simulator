"""Layer: timetable model. Turns (route + planned times + disturbances + holds) into track occupancy intervals."""
import copy
from dataclasses import dataclass
from .models import Station, Track, Train


@dataclass
class Step:
    track_id: str
    frm: str
    to: str
    direction: int      # +1 if travelling a->b, -1 if b->a
    hold: float         # minutes waited before entering this track
    enter: float
    exit: float


@dataclass
class TrainSchedule:
    train_id: str
    steps: list[Step]

    @property
    def arrival(self) -> float:
        return self.steps[-1].exit if self.steps else 0.0


class Network:
    def __init__(self, stations: list[Station], tracks: list[Track], trains: list[Train]):
        self.stations = {s.id: s for s in stations}
        self.trains = {t.id: t for t in trains}
        self.delays: dict[str, float] = {}      # initial departure delays (the disturbance)
        self.tracks: dict[str, Track] = {}
        self._pair: dict[frozenset, Track] = {}
        for t in tracks:  # de-duplicate A->B / B->A stored twice
            key = frozenset((t.a, t.b))
            if key not in self._pair:
                self._pair[key] = t
                self.tracks[t.id] = t
        self._validate()

    def with_delays(self, delays: dict[str, float]) -> "Network":
        n = copy.copy(self)
        n.delays = dict(delays)
        return n

    def track_between(self, a: str, b: str) -> Track | None:
        return self._pair.get(frozenset((a, b)))

    def start(self, tr: Train) -> float:
        return tr.departure_min + self.delays.get(tr.id, 0.0)

    def run_minutes(self, tr: Train, i: int, trk: Track) -> float:
        if tr.run_min:
            return tr.run_min[i]
        return trk.length_km / max(tr.speed_kmh, 1e-6) * 60.0

    def dwell(self, tr: Train, i: int) -> float:
        return tr.dwells[i] if tr.dwells else tr.dwell_min

    def _validate(self):
        for t in self.trains.values():
            if len(t.route) < 2:
                raise ValueError(f"Train {t.id} has fewer than 2 stations in its route")
            if t.run_min and len(t.run_min) != len(t.route) - 1:
                raise ValueError(f"Train {t.id}: run_min length does not match route")
            for a, b in zip(t.route, t.route[1:]):
                if self.track_between(a, b) is None:
                    raise ValueError(f"Train {t.id}: no track between {a} and {b}")

    def zero_holds(self) -> dict[str, list[float]]:
        return {t.id: [0.0] * (len(t.route) - 1) for t in self.trains.values()}


def simulate(net: Network, holds: dict[str, list[float]] | None = None) -> list[TrainSchedule]:
    holds = holds or {}
    out = []
    for tr in net.trains.values():
        h = holds.get(tr.id, [])
        clock = net.start(tr)
        steps = []
        for i, (a, b) in enumerate(zip(tr.route, tr.route[1:])):
            trk = net.track_between(a, b)
            hold = h[i] if i < len(h) else 0.0
            clock += hold
            enter = clock
            clock += net.run_minutes(tr, i, trk)
            steps.append(Step(trk.id, a, b, 1 if trk.a == a else -1, hold, enter, clock))
            clock += net.dwell(tr, i)
        out.append(TrainSchedule(tr.id, steps))
    return out
