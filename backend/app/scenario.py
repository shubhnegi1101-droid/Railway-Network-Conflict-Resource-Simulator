"""A real timetable is usually conflict-free, so we inject a disturbance (late departures) and let the solver repair it."""
import random
from .models import SolveParams
from .schedule import Network


def make_scenario(net: Network, p: SolveParams) -> Network:
    rnd = random.Random(p.disturb_seed)
    ids = sorted(net.trains)
    k = min(max(p.disturb_count, 0), len(ids))
    delays = {t: round(rnd.uniform(p.disturb_min, p.disturb_max), 1) for t in rnd.sample(ids, k)}
    delays.update({t: d for t, d in p.delays.items() if t in net.trains})
    return net.with_delays(delays)
