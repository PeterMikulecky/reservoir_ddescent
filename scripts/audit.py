"""AUDIT — does the pipeline measure what it claims, and do its premises hold?

WHY THIS EXISTS. In a single session seven significant defects were found, all by INSPECTION rather than
by running anything:
  D112  "encoding" and "regulation" were the same measurement offset by a constant
  D113  fitness was computed from TEST error (selection optimised the reported quantity)
  D116  the "memoryless floor" measured representational CAPACITY, not memorylessness
  D115  n_assays=1 gave fitness reliability ~0.05 (selection on approximately pure noise)
  ---   dev_ms=800 exposed development to 27% of stimuli, 2 of 4 contexts, ONE transition
  ---   d=3 collapsed the low-rank waist (r1 == min(K,d)), making H-B untestable
  D117  spectral radius ~5x supercritical, never measured or controlled

Three of those are the SAME failure (a quantity not measuring what its name claims) and three more are
parameters set once and never revisited against what the science requires. The common thread: nothing in
the codebase ever CHECKED ITS OWN PREMISES. This script does.

It supersedes preflight.py (whose five checks are included here as groups A/B/E/F).

GROUPS
  A  FITNESS PROVENANCE   destroy each split; confirm fitness moves iff it should.
  B  MEASUREMENT IDENTITY does each named quantity measure what its name claims?
  C  TASK INVARIANTS      do the design properties the hypotheses depend on actually hold?
  D  EXPOSURE COHERENCE   does development actually see what it must?
  E  CONFIG COHERENCE     are the parameters mutually consistent with what the science requires?
  F  RELIABILITY & POWER  is the fitness signal measurable, and does the network beat random?

Usage:  python audit.py [--fast] [--n 12] [--assays 4]
        --fast skips the groups that require simulation (A, B-partial, F).
Exit status 0 if no FAIL, 1 otherwise — so it can gate a launch script.
"""
import sys, argparse, pathlib, inspect
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, warnings
warnings.filterwarnings("ignore")
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig, EvoNet, random_genome
from ddescent.evolve import (EvolveConfig, evaluate, _fitness, _affine_nmse,
                             context_destroyed_score)
from ddescent.baseline import best_nmse
from ddescent import tasks as T

PASS, FAIL, WARN = "PASS", "FAIL", "WARN"
RESULTS = []


def rec(group, name, status, detail):
    RESULTS.append((group, name, status, detail))
    print(f"  [{status}] {name}: {detail}")


# =============================================================================================
# A. FITNESS PROVENANCE — destroy each split; fitness must move iff that split legitimately feeds it
# =============================================================================================
def group_A(task, net_cfg, cfg):
    print("\nA. FITNESS PROVENANCE — which splits actually influence fitness?")
    g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=1)

    def fit():
        r = evaluate(g, task, net_cfg, cfg)
        return _fitness(r, r["n_params"], cfg)

    base = fit()
    rng = np.random.default_rng(0)
    for split, attr, should_move in [("TEST", "Y_test", False),
                                     ("VAL", "Y_val", True),
                                     ("TRAIN", "Y_train", True)]:
        backup = getattr(task, attr)
        if backup is None:
            rec("A", f"A {split} split", WARN, "split absent"); continue
        setattr(task, attr, rng.normal(size=backup.shape) * 10.0)
        moved = abs(fit() - base) > 1e-12
        setattr(task, attr, backup)
        ok = (moved == should_move)
        detail = (f"destroying {split} {'changed' if moved else 'did NOT change'} fitness "
                  f"(expected {'change' if should_move else 'no change'})")
        if split == "TEST" and moved:
            detail += "  <-- TEST LEAKAGE: selection optimises the reported quantity (D113)"
        rec("A", f"A {split} split", PASS if ok else FAIL, detail)


