"""Run-diagnostics panel (D101). Six readouts, each mapped to a specific knob + action, so that a
run (pilot or full) is read as a DESIGN PROBE for the next run's parameter budget -- data-driven,
not eyeballed. Consumes the per-generation history rows that run_evolution produces (with the
component means, fit_std, dev_conv_frac, dev_abort_n that D096/D099/D101 added).

Usage:
    from ddescent.diagnostics import run_panel
    panel = run_panel(history_df)          # dict of readouts + implied actions
    print(format_panel(panel))             # human-readable block

The panel is deliberately conservative: it reports the readout, the implied knob, and a suggested
action, but does NOT auto-change anything. The scientist decides. Thresholds are defaults, tunable.
"""
from __future__ import annotations
import numpy as np


def _slope_last_k(y, k):
    """Least-squares slope of y over its last k points (per-generation units)."""
    y = np.asarray(y, float)
    if len(y) < 2:
        return 0.0
    k = min(k, len(y))
    yy = y[-k:]; xx = np.arange(k)
    return float(np.polyfit(xx, yy, 1)[0])


def cell_panel(df_cell, last_k=10, climb_eps=1e-4, std_collapse_frac=0.2,
               rise_eps=1e-3, conv_floor=0.8):
    """Compute the six D101 readouts for a SINGLE (P, seed) cell's history.

    df_cell: rows for one cell, columns include gen, fit_mean, fit_std, enc_mean, car_mean,
             reg_mean, dev_conv_frac, dev_abort_n. Must be sorted by gen.
    Returns a dict: each readout with its value, verdict, implied knob, and suggested action.
    """
    d = df_cell.sort_values("gen")
    g = d["gen"].values
    fit = d["fit_mean"].values
    fstd = d["fit_std"].values
    enc = d["enc_mean"].values; car = d["car_mean"].values; reg = d["reg_mean"].values

    # (1) fitness slope over last K gens -> gens
    slope = _slope_last_k(fit, last_k)
    still_climbing = slope > climb_eps
    d1 = dict(readout="fitness_slope_lastK", value=round(slope, 6),
              verdict="still climbing" if still_climbing else "plateaued",
              knob="gens", action=("INCREASE gens (fitness not saturated)" if still_climbing
                                    else "gens sufficient (plateaued) — can economize"))

    # (2) fit_std trajectory -> pop (premature convergence)
    std0 = float(np.mean(fstd[:max(1, len(fstd)//5)]))     # early-run mean std
    stdf = float(np.mean(fstd[-max(1, len(fstd)//5):]))    # late-run mean std
    collapsed = (std0 > 1e-9) and (stdf < std_collapse_frac * std0)
    d2 = dict(readout="fit_std_collapse", value=dict(early=round(std0, 5), late=round(stdf, 5)),
              verdict="premature convergence" if collapsed else "diversity retained",
              knob="pop", action=("INCREASE pop or mutation (diversity collapsed early)" if collapsed
                                  else "pop adequate (diversity retained)"))

    # (3) component emergence -> N or dev_ms
    def _rose(x):
        return (np.max(x) - x[0]) > rise_eps and _slope_last_k(x, last_k) > -abs(rise_eps)
    enc_rose, car_rose, reg_rose = _rose(enc), _rose(car), _rose(reg)
    cap_emerged = car_rose or reg_rose
    d3 = dict(readout="component_emergence",
              value=dict(enc_rose=bool(enc_rose), car_rose=bool(car_rose), reg_rose=bool(reg_rose),
                         enc_final=round(float(enc[-1]), 4), car_final=round(float(car[-1]), 4),
                         reg_final=round(float(reg[-1]), 4)),
              verdict=("capability (car/reg) emerged" if cap_emerged
                       else "capability did NOT emerge (encoding-only)"),
              knob="N / dev_ms",
              action=("capability building — good" if cap_emerged
                      else "car/reg never rose: suspect N too small OR dev_ms too short — "
                           "check diagnostic #4 first, then consider larger N"))

    # (4) development convergence fraction -> dev_ms
    conv = float(d["dev_conv_frac"].mean()) if "dev_conv_frac" in d else float("nan")
    conv_ok = conv >= conv_floor
    d4 = dict(readout="dev_convergence_fraction", value=round(conv, 3),
              verdict=("dev_ms sufficient" if conv_ok else "dev_ms TOO SHORT (immature phenotypes)"),
              knob="dev_ms", action=("dev_ms adequate" if conv_ok
                                     else "INCREASE dev_ms — scoring immature phenotypes undermines "
                                          "the develop-then-score premise (D083)"))

    # (6) numerical health -> inspect
    aborts = int(d["dev_abort_n"].sum()) if "dev_abort_n" in d else 0
    d6 = dict(readout="nan_abort_count", value=aborts,
              verdict="clean" if aborts == 0 else "NaN aborts occurred",
              knob="numerical health",
              action=("healthy" if aborts == 0 else "INSPECT — NaN tripwire fired; fix before scaling"))

    return dict(cell=dict(density=float(d["density"].iloc[0]) if "density" in d else None,
                          seed=int(d["seed"].iloc[0]) if "seed" in d else None),
                d1_gens=d1, d2_pop=d2, d3_components=d3, d4_dev_ms=d4, d6_numerical=d6)


def run_panel(df, last_k=10, **kw):
    """Full-run panel: per-cell readouts (1-4,6) PLUS the cross-cell P-dependence readout (#5).

    #5 asks whether capability emergence TRENDS with P (density) -- the first whisper of double-
    descent structure (the pilot doesn't resolve the curve; a monotone P-trend is the signal).
    """
    cells = []
    for (dens, seed), sub in df.groupby(["density", "seed"]):
        cells.append(cell_panel(sub, last_k=last_k, **kw))

    # (5) P-dependence of capability emergence -> the science
    by_P = df.groupby("density").apply(
        lambda s: float(s.sort_values("gen")["car_mean"].iloc[-1] +
                        s.sort_values("gen")["reg_mean"].iloc[-1])
    ).sort_index()
    Ps = [round(float(x), 3) for x in by_P.index.values]
    caps = by_P.values.astype(float)
    p_slope = float(np.polyfit(np.array(Ps), caps, 1)[0]) if len(Ps) >= 2 else 0.0
    monotone = bool(np.all(np.diff(caps) >= -1e-4)) or bool(np.all(np.diff(caps) <= 1e-4))
    d5 = dict(readout="P_dependence_of_capability", value=dict(
                  densities=Ps,
                  final_car_plus_reg=[round(float(x), 4) for x in caps], slope=round(p_slope, 5)),
              verdict=("capability TRENDS with P (double-descent whisper)" if abs(p_slope) > 1e-3 and monotone
                       else "no clean P-trend in capability"),
              knob="the science",
              action=("P-structure present — proceed to full run to resolve the curve"
                      if abs(p_slope) > 1e-3 else "no P-structure yet — may need more gens/N before "
                                                  "the effect appears, or the effect is absent"))
    return dict(per_cell=cells, d5_P_dependence=d5)


def format_panel(panel):
    """Human-readable diagnostic block for stdout/log (D101)."""
    L = ["=" * 70, "RUN DIAGNOSTICS PANEL (D101) — each readout -> knob -> action", "=" * 70]
    for cell in panel["per_cell"]:
        c = cell["cell"]
        L.append(f"\n[cell density={c['density']} seed={c['seed']}]")
        for key in ("d1_gens", "d2_pop", "d3_components", "d4_dev_ms", "d6_numerical"):
            r = cell[key]
            L.append(f"  {r['readout']:28s} [{r['knob']}]: {r['verdict']}")
            L.append(f"      -> {r['action']}")
    r5 = panel["d5_P_dependence"]
    L.append(f"\n[cross-cell] {r5['readout']} [{r5['knob']}]: {r5['verdict']}")
    L.append(f"    densities {r5['value']['densities']}")
    L.append(f"    final car+reg {r5['value']['final_car_plus_reg']} (slope {r5['value']['slope']})")
    L.append(f"    -> {r5['action']}")
    L.append("=" * 70)
    return "\n".join(L)
