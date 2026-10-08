"""Small demo network (used by tests and scripts/seed_demo.py)."""
from .models import Station, Track, Train

STATIONS = [Station(id=i, name=n) for i, n in
            [("A", "Alder"), ("B", "Birch"), ("C", "Cedar"), ("D", "Dunmore"), ("E", "Elm"), ("F", "Fenwick")]]
TRACKS = [
    Track(id="AB", a="A", b="B", length_km=10, single_track=False),
    Track(id="BC", a="B", b="C", length_km=13, single_track=True),
    Track(id="CD", a="C", b="D", length_km=12, single_track=True),
    Track(id="DE", a="D", b="E", length_km=10, single_track=False),
    Track(id="CF", a="C", b="F", length_km=15, single_track=True),
]
TRAINS = [
    Train(id="IC101", priority=3, speed_kmh=100, departure_min=0, route=list("ABCDE")),
    Train(id="RE202", priority=2, speed_kmh=90, departure_min=3, route=list("EDCBA")),
    Train(id="RB303", priority=2, speed_kmh=80, departure_min=6, route=list("FCBA")),
    Train(id="RB404", priority=1, speed_kmh=80, departure_min=9, route=list("ABCF")),
    Train(id="FR505", priority=1, speed_kmh=60, departure_min=4, route=list("ABCDE")),
]