# =============================================================================================
# B. MEASUREMENT IDENTITY — does each named quantity measure what its name claims?
# =============================================================================================
def group_B(task, net_cfg, cfg, n, fast=False):
    print("\nB. MEASUREMENT IDENTITY — do named quantities measure what they claim?")
    # B1: static random expansion vs the "memoryless" floor (D116)
    ht = task.headroom(split="test")
    rng = np.random.default_rng(0)
    Wr = rng.normal(size=(task.E_train.shape[1], net_cfg.N)) / np.sqrt(task.E_train.shape[1])
    Ftr, Fte = np.tanh(task.E_train @ Wr), np.tanh(task.E_test @ Wr)
    static = float(np.mean([best_nmse(Ftr, task.Y_train[:, k], Fte, task.Y_test[:, k],
                                      standardize=False)[0] for k in range(task.Y_train.shape[1])]))
    if static < ht["memoryless_floor"]:
        rec("B", "B1 memoryless floor", FAIL,
            f"a STATIC context-free random {net_cfg.N}-dim expansion scores {static:.4f}, beating the "
            f"'memoryless floor' {ht['memoryless_floor']:.4f} -> the floor measures CAPACITY, not "
            f"memorylessness; beating it does not demonstrate context inference (D116)")
    else:
        rec("B", "B1 memoryless floor", PASS,
            f"static expansion {static:.4f} does not beat floor {ht['memoryless_floor']:.4f}")
    if fast:
        return
    # B2: component redundancy (D112)
    comps = {"encoding": [], "carrying": [], "regulation": []}
    for i in range(n):
        g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=200 + i)
        r = evaluate(g, task, net_cfg, cfg)
        for k in comps:
            comps[k].append(r[k])
    comps = {k: np.array(v) for k, v in comps.items()}
    keys = list(comps)
    for a in range(len(keys)):
        for b in range(a + 1, len(keys)):
            x, y = comps[keys[a]], comps[keys[b]]
            if x.std() < 1e-12 or y.std() < 1e-12:
                rec("B", f"B2 {keys[a]}~{keys[b]}", WARN, "a component has zero variance"); continue
            r_ = float(np.corrcoef(x, y)[0, 1])
            spread = float(np.ptp(x - y))
            redundant = abs(r_) > 0.99 and spread < 1e-9
            rec("B", f"B2 {keys[a]}~{keys[b]}", FAIL if redundant else PASS,
                f"r={r_:+.4f}, range(x-y)={spread:.2e}"
                + ("  <-- SAME measurement up to a constant (D112)" if redundant else ""))
    # B3: matched context control (D116)
    gains = []
    for i in range(3):
        net = EvoNet(random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split,
                                   seed=400 + i), net_cfg)
        net.develop(task.E_train, eta=cfg.dev_eta, dev_ms=cfg.dev_ms, warmup_ms=200.0,
                    seed=400 + i, eta_e=5e-3)
        ordered = _affine_nmse(task.Y_test, net.behave(task.E_test, noise_seed=2)["rates"])
        gains.append(context_destroyed_score(net, task, split="test", noise_seed=2) - ordered)
    gm = float(np.mean(gains))
    rec("B", "B3 context use (matched)", PASS if gm > 0.01 else WARN,
        f"context gain (destroyed - ordered) = {gm:+.4f} over 3 nets "
        f"({'networks USE context' if gm > 0.01 else 'NO measurable context use'})")


