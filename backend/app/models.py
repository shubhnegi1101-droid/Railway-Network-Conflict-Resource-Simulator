from typing import Literal
from pydantic import BaseModel, Field


class Station(BaseModel):
    id: str            # station code, e.g. "DDN"
    name: str
    lat: float | None = None
    lon: float | None = None


class Track(BaseModel):
    id: str
    a: str
    b: str
    length_km: float = 1.0
    single_track: bool = True


class Train(BaseModel):
    id: str                          # train number, e.g. "04601"
    name: str = ""
    priority: int = 1
    speed_kmh: float = 80.0          # only used when run_min is not given
    departure_min: float = 0.0       # minutes since 00:00 of day 1
    dwell_min: float = 0.0           # only used when dwells is not given
    route: list[str]                 # station codes in travel order
    run_min: list[float] | None = None   # timetabled running time of each section
    dwells: list[float] | None = None    # timetabled stop time after each section


class SolveParams(BaseModel):
    headway_min: float = 2.0
    # disturbance scenario: delay some trains at departure, then ask the solver to repair the timetable
    disturb_count: int = 6
    disturb_min: float = 15.0
    disturb_max: float = 45.0
    disturb_seed: int = 1
    delays: dict[str, float] = Field(default_factory=dict)   # explicit {train_number: minutes}
    # OS scheduler
    policy: Literal["fcfs", "priority", "sjf"] = "priority"
    # metaheuristic
    start_from: Literal["planned", "os"] = "os"
    iterations: int = 3000
    start_temp: float = 60.0
    cooling: float = 0.999
    max_hold_min: float = 20.0
    seed: int = 7
    # fitness weights
    w_conflict: float = 100.0
    w_overlap: float = 5.0
    w_delay: float = 1.0
