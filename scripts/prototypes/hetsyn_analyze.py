"""hetsyn_analyze.py - re-analyse a persisted prototype run WITHOUT re-simulating.

This is what `save_results` was added for. The component-scaling run took ~4 hours; every question
below is arithmetic on its raw rows.

THREE CHECKS:

  1. SECOND-BEST CELL. Taking the maximum over a tau grid is upward-biased, and the bias grows with
     grid size -- P=3 searches 10 triples where P=1 searches 5 singles. If the SECOND-best P=m cell
     also beats the best P=m-1 cell, the diagonal is not one lucky configuration.

  2. HELD-OUT-SEED SELECTION. The principled fix for that bias: choose the tau configuration on one
     half of the seeds and REPORT it on the other half. The reported number is then unbiased by the
     selection. With 4 seeds this is thin (2 select, 2 report) but it is the right statistic, and a
     diagonal that survives it is considerably stronger than one that does not.

  3. PER-SEED CONSISTENCY. Does the diagonal appear in individual seeds, or only after averaging? D126's
     peak criterion requires a majority of individual seed curves to show the effect -- averaging can
     manufacture a shape that no single run exhibits.

Run:  python scripts/prototypes/hetsyn_analyze.py runs/prototypes/<timestamp>_component_scaling.json
"""
from __future__ import annotations
import argparse, json, sys
from collections import defaultdict
import numpy as np


def load(path):
    d = json.loads(open(path, encoding="utf-8").read())
    rows = d["rows"]
    # component_scaling rows: (m, P, taus, seed, acc);  stream_demand rows: (P, taus, lam, seed, acc)
    if d["name"] == "component_scaling":
        recs = [dict(m=r[0], P=r[1], taus=tuple(r[2]), seed=r[3], acc=r[4]) for r in rows]
    else:
        recs = [dict(m=r[2], P=r[0], taus=tuple(r[1]), seed=r[3], acc=r[4]) for r in rows]
    return d, recs


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("path")
    a = ap.parse_args()
    meta, recs = load(a.path)
    print("%s   (%d rows, meta=%s)\n" % (a.path, len(recs), meta.get("meta")))

    groups = defaultdict(lambda: defaultdict(list))     # groups[(m,P)][taus] = [acc per seed]
    seeds = sorted({r["seed"] for r in recs})
    for r in recs:
        groups[(r["m"], r["P"])][r["taus"]].append((r["seed"], r["acc"]))
    ms = sorted({m for m, _ in groups})
    Ps = sorted({P for _, P in groups})

    # ---- 1. best and SECOND-best ----------------------------------------------------------------
    print("1. BEST vs SECOND-BEST  (is the diagonal one lucky configuration?)")
    print("   m  |  P  | best              | 2nd best          | 2nd vs best of P-1")
    print("  ----+-----+-------------------+-------------------+--------------------")
    tops = {}
    for m in ms:
        for P in Ps:
            if (m, P) not in groups:
                continue
            ranked = sorted(((float(np.mean([a for _, a in v])), k) for k, v in groups[(m, P)].items()),
                            reverse=True)
            tops[(m, P)] = ranked
            b, b2 = ranked[0], (ranked[1] if len(ranked) > 1 else (float("nan"), ()))
            cmp_s = ""
            if (m, P - 1) in tops:
                prev = tops[(m, P - 1)][0][0]
                cmp_s = "%+.3f %s" % (b2[0] - prev, "OK" if b2[0] > prev else "FAILS")
            print("   %d  |  %d  | %.3f %-11s | %.3f %-11s | %s"
                  % (m, P, b[0], str(tuple(int(t) for t in b[1])),
                     b2[0], str(tuple(int(t) for t in b2[1])), cmp_s))
        print("  ----+-----+-------------------+-------------------+--------------------")

    # ---- 2. held-out-seed selection --------------------------------------------------------------
    half = len(seeds) // 2
    sel_s, rep_s = set(seeds[:half]), set(seeds[half:])
    print("\n2. HELD-OUT-SEED SELECTION  (tau chosen on seeds %s, reported on seeds %s)"
          % (sorted(sel_s), sorted(rep_s)))
    print("   m  |  P  | chosen taus          | reported | gain vs P-1")
    print("  ----+-----+----------------------+----------+------------")
    ho = {}
    for m in ms:
        prev = None
        for P in Ps:
            if (m, P) not in groups:
                continue
            best_k, best_v = None, -np.inf
            for k, v in groups[(m, P)].items():
                sv = [a for s, a in v if s in sel_s]
                if sv and np.mean(sv) > best_v:
                    best_k, best_v = k, float(np.mean(sv))
            rv = [a for s, a in groups[(m, P)][best_k] if s in rep_s]
            rep = float(np.mean(rv)) if rv else float("nan")
            ho[(m, P)] = rep
            g = "    --   " if prev is None else "%+.3f   " % (rep - prev)
            print("   %d  |  %d  | %-20s |  %.3f   | %s"
                  % (m, P, str(tuple(int(t) for t in best_k)), rep, g))
            prev = rep
        print("  ----+-----+----------------------+----------+------------")

    # ---- 3. per-seed consistency -----------------------------------------------------------------
    print("\n3. PER-SEED CONSISTENCY  (does the diagonal appear in INDIVIDUAL seeds?)")
    print("   m  | seeds where the largest gain lands at P=m")
    for m in ms:
        hits = 0
        for s in seeds:
            per_P = {}
            for P in Ps:
                if (m, P) not in groups:
                    continue
                per_P[P] = max(a for k, v in groups[(m, P)].items() for sd, a in v if sd == s)
            gains = {P: per_P[P] - per_P[P - 1] for P in per_P if P - 1 in per_P}
            if gains and max(gains, key=lambda k: gains[k]) == m:
                hits += 1
        print("   %d  | %d of %d%s" % (m, hits, len(seeds),
                                        "   (m=1 cannot hit: no P=0 to gain over)" if m == 1 else ""))

    print("\nREAD: the diagonal is solid if (1) second-best still clears the previous P, (2) held-out")
    print("selection preserves the gain at P=m, and (3) a majority of individual seeds show it (D126).")


if __name__ == "__main__":
    main()
