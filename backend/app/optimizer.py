"""Layer: metaheuristic optimisation (simulated annealing over per-segment hold times)."""
import copy
import math
import random
from .evaluation import Evaluation, Evaluator
from .models import SolveParams
from .schedule import Network


def _clamp(v: float, hi: float) -> float:
    return round(min(hi, max(0.0, v)) * 2) / 2   # half-minute resolution


def _mutate(net: Network, holds, cur: Evaluation, rnd: random.Random, p: SolveParams):
    # Targeted move: delay one of the trains involved in a real conflict (usually the lower priority one)
    if cur.conflicts and rnd.random() < 0.6:
        c = rnd.choice(cur.conflicts)
        a, b = net.trains[c.train_a], net.trains[c.train_b]
        victim = a if a.priority < b.priority else b if b.priority < a.priority else rnd.choice([a, b])
        if rnd.random() < 0.2:
            victim = b if victim is a else a
        sched = next(s for s in cur.schedules if s.train_id == victim.id)
        idx = next((i for i, st in enumerate(sched.steps) if st.track_id == c.track_id), 0)
        holds[victim.id][idx] = _clamp(holds[victim.id][idx] + rnd.uniform(0.5, 6.0), p.max_hold_min)
        return
    # Random move: perturb or reset one hold
    t = rnd.choice(list(net.trains.values()))
    i = rnd.randrange(len(t.route) - 1)
    new = 0.0 if rnd.random() < 0.15 else holds[t.id][i] + rnd.gauss(0, 4)
    holds[t.id][i] = _clamp(new, p.max_hold_min)


def anneal(net: Network, ev: Evaluator, start: dict[str, list[float]], p: SolveParams):
    rnd = random.Random(p.seed)
    cur = copy.deepcopy(start)
    cur_e = ev.evaluate(cur)
    best, best_e = copy.deepcopy(cur), cur_e
    temp = p.start_temp
    history = []
    every = max(1, p.iterations // 200)

    for it in range(p.iterations):
        cand = copy.deepcopy(cur)
        _mutate(net, cand, cur_e, rnd, p)
        cand_e = ev.evaluate(cand)
        d = cand_e.fitness - cur_e.fitness
        if d < 0 or rnd.random() < math.exp(-d / max(temp, 1e-9)):
            cur, cur_e = cand, cand_e
            if cur_e.fitness < best_e.fitness:
                best, best_e = copy.deepcopy(cur), cur_e
        temp *= p.cooling
        if it % every == 0 or it == p.iterations - 1:
            history.append({"iter": it, "best": round(best_e.fitness, 2), "current": round(cur_e.fitness, 2),
                            "conflicts": len(cur_e.conflicts), "temp": round(temp, 3)})
    return best, best_e, history
