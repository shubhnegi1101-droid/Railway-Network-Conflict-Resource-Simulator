"""Reads the railway timetable graph from Neo4j and turns it into the solver's network.

Your graph
  (:Train   {number, name, distance, duration_m})
  (:Station {code, name})
  (:Train)-[:STOPS_AT {arrival:'HH:MM:SS', departure:'HH:MM:SS'|'None', day}]->(:Station)

The graph has no :TRACK edges and no stop order, so
  * stop order  = sorted by (time, relationship id)
  * tracks      = consecutive stations on any train's route
  * run times   = the real timetable (arrival at B minus departure from A)
  * priority    = guessed from the train name (Rajdhani > Express > Passenger)
  * single/double track = guessed from how many trains use the section (see DOUBLE_TRACK_MIN_TRAINS)
"""
from collections import defaultdict
from . import config, db
from .models import Station, Track, Train

Q_BETWEEN = """
MATCH (t:Train)-[:STOPS_AT]->(:Station {code: $f}), (t)-[:STOPS_AT]->(:Station {code: $t})
MATCH (t)-[r:STOPS_AT]->(s:Station)
RETURN t.number AS number, s.code AS code, r.arrival AS arr, r.departure AS dep, r.day AS day, id(r) AS rid
"""

Q_STOPS = """
MATCH (t:Train)-[r:STOPS_AT]->(s:Station)
WHERE s.code IN $codes
RETURN t.number AS number, t.name AS name, s.code AS code,
       r.arrival AS arr, r.departure AS dep, r.day AS day, id(r) AS rid
"""

Q_STATIONS = "MATCH (s:Station) WHERE s.code IN $codes RETURN s.code AS id, coalesce(s.name, s.code) AS name"


def _minutes(value, day) -> float | None:
    """'11:11:00' + day 1 -> minutes since 00:00 of day 1."""
    if value is None or str(value).strip().lower() in ("", "none", "null", "nan"):
        return None
    parts = str(value).split(":")
    sec = float(parts[2]) if len(parts) > 2 else 0.0
    try:
        d = int(day)
    except (TypeError, ValueError):
        d = 1
    return (d - 1) * 1440 + int(parts[0]) * 60 + int(parts[1]) + sec / 60


def priority_of(name: str) -> int:
    n = (name or "").upper()
    if any(k in n for k in ("RAJDHANI", "SHATABDI", "DURONTO", "VANDE", "TEJAS", "GATIMAN", "HUMSAFAR")):
        return 5
    if any(k in n for k in ("PASSENGER", " PASS", "DMU", "MEMU", "LOCAL", "SHUTTLE")):
        return 1
    if any(k in n for k in ("SUPERFAST", " SF", "JAN SHATABDI", "GARIB")):
        return 4
    if any(k in n for k in ("EXPRESS", " EXP", "MAIL", "SPL", "SPECIAL")):
        return 3
    return 2


def _ordered(rows):
    """rows of one train -> [(key, rid, code, arr, dep)] sorted in travel order."""
    out = []
    for r in rows:
        a, d = _minutes(r["arr"], r["day"]), _minutes(r["dep"], r["day"])
        if a is None and d is None:
            continue
        out.append((a if a is not None else d, r["rid"], r["code"], a, d))
    out.sort(key=lambda x: (x[0], x[1]))
    return out


def corridor(frm: str, to: str) -> list[str]:
    """All station codes lying between two stations on trains that run between them."""
    by = defaultdict(list)
    for r in db.run(Q_BETWEEN, f=frm, t=to):
        by[r["number"]].append(r)
    codes: list[str] = []
    for rows in by.values():
        seq = [x[2] for x in _ordered(rows)]
        if frm in seq and to in seq:
            i, j = sorted((seq.index(frm), seq.index(to)))
            for c in seq[i:j + 1]:
                if c not in codes:
                    codes.append(c)
    return codes


def build_trains(rows, max_trains: int = 0) -> list[Train]:
    by, names = defaultdict(list), {}
    for r in rows:
        by[str(r["number"])].append(r)
        names[str(r["number"])] = r.get("name") or str(r["number"])
    trains = []
    for num, rs in by.items():
        route, arr, dep = [], [], []
        for _, _, code, a, d in _ordered(rs):
            if route and route[-1] == code:
                continue
            a = a if a is not None else d
            d = d if d is not None else a
            if dep:
                a = max(a, dep[-1])
            d = max(d, a)
            route.append(code); arr.append(a); dep.append(d)
        if len(route) < 2 or len(set(route)) < len(route):
            continue
        n = len(route)
        run = [max(0.5, arr[i + 1] - dep[i]) for i in range(n - 1)]
        dwell = [max(0.0, dep[i + 1] - arr[i + 1]) for i in range(n - 2)] + [0.0]
        trains.append(Train(id=num, name=names[num], priority=priority_of(names[num]),
                            departure_min=dep[0], route=route, run_min=run, dwells=dwell))
    trains.sort(key=lambda t: (-len(t.route), t.departure_min))
    if max_trains > 0:
        trains = trains[:max_trains]
    return trains


def build_tracks(trains: list[Train], double_min: int) -> list[Track]:
    use = defaultdict(int)
    for t in trains:
        for a, b in zip(t.route, t.route[1:]):
            use[tuple(sorted((a, b)))] += 1
    return [Track(id=f"{a}-{b}", a=a, b=b, length_km=1.0, single_track=n < double_min)
            for (a, b), n in sorted(use.items())]


def fetch_all():
    codes = config.SCOPE_STATIONS or corridor(config.SCOPE_FROM, config.SCOPE_TO)
    if len(codes) < 2:
        raise ValueError(f"No corridor found between {config.SCOPE_FROM} and {config.SCOPE_TO}. "
                         f"Check the codes in .env or set SCOPE_STATIONS.")
    trains = build_trains(db.run(Q_STOPS, codes=codes), config.MAX_TRAINS)
    if not trains:
        raise ValueError("No trains with 2+ stops inside the scope")
    used = sorted({c for t in trains for c in t.route})
    stations = [Station(**r) for r in db.run(Q_STATIONS, codes=used)]
    known = {s.id for s in stations}
    stations += [Station(id=c, name=c) for c in used if c not in known]
    return stations, build_tracks(trains, config.DOUBLE_TRACK_MIN_TRAINS), trains