# =============================================================================================
# C. TASK INVARIANTS — do the design properties the hypotheses depend on actually hold?
# =============================================================================================
def group_C(task, task_kwargs):
    print("\nC. TASK INVARIANTS — do the hypotheses' design premises hold?")
    K, d, r1 = task_kwargs["K"], task_kwargs["d"], task_kwargs["r1"]
    # C1: the low-rank WAIST (B2 / H-B). r1 must be STRICTLY less than min(K,d), ideally much less.
    mp = min(K, d)
    if r1 >= mp:
        rec("C", "C1 low-rank waist", FAIL,
            f"r1={r1} == min(K,d)={mp}: the rank constraint is VACUOUS (any K->d map has rank<=d). "
            f"There is NO low-rank structure, so r1 is not a free structural parameter and H-B "
            f"(peak tracks r1, not the constraint count) is UNTESTABLE in this configuration.")
    elif r1 > mp / 2:
        rec("C", "C1 low-rank waist", WARN,
            f"r1={r1} vs min(K,d)={mp}: a waist exists but is shallow (B2 asks for r1 << min(K,d))")
    else:
        rec("C", "C1 low-rank waist", PASS, f"r1={r1} << min(K,d)={mp}: genuine waist")
    # C2: realised rank of the level-1 maps matches r1
    W = (task.meta or {}).get("W_ctx")
    if W is None:
        rec("C", "C2 realised rank", WARN, "W_ctx not exposed in task.meta; cannot verify")
    else:
        ranks = [int(np.linalg.matrix_rank(W[c])) for c in range(W.shape[0])]
        ok = all(r == r1 for r in ranks)
        rec("C", "C2 realised rank", PASS if ok else FAIL,
            f"per-context map ranks {ranks} (r1={r1})")
    # C3: contexts must be MEAN-ZERO (context lives in covariance only).
    # NOTE the test must account for SAMPLE SIZE: with n_c samples the empirical mean of a mean-zero
    # variable has SE = sd/sqrt(n_c), so comparing |mean| to the SD (as a first version of this check
    # wrongly did) flags pure sampling noise. Use a z-score and a multiple-comparison-aware threshold.
    zs, n_tests = [], 0
    for c in np.unique(task.C_train):
        X = task.E_train[task.C_train == c]
        if len(X) < 3:
            continue
        se = X.std(0) / np.sqrt(len(X))
        z = np.abs(X.mean(0)) / (se + 1e-12)
        zs.append(z.max()); n_tests += X.shape[1]
    maxz = float(max(zs)) if zs else 0.0
    # Bonferroni-ish critical value for n_tests two-sided normal tests at alpha=0.01
    crit = float(abs(np.sqrt(2) * 2.5 + np.log(max(n_tests, 1)) ** 0.5))  # ~4 for tens of tests
    rec("C", "C3 contexts mean-zero", PASS if maxz < crit else FAIL,
        f"max per-context mean z-score = {maxz:.2f} over {n_tests} tests (crit ~{crit:.1f}). "
        f"Context must live in COVARIANCE only; a real mean offset would make it linearly decodable "
        f"and trivialise the task.")
    # C4: headroom must be positive and non-trivial
    for split in ("val", "test"):
        h = task.headroom(split=split)
        hr = h["memoryless_floor"] - h["oracle_ceiling"]
        rec("C", f"C4 headroom ({split})", PASS if hr > 0.1 else FAIL,
            f"floor={h['memoryless_floor']:.3f} ceiling={h['oracle_ceiling']:.3f} headroom={hr:.3f}")
    # C5: r1 and n_env must be INDEPENDENTLY variable (H-B's whole design)
    try:
        a = T.hierarchical_environments(**{**task_kwargs, "r1": max(1, r1 - 1)})
        b = T.hierarchical_environments(**{**task_kwargs, "n_train": task_kwargs["n_train"] + 20})
        Wa = (a.meta or {}).get("W_ctx"); Wb = (b.meta or {}).get("W_ctx")
        ra = int(np.linalg.matrix_rank(Wa[0])) if Wa is not None else -1
        rb = int(np.linalg.matrix_rank(Wb[0])) if Wb is not None else -1
        ok = (ra == max(1, r1 - 1)) and (rb == r1)
        rec("C", "C5 r1 / n_env independence", PASS if ok else FAIL,
            f"varying r1 changes map rank ({ra}); varying n_train leaves it ({rb})")
    except Exception as e:
        rec("C", "C5 r1 / n_env independence", WARN, f"could not verify: {e}")


