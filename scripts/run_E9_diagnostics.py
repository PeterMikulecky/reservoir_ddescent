#!/usr/bin/env python3
r"""
E9 DIAGNOSTICS — the five measurements that come before any more compute.

**Why this exists.** D067 read Gate B0's failure as an evaluation-budget problem and proposed
shrinking N. D068 killed that: cost is TIMESTEP-dominated, so N was never the lever. D069 killed
the other reading: `baseline == memoryless_floor` is an IDENTITY, so "the states never beat the
baseline" was never evidence the network is broken — it is what a network with no context
inference must look like. **Both readings were wrong, and neither was measured.** This script
measures, at ~5 min of compute, before anything expensive is built.

**The question this actually asks.** `hierarchical_environments` puts context in the COVARIANCE
across `context_dwell`=10 stimuli (D048). At `present_ms`=150 that is a **1,500 ms** regularity.
The substrate's dynamical memory is **tau_m = 20 ms**. (Note tau_r=30 ms is the READOUT FILTER,
not network state: `r` appears in no other equation.) So the task needs 75x the substrate's
single-neuron memory, and the only route is recurrent collective modes.

**And the timing parameters were never chosen for this.** `present_ms`=150, `readout_window_ms`=60
and every tau are IDENTICAL to `ReservoirConfig` — inherited across D032 untouched. Their
rationale, in `reservoir.py`'s own words: *"With present_ms >> tau_r, cross-pattern carryover
fades, so order effects are small."* **Carryover-fading was the DESIGN GOAL.** D048 then made
carryover the mechanism. Nobody revisited the engine. Measurements 3 and 4 are that audit.

THE FIVE
--------
1. **decode E from `state`, and from `rates`** — D030's ACTUAL gate, which has never been run
   (D069: `skill()` and `raw_input_baseline()` take the retired `TaskData` API and would raise on
   a `HierarchicalTask`; the gate was unreachable, not skipped). `rates` matters separately:
   fitness reads the LAST d OF N neurons. A random W may encode E in the state and never ROUTE it
   to the output slice. **That is Gate A, sharpened** — it separates "the encoder is broken" from
   "the encoder works and nothing reaches fitness".
2. **PR_mean vs PR_var** — `FRAMING.md` sec.3 justifies the SPIKING SUBSTRATE on exactly one
   finding of our own: PR_mean compresses (~7.4 of K=20), PR_var expands (~27), and PR_var
   predicts generalization while PR_mean anti-predicts it. **That is D028/D033 — N=1000 reservoir,
   `anisotropic_regression`, trained readout: all four retired by D032/sec.2c, in the same session
   sec.3 was written.** It has never been measured on `evonet`. If it does not transfer, sec.3
   needs rewriting and H-E loses its footing. Free: `behave()` already returns both channels.
3. **memory vs delay** — reconstruct E(t-k) from `state(t)`. The timescale audit, quantitatively.
4. **carryover** — present the SAME stimuli in shuffled order; does `state` for a given E change?
   **Controlled against a fresh-noise replicate**, because `noise_sigma` > 0 means identical runs
   already differ. ratio ~= 1 => no carryover beyond noise => no context inference is possible.
5. **decode context from `state`** — `BRIDGE.md` Level 5 lists this and it has NEVER been run.
   Chance = 1/n_contexts. **Is the system doing Level 2(iii) at all?**

Measurements 1-2 are one call each; 3-5 are new. None need PROTOCOLS.md's Protocol S/T framework
(reservoir-era, retired) — they are built because the questions are right, not because a retired
document promised them.

THE GRID
--------
gain x noise_sigma. Gate C chose bias=0.6, **gain=1.0**, noise=1.0 on CV_ISI alone — and D069
showed that is the WORST cell for encoding (0.935/0.993 ~= predicting the mean). Gate C repeated
D030's error one level up: **CV_ISI ~= 1 MEANS fluctuation-dominated MEANS input-subordinate.**
The objectives are in opposition, so the operating point must be chosen on BOTH.
*Not measured here:* CV_ISI, which needs a SpikeMonitor in `behave()`. **This grid is Gate C v2's
skill axis; adding the CV_ISI axis is the next step, and the pair is what selects an operating
point that is both fluctuation-driven and input-encoding. If no such cell exists, H-D is
unrunnable — and that is a finding about the substrate, not a design failure.*

Usage:
  python scripts\run_E9_diagnostics.py                 # the full grid (~5 min)
  python scripts\run_E9_diagnostics.py --quick         # gate C's point + gain=10, ~2 min
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

import argparse
import itertools
import time

import numpy as np
import pandas as pd

from ddescent import provenance as P
from ddescent import tasks as T
from ddescent.evonet import EvoNetConfig, EvoNet, random_genome
from ddescent.baseline import best_nmse
from ddescent.readout import LinearReadout, one_hot
from ddescent.metrics import spectrum, pr_from_spectrum
from ddescent.measures import participation_ratio

# House convention (baseline.ALPHA_GRID): report the BEST achievable test error over a ridge
# grid, so a comparison is about representational quality rather than tuning luck. That does
# select alpha on the test set — acceptable here because every condition gets the same
# advantage and we are comparing conditions, not estimating a generalization bound.
ALPHAS = (1e-2, 1e-1, 1e0, 1e1, 1e2, 1e3, 1e4)


def _zs(Xtr, others):
    """Z-score by TRAIN stats, with an sd floor (near-silent units otherwise blow up)."""
    mu = Xtr.mean(0, keepdims=True)
    sd = np.maximum(Xtr.std(0, keepdims=True), 1e-3 * (Xtr.std(0).mean() + 1e-12))
    return (Xtr - mu) / sd, [(X - mu) / sd for X in others]


def decode_nmse(Xtr, Ytr, Xte, Yte) -> float:
    """Best test NMSE reconstructing Y from X. 1.0 == predicting the mean == no information."""
    return float(best_nmse(Xtr, Ytr, Xte, Yte, alphas=ALPHAS, standardize=True)[0])


def decode_acc(Xtr, ytr, Xte, yte, n_classes: int) -> float:
    """Best test accuracy classifying y from X, over the ridge grid."""
    A, (B,) = _zs(Xtr, [Xte])
    Ytr = one_hot(ytr, n_classes)
    best = 0.0
    for a in ALPHAS:
        try:
            r = LinearReadout(alpha=a).fit(A, Ytr)
            best = max(best, float((np.argmax(r.predict(B), axis=1) == yte).mean()))
        except Exception:
            continue
    return best


def memory_curve(Str, Ste, Etr, Ete, max_delay: int = 6) -> dict:
    """Reconstruct E(t-k) from state(t), for k = 0..max_delay. Jaeger memory capacity in spirit.

    k=0 is measurement 1 (does the state encode the CURRENT stimulus). k>=1 is memory. Context
    inference needs k up to `context_dwell` = 10 — so if this is at 1.0 by k=1, the substrate is
    not doing it, and no evaluation budget changes that.
    """
    out = {}
    for k in range(max_delay + 1):
        if k == 0:
            a, b, c, d = Str, Etr, Ste, Ete
        else:
            a, b, c, d = Str[k:], Etr[:-k], Ste[k:], Ete[:-k]
        out[k] = decode_nmse(a, b, c, d)
    return out


def carryover(net, E, state_ref, rng) -> tuple:
    """Does the response to a given stimulus depend on what preceded it?

    Present the SAME stimuli in shuffled order and compare state for the same E. If the network
    is memoryless, `state` for stimulus j is identical either way.

    **The control is essential.** `noise_sigma` > 0 means two identical runs already differ, so a
    raw difference proves nothing. We therefore also run the ORIGINAL order with fresh noise and
    report the RATIO. ratio ~= 1 => order changes nothing beyond noise => NO carryover => context
    inference is impossible => the environment's second level is unreachable by construction.

    *(This is PROTOCOLS.md's `order_dependence` with the sign flipped. There it was an ARTIFACT
    CHECK — memory contaminating a stationary measurement. Under D048 carryover IS the mechanism.
    Same measurement, opposite meaning.)*
    """
    n = E.shape[0]
    perm = rng.permutation(n)
    s_shuf = net.behave(E[perm])["state"]          # response to E[perm[i]] in shuffled context
    s_ctl = net.behave(E)["state"]                 # original order, fresh noise: the floor
    d_order = float(np.abs(s_shuf - state_ref[perm]).mean())
    d_noise = float(np.abs(s_ctl - state_ref).mean())
    return d_order, d_noise, d_order / max(d_noise, 1e-12)


def one_cell(gain: float, sigma: float, pos: str, nmda_frac: float, task, args, rng) -> dict:
    net_cfg = EvoNetConfig(N=args.N, n_in=args.K, d=args.d, bias=args.bias,
                           input_gain=gain, noise_sigma=sigma, readout_pos=pos,
                           nmda_frac=nmda_frac, present_ms=args.present_ms,
                           readout_window_ms=min(args.readout_window_ms, args.present_ms * 0.4))
    g = random_genome(net_cfg, args.density, w0=args.w0, seed=args.seed)
    net = EvoNet(g, net_cfg)

    Btr, Bte = net.behave(task.E_train), net.behave(task.E_test)
    Str, Ste = Btr["state"], Bte["state"]

    row = dict(input_gain=gain, noise_sigma=sigma, readout_pos=pos, nmda_frac=nmda_frac,
               present_ms=args.present_ms, n_params=g.n_params())

    # --- 1. does the state encode E? and does it REACH the output neurons? ----------
    row["E_from_state"] = decode_nmse(Str, task.E_train, Ste, task.E_test)
    row["E_from_rates"] = decode_nmse(Btr["rates"], task.E_train, Bte["rates"], task.E_test)

    # --- 2. FRAMING sec.3: does the channel dissociation transfer to evonet? --------
    row["pr_mean"] = pr_from_spectrum(spectrum(Str))
    row["pr_var"] = pr_from_spectrum(spectrum(Btr["state_var"]))
    row["pr_input"] = participation_ratio(task.E_train)

    # --- 3. the timescale audit ------------------------------------------------------
    mem = memory_curve(Str, Ste, task.E_train, task.E_test, max_delay=args.max_delay)
    for k, v in mem.items():
        row[f"mem_d{k}"] = v
    # capacity: sum of explained variance over delays >= 1, clipped. 0 => no usable memory.
    row["memory_capacity"] = float(sum(max(0.0, 1.0 - mem[k]) for k in mem if k >= 1))

    # --- 4. carryover, controlled against the noise floor ----------------------------
    d_o, d_n, ratio = carryover(net, task.E_train, Str, rng)
    row.update(order_delta=d_o, noise_delta=d_n, order_over_noise=ratio)

    # --- 5. is the memory USEFUL? ----------------------------------------------------
    row["context_acc"] = decode_acc(Str, task.C_train, Ste, task.C_test,
                                    task.meta["n_contexts"])
    row["context_chance"] = 1.0 / task.meta["n_contexts"]
    return row


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--N", type=int, default=50)
    ap.add_argument("--K", type=int, default=10)
    ap.add_argument("--d", type=int, default=5)
    ap.add_argument("--n-env", type=int, default=200,
                    help="diagnostics only, NOT the GA: more samples than state dims so the "
                         "decodes are well-posed. Costs one behave() call, not a GA arm.")
    ap.add_argument("--density", type=float, default=0.3)   # Gate C's operating point
    ap.add_argument("--w0", type=float, default=0.6)        # Gate C's operating point
    ap.add_argument("--bias", type=float, default=0.6)      # Gate C's operating point
    ap.add_argument("--max-delay", type=int, default=10,
                    help="D074: gate is movement past d1 (d2-d3), not d10. d10 needs an EVOLVED "
                         "attractor (Wang slow reverberation); demanding it from a random net "
                         "demands the answer before the experiment. Kept at 10 to SEE the shape.")
    ap.add_argument("--nmda-frac", default="0,0.3,0.5,0.8",
                    help="D074: comma-separated sweep. 0.0 = today's model (REQUIRED control: "
                         "must reproduce mem_d1=1.000). Wang recurrent exc is NMDA-dominated, so "
                         "0.8 is the literature high end.")
    ap.add_argument("--present-ms", type=float, default=50.0,
                    help="D073: 150->50 shortens the span memory must cross AND is D068's 3x "
                         "compute win. The one lever that is both a fix and a speedup.")
    ap.add_argument("--readout-window-ms", type=float, default=60.0,
                    help="capped at 0.4*present_ms inside one_cell so the window fits the "
                         "presentation (at present_ms=50 -> 20 ms).")
    ap.add_argument("--readout-pos", choices=("both", "trailing", "leading"), default="both",
                    help="rung 1: 'trailing' is the inherited default (read after ~4.5 tau_m of "
                         "settling); 'leading' reads the onset, where carryover lives.")
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    args = ap.parse_args()

    gains = (10.0,) if args.quick else (3.0, 10.0)     # D069: gain=1 is the worst cell; drop it
    sigmas = (0.2,) if args.quick else (0.2, 1.0)
    nmdas = tuple(float(x) for x in args.nmda_frac.split(","))
    # RUNG 1 (D072): readout POSITION is now an axis. mem_d1 = 1.000 in all 8 trailing cells
    # has two readings -- memory absent, or memory unread. Running both positions on the SAME
    # grid separates them in one pass. 'trailing' is the inherited default; every number in the
    # first diagnostics run is a trailing number.
    # D074: with the slow current in play, TRAILING is the right readout again -- we WANT the
    # settled response now that memory can persist through it. leading was a rung-1 diagnostic.
    positions = (args.readout_pos,) if args.readout_pos != "both" else ("trailing",)

    task_kw = dict(K=args.K, d=args.d, r1=3, n_contexts=4, n_train=args.n_env,
                   n_test=args.n_env, context_dwell=10, seed=args.seed)

    run = P.new_run("E9", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=dict(task=task_kw,
                                grid=dict(gains=gains, sigmas=sigmas, positions=positions,
                                          nmda_frac=nmdas, present_ms=args.present_ms),
                                net=vars(args)),
                    tag="nmda-sweep", seeds=[args.seed],
                    notes="E9 diagnostics: encode/route, PR channels, memory, carryover, context")
    print(f"run: {run.run_id}")
    # D072: mirror everything below into logs/run.log. NAMING.md sec.3 has specified
    # that file since the scaffold and nothing ever wrote to it -- every verdict these
    # scripts print was lost on terminal close. finalize() closes it, on both paths.
    run.start_log()
    # D072: mirror everything below into logs/run.log. NAMING.md sec.3 has specified
    # that file since the scaffold; nothing ever wrote to it, so every verdict this
    # script prints has been lost on terminal close while data/*.parquet survived.
    run.start_log()
    try:
        task = T.hierarchical_environments(**task_kw)
        hr = task.headroom()                     # D057: required pre-run check
        print(f"task: constraints={task.n_constraints()}  "
              f"memoryless_floor={hr['memoryless_floor']:.3f}  "
              f"oracle={hr['oracle_ceiling']:.3f}  headroom={hr['headroom']:.3f}")
        print(f"      mean_separation={task.meta['mean_separation']:.4f} "
              f"(D048: contexts differ in COVARIANCE only; this must be ~0)")
        print(f"      context timescale = {10 * 150} ms vs tau_m = 20 ms  -> 75x\n")

        cells = list(itertools.product(gains, sigmas, positions, nmdas))
        # D068's rule: NAME the quantity cost scales with. It is TIMESTEPS.
        # 113 us/timestep is D065's 3.4 s/eval divided by its 30,000 timesteps, serial.
        n_steps = len(cells) * 4 * args.n_env * 150 / 0.5     # 4 behave() calls per cell
        print(f"{len(cells)} cells x 4 behave() = {n_steps:,.0f} timesteps "
              f"~ {n_steps * 113e-6 / 60:.1f} min at 113 us/step (measured, D065/D068).")
        print(f"Cost is ~FLAT in N and |W| -- that is why shrinking N never helped.\n")

        rng = np.random.default_rng(args.seed)
        rows = []
        for i, (gain, sigma, pos, nf) in enumerate(cells):
            t0 = time.time()
            rows.append(one_cell(gain, sigma, pos, nf, task, args, rng))
            r = rows[-1]
            print(f"  [{i+1}/{len(cells)}] gain={gain:<4g} sig={sigma:<4g} nmda={nf:<4g} "
                  f"E|state={r['E_from_state']:.3f} E|rates={r['E_from_rates']:.3f} "
                  f"d1={r['mem_d1']:.3f} d2={r['mem_d2']:.3f} d3={r['mem_d3']:.3f} "
                  f"MC={r['memory_capacity']:.2f} ctx={r['context_acc']:.2f}  "
                  f"({time.time()-t0:.0f}s)", flush=True)

        df = pd.DataFrame(rows)
        df.to_parquet(run.table_path("diagnostics"))

        # ------------------------------------------------------------------ verdicts
        base = hr["memoryless_floor"]
        print(f"\n=== 1. DOES THE STATE ENCODE E, AND DOES IT REACH FITNESS? ===")
        print(f"    (NMSE reconstructing E. 1.0 = no information. This is D030's ACTUAL gate,")
        print(f"     which has never been run: skill() takes the retired TaskData API — D069.)")
        print(f"{'gain':>6} {'sigma':>6} {'pos':>9} {'E|state':>9} {'E|rates':>9}  routed?")
        for _, r in df.iterrows():
            routed = "YES" if r.E_from_rates < 0.9 else ("state only" if r.E_from_state < 0.9 else "-")
            print(f"{r.input_gain:>6g} {r.noise_sigma:>6g} {r.readout_pos:>9} "
                  f"{r.E_from_state:>9.3f} {r.E_from_rates:>9.3f}  {routed}")
        enc = df.E_from_state.min()
        print(f"  best E|state = {enc:.3f} -> encoder "
              f"{'WORKS' if enc < 0.5 else 'DEGRADED' if enc < 0.9 else 'CARRIES NOTHING'}")
        if df.E_from_state.min() < 0.5 <= df.E_from_rates.min():
            print("  !! E is in the STATE but not in the RATES: the encoder works and nothing")
            print("     reaches fitness. Gate A is a ROUTING problem, and selection's job.")

        print(f"\n=== 2. DOES FRAMING sec.3 TRANSFER? (PR_mean compresses, PR_var expands) ===")
        print(f"    reservoir era, D028/D033 at K=20: PR_mean~7.4 (compress), PR_var~27 (expand).")
        print(f"    Here K={args.K}, input PR = {df.pr_input.iloc[0]:.2f}.")
        print(f"{'gain':>6} {'sigma':>6} {'pos':>9} {'PR_in':>6} {'PR_mean':>9} {'PR_var':>9}")
        for _, r in df.iterrows():
            print(f"{r.input_gain:>6g} {r.noise_sigma:>6g} {r.readout_pos:>9} "
                  f"{r.pr_input:>6.2f} {r.pr_mean:>9.2f} {r.pr_var:>9.2f}")
        # D072: "PR_var > PR_mean" is NOT the sec.3 claim and my first verdict over-claimed it.
        # sec.3's striking half is that the MEAN channel COMPRESSES (7.4 from K=20 inputs).
        # Run 1: PR_input 5.86 -> PR_mean 7.00 = mild EXPANSION. Compression did NOT transfer.
        # And PR_var tracks sigma (12-14 at 0.2, 23-34 at 1.0) -- much of "var expands" is the
        # dimensionality of INJECTED NOISE. D028's real claim is that PR_var PREDICTS
        # generalization while PR_mean anti-predicts it. That needs generalization measured
        # across conditions and is NOT tested here. Reported, not adjudicated.
        print(f"  PR_mean vs PR_input: "
              f"{'COMPRESSES (sec.3 transfers)' if df.pr_mean.min() < df.pr_input.iloc[0] else 'EXPANDS -- sec.3 compression does NOT transfer'}")
        print(f"  NOTE: PR_var tracks noise_sigma, so 'var expands' is partly the dimensionality")
        print(f"        of injected noise. sec.3 rests on PREDICTION, which this does not test.")
        if (df.pr_var > df.pr_mean).mean() < 0.5:
            print("  !! The channel dissociation does NOT transfer to evonet. FRAMING sec.3's")
            print("     ONLY substrate-specific justification is a retired-model result.")

        print(f"\n=== 3-4. THE TIMESCALE AUDIT ===")
        print(f"    present_ms=150, tau_m=20 (tau_r=30 is the READOUT FILTER, not state).")
        print(f"    Context needs memory over context_dwell=10 presentations = 1500 ms.")
        dcols = [c for c in df.columns if c.startswith("mem_d")]
        print(f"{'gain':>6} {'sigma':>6} {'pos':>9} " + " ".join(f"{c:>7}" for c in dcols) +
              f" {'MC':>6} {'ord/noise':>10}")
        for _, r in df.sort_values(["readout_pos", "input_gain", "noise_sigma"]).iterrows():
            print(f"{r.input_gain:>6g} {r.noise_sigma:>6g} {r.readout_pos:>9} " +
                  " ".join(f"{r[c]:>7.3f}" for c in dcols) +
                  f" {r.memory_capacity:>6.2f} {r.order_over_noise:>10.2f}")
        mc = df.memory_capacity.max()
        print(f"  best memory capacity over delays>=1: {mc:.2f}")
        print(f"  max order/noise ratio: {df.order_over_noise.max():.2f} "
              f"(~1.0 => order changes nothing beyond noise)")
        if mc < 0.1 and df.order_over_noise.max() < 1.2:
            print("  !! NO USABLE MEMORY AND NO CARRYOVER.")
            print("     present_ms=150 = 5*tau_r was inherited from reservoir.py, whose docstring")
            print("     states the intent: 'With present_ms >> tau_r, cross-pattern carryover")
            print("     fades.' D048 then made carryover the MECHANISM. The engine is still")
            print("     configured to prevent the thing the task requires.")
            print("     -> D067 was NEVER about the evaluation budget.")

        print(f"\n=== 5. IS THE MEMORY USEFUL? (context decode; BRIDGE L5, never run) ===")
        print(f"{'gain':>6} {'sigma':>6} {'pos':>9} {'ctx_acc':>9} {'chance':>7}")
        for _, r in df.iterrows():
            print(f"{r.input_gain:>6g} {r.noise_sigma:>6g} {r.readout_pos:>9} "
                  f"{r.context_acc:>9.3f} {r.context_chance:>7.2f}")
        ca, ch = df.context_acc.max(), df.context_chance.iloc[0]
        print(f"  best = {ca:.3f} vs chance {ch:.2f} -> "
              f"{'context IS recoverable' if ca > ch + 0.15 else 'AT CHANCE'}")

        # -------------------------------------------------- D074: the NMDA sweep verdict
        if len(nmdas) > 1:
            print(f"\n=== D074: DOES SLOW EXCITATORY CURRENT BUY MEMORY PAST d1? ===")
            print(f"    present_ms={args.present_ms:g}, tau_slow=100 ms. Gate = d2-d3 MOVEMENT in a")
            print(f"    RANDOM net (d10 is selection's job -- Wang slow reverberation needs an")
            print(f"    EVOLVED attractor). Watch the ENCODING COST: D030's opposition, again.")
            agg = (df.groupby("nmda_frac")
                     .agg(d1=("mem_d1","min"), d2=("mem_d2","min"), d3=("mem_d3","min"),
                          MC=("memory_capacity","max"), E_state=("E_from_state","min"),
                          E_rates=("E_from_rates","min"), ctx=("context_acc","max"))
                     .reset_index())
            print(f"{'nmda':>6} {'best_d1':>8} {'best_d2':>8} {'best_d3':>8} {'MC':>6} "
                  f"{'E|state':>8} {'E|rates':>8} {'ctx':>6}")
            for _, r in agg.iterrows():
                print(f"{r.nmda_frac:>6g} {r.d1:>8.3f} {r.d2:>8.3f} {r.d3:>8.3f} {r.MC:>6.2f} "
                      f"{r.E_state:>8.3f} {r.E_rates:>8.3f} {r.ctx:>6.3f}")
            ctrl = agg[agg.nmda_frac == 0.0]
            if len(ctrl) and ctrl.d1.iloc[0] < 0.95:
                print(f"  !! CONTROL BROKEN: nmda_frac=0 gives d1={ctrl.d1.iloc[0]:.3f}, not ~1.0.")
                print(f"     The new current path has a bug -- fix before reading anything else.")
            else:
                print(f"  control OK: nmda_frac=0 reproduces the memoryless result (d1~1.0).")
            best = agg[agg.nmda_frac > 0]
            moved = best.d2.min() < 0.9 if len(best) else False
            print(f"  slow current moves memory past d1: "
                  f"{'YES -- the capability is real, selection has a foothold' if moved else 'NO'}")
            if moved:
                worst_cost = (best.loc[best.d2.idxmin(), "E_state"]
                              - ctrl.E_state.iloc[0]) if len(ctrl) else float('nan')
                print(f"     encoding cost at that cell: E|state worsens by {worst_cost:+.3f}")
                print(f"     (D030's opposition -- weigh memory gained vs level-1 lost)")

        # ------------------------------------------------------ RUNG 1: the fork (only if swept)
        if len(positions) > 1:
            tr = df[df.readout_pos == "trailing"]
            le = df[df.readout_pos == "leading"]
            print(f"\n=== RUNG 1: IS THE MEMORY ABSENT, OR UNREAD? ===")
            print(f"    trailing reads after ~4.5 tau_m of settling; leading reads the onset.")
            print(f"    Arithmetic: averaging exp(-t/tau_m) over a 60 ms leading window retains")
            print(f"    ~32% of the previous stimulus. If mem_d1 does not move, it is not there.")
            print(f"{'':>10} {'best mem_d1':>12} {'best MC':>9} {'max ord/noise':>14} {'best E|state':>13}")
            for nm, sub in (("trailing", tr), ("leading", le)):
                print(f"{nm:>10} {sub.mem_d1.min():>12.3f} {sub.memory_capacity.max():>9.2f} "
                      f"{sub.order_over_noise.max():>14.2f} {sub.E_from_state.min():>13.3f}")
            moved = (tr.mem_d1.min() - le.mem_d1.min())
            print(f"\n  mem_d1 improvement, trailing -> leading: {moved:+.3f}")
            if le.mem_d1.min() < 0.95:
                print("  -> THE MEMORY IS THERE AND WE WERE NOT LOOKING AT IT.")
                print("     The inherited trailing window (reservoir.py: 'present_ms >> tau_r,")
                print("     cross-pattern carryover fades') was doing exactly what it was")
                print("     designed to do. This is a MEASUREMENT fix, not a design fix.")
                print("     BUT: it buys d1-d2, NEVER d10. exp(-1500/30) = 0 at any position.")
                print("     Spanning context_dwell=10 still needs heterogeneous tau_m.")
            else:
                print("  -> THE MEMORY IS GENUINELY ABSENT. Window position is not the problem.")
                print("     A random W at tau_m=20 builds no collective mode outlasting 150 ms.")
                print("     -> the fix is a DESIGN change: fixed-heterogeneous tau_m, DRAWN not")
                print("        evolved (D038: a capability, not a route). D059 tiers tau_m as an")
                print("        'alternative route that could BYPASS regulation' -- but a slow")
                print("        neuron gives a running AVERAGE, i.e. DRIVE, and tasks.py says an")
                print("        additive signal 'can only SHIFT the output, never change the E->Y")
                print("        mapping'. So tau_m is not regulation's ALTERNATIVE, it is its")
                print("        PREREQUISITE -- and Arm 1 as specified has ZERO routes, not one.")

        print(f"\n=== WHAT THIS DECIDES ===")
        print(f"  memoryless floor {base:.3f} == the raw-input baseline BY IDENTITY (D069):")
        print(f"  'beats baseline' == 'infers context' == the whole experiment. So the only")
        print(f"  question that matters here is whether the substrate CAN hold context at all.")
        if ca <= ch + 0.15:
            print("  -> Context is NOT recoverable from a random network's state. Next: is that")
            print("     because selection hasn't acted (Gate A's premise), or because the")
            print("     timing parameters forbid it? Measurement 3-4 separates those, and the")
            print("     fix is fixed-heterogeneous tau_m (drawn, not evolved -- a CAPABILITY,")
            print("     not a route: it gives step 1 without handing evolution a shortcut).")

        note = (f"rung1: best mem_d1 trailing="
                f"{df[df.readout_pos=='trailing'].mem_d1.min() if 'trailing' in set(df.readout_pos) else float('nan'):.3f} "
                f"leading="
                f"{df[df.readout_pos=='leading'].mem_d1.min() if 'leading' in set(df.readout_pos) else float('nan'):.3f}; "
                f"E|state={enc:.3f} E|rates={df.E_from_rates.min():.3f}; "
                f"PR_in={df.pr_input.iloc[0]:.2f} PR_mean_min={df.pr_mean.min():.2f}; "
                f"MC={mc:.2f}; ord/noise={df.order_over_noise.max():.2f}; ctx={ca:.2f}/{ch:.2f}")
        run.finalize(status="complete", n_conditions=len(df), notebook_note=note)
    except Exception as e:
        run.finalize(status="failed", error=str(e)); raise


if __name__ == "__main__":
    main()