# =============================================================================================
# D. EXPOSURE COHERENCE — does development actually see what it must?
# =============================================================================================
def group_D(task, net_cfg, cfg, warmup_ms=200.0):
    print("\nD. EXPOSURE COHERENCE — does development see what it needs to?")
    present = net_cfg.present_ms
    n_stim = task.E_train.shape[0]
    seq_ms = n_stim * present
    i0 = int(warmup_ms // present)
    i1 = int((warmup_ms + cfg.dev_ms) // present)
    C = task.C_train
    # D1: does the development window exceed the stimulus sequence? (TimedArray CLAMPS, does not loop)
    if warmup_ms + cfg.dev_ms > seq_ms:
        rec("D", "D1 stimulus supply", FAIL,
            f"warmup+dev_ms = {warmup_ms + cfg.dev_ms:.0f} ms exceeds the stimulus sequence "
            f"({n_stim} x {present:g} = {seq_ms:.0f} ms). Brian2 TimedArray CLAMPS past its end, so the "
            f"final stimulus is held constant for the remainder — it does NOT loop. Tile the drive array.")
    else:
        rec("D", "D1 stimulus supply", PASS, f"development window fits inside the {seq_ms:.0f} ms sequence")
    # D2: fraction of stimuli seen under plasticity
    i1c = min(i1, n_stim)
    frac = (i1c - i0) / max(n_stim, 1)
    rec("D", "D2 stimulus coverage", PASS if frac >= 0.9 else FAIL,
        f"plasticity sees stimuli {i0}..{i1c-1} = {i1c-i0}/{n_stim} = {frac:.0%} "
        f"({(cfg.dev_ms)/max(seq_ms,1):.2f} passes)")
    # D3: contexts seen under plasticity
    seen = np.unique(C[i0:i1c]); allc = np.unique(C)
    rec("D", "D3 context coverage", PASS if len(seen) == len(allc) else FAIL,
        f"contexts seen under plasticity {list(seen)} of {list(allc)} "
        f"({len(seen)}/{len(allc)}) — unseen contexts cannot be learned yet ARE assayed")
    # D4: context transitions experienced
    tr = int(np.sum(C[i0 + 1:i1c] != C[i0:i1c - 1])) if i1c - i0 > 1 else 0
    rec("D", "D4 context transitions", PASS if tr >= 2 * len(allc) else FAIL,
        f"{tr} transition(s) under plasticity; context inference cannot be learned from few "
        f"(target >= 2 per context = {2*len(allc)})")


# =============================================================================================
# E. CONFIG COHERENCE — are the parameters mutually consistent with what the science requires?
# =============================================================================================
def group_E(task, net_cfg, cfg):
    print("\nE. CONFIG COHERENCE — are parameters consistent with what the science requires?")
    # E1: readout saturation — samples vs ACTUALLY FITTED parameters.
    # _affine_nmse is the D095 capacity-constrained readout: a per-output AFFINE map (gain+offset),
    # reading output j from neuron j. It fits 2 parameters per output dimension and CANNOT mix
    # neurons. (A first version of this check wrongly assumed it fits all N features.)
    n_samp = task.E_test.shape[0]
    n_fitted = 2                      # gain + offset, per output dimension, fitted independently
    ratio = n_samp / n_fitted
    rec("E", "E1 readout saturation", PASS if ratio >= 10 else (WARN if ratio >= 3 else FAIL),
        f"{n_samp} assay samples per output vs {n_fitted} fitted readout parameters (gain+offset) "
        f"= ratio {ratio:.0f}. Capacity-constrained readout (D095): cannot mix neurons, so readout "
        f"parameters are NOT uncounted P (D111).")
    # E2: memory demand vs substrate timescale
    dwell_ms = getattr(task, "meta", {}).get("context_dwell", None)
    dwell_ms = (dwell_ms or 10) * net_cfg.present_ms
    slow = net_cfg.tau_slow
    rec("E", "E2 memory demand", PASS if slow >= 0.2 * dwell_ms else WARN,
        f"context must be held ~{dwell_ms:.0f} ms; slowest substrate timescale tau_slow={slow:.0f} ms "
        f"(gap {dwell_ms/max(slow,1e-9):.1f}x). A large gap is the known memory problem (A3).")
    # E3: n_assays vs the known reliability curve (D115)
    rec("E", "E3 n_assays", PASS if cfg.n_assays >= 4 else FAIL,
        f"n_assays={cfg.n_assays}; D115 measured fitness reliability ~0.05 at n_assays=1 "
        f"(selection on approximately pure noise). >= 4 required.")
    # E4: spectral radius, measured (D117)
    rhos = []
    for i in range(3):
        g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=700 + i)
        W = np.array(getattr(g, "W", None), dtype=float)
        rhos.append(float(np.max(np.abs(np.linalg.eigvals(W)))))
    rho = float(np.mean(rhos))
    rec("E", "E4 spectral radius", WARN if (rho > 2 or rho < 0.3) else PASS,
        f"mean rho(W) = {rho:.2f} over 3 genomes. Stringer et al. 2026: long timescales require "
        f"CRITICAL normalisation (rho ~ 1); incomplete normalisation destroys them. NOTE raw rho "
        f"overstates gain in a spiking net (threshold/refractoriness clamp it) — an effective/linearised "
        f"rho at the operating point is the quantity that matters and is NOT yet computed.")


# =============================================================================================
# F. RELIABILITY & POWER
# =============================================================================================
def group_F(task, net_cfg, cfg, n):
    print("\nF. RELIABILITY & POWER")
    va, te, fits = [], [], []
    for i in range(n):
        g = random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=300 + i)
        r = evaluate(g, task, net_cfg, cfg, report=True)
        va.append(r["val_err"]); te.append(r["test_err"])
        fits.append(_fitness(r, r["n_params"], cfg))
    va, te, fits = np.array(va), np.array(te), np.array(fits)
    se = 1.0 / np.sqrt(max(n - 3, 1))
    r_ = float(np.corrcoef(va, te)[0, 1]) if va.std() > 1e-12 and te.std() > 1e-12 else float("nan")
    rec("F", "F1 fitness reliability", PASS if (not np.isnan(r_) and r_ > 2 * se) else FAIL,
        f"r(val,test) = {r_:+.3f} +/- {se:.3f} at n_assays={cfg.n_assays} "
        f"({'above' if (not np.isnan(r_) and r_ > 2*se) else 'NOT above'} 2 SE)")
    rec("F", "F2 random baseline", PASS,
        f"random-genome fitness mean={fits.mean():.4f} sd={fits.std():.4f} max={fits.max():.4f} "
        f"(evolved runs must clearly exceed max to claim the NETWORK contributes)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fast", action="store_true", help="skip groups needing simulation")
    ap.add_argument("--n", type=int, default=12)
    ap.add_argument("--assays", type=int, default=4)
    args = ap.parse_args()

    task_kwargs = dict(K=10, d=3, r1=3, n_contexts=4, n_train=60, n_val=60, n_test=60,
                       context_dwell=10, seed=0)

    with tee("audit", header="AUDIT — does the pipeline measure what it claims, and do its premises hold?"):
        task = T.hierarchical_environments(**task_kwargs)
        net_cfg = EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                               present_ms=50, tau_slow=100.0, nmda_frac=0.5,
                               dev_ee_stdp=True, dev_wta_comp=True, wta_gain=1.0)
        cfg = EvolveConfig(pop_size=args.n, n_generations=1, dev_ms=800.0, dev_eta=1e-3,
                           n_assays=args.assays, fitness_beta=50.0, seed=999,
                           fitness_mode="regulation_only")
        cfg._gen = 0
        print(f"task {task_kwargs}")
        print(f"net  N={net_cfg.N} present_ms={net_cfg.present_ms} tau_slow={net_cfg.tau_slow}")
        print(f"evo  dev_ms={cfg.dev_ms} n_assays={cfg.n_assays} mode={cfg.fitness_mode}")

        # cheap groups always
        group_C(task, task_kwargs)
        group_D(task, net_cfg, cfg)
        group_E(task, net_cfg, cfg)
        group_B(task, net_cfg, cfg, args.n, fast=True)
        if not args.fast:
            group_A(task, net_cfg, cfg)
            group_B(task, net_cfg, cfg, args.n, fast=False)
            group_F(task, net_cfg, cfg, args.n)

        print("\n" + "=" * 78)
        n_fail = sum(1 for *_x, s, _ in [(g, n, s, d) for g, n, s, d in RESULTS] if s == FAIL)
        n_warn = sum(1 for g, n, s, d in RESULTS if s == WARN)
        for g, name, s, _ in RESULTS:
            if s != PASS:
                print(f"  {s}: [{g}] {name}")
        print(f"\n{n_fail} FAIL, {n_warn} WARN, {len(RESULTS)-n_fail-n_warn} PASS")
        if n_fail:
            print("\nDo not launch an expensive run until each FAIL is either fixed or recorded as a")
            print("deliberate, documented DECISION that does not affect the contrast being measured.")
        return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
