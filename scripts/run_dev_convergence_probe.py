#!/usr/bin/env python3
"""DEVELOPMENT CONVERGENCE PROBE (D083 sub-decision 3 · D085 question a).

The ONE question everything forks on: does a Kind-A (strength-only, support-frozen) plasticity rule
CONVERGE on these networks? If yes, "developed = matured" is definable by convergence and the
T-confound dissolves; the mean convergence time calibrates the development-duration window. If no
(cycles/diverges), convergence-based maturity is unavailable and we fall back to demonstrating
T-robustness.

Rule: **Oja** — the simplest convergent Hebbian rule (Zenke & Gerstner 2017: naive Hebb + slow
homeostatic scaling does NOT converge; Oja builds the stabilizer INTO the rule). Its convergence is a
theorem, so it is the right rule to ISOLATE the convergence question with. Oja is linear/PCA-style, so
it may build level-1 (encoding) structure but be blind to level-2 (context) — that is FINE for a
convergence probe, and we INSTRUMENT it (E-decode for level-1; a context-decode read for level-2) so a
'converged but level-2-blind' outcome is measured, not assumed. If that outcome appears, BCM /
nonlinear rules are the flagged next step (D085).

NO GA, NO fitness — this is a diagnostic in the spirit of run_E9_diagnostics.py.

Run from repo root:  python run_dev_convergence_probe.py
"""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np
from ddescent import provenance as P
from ddescent import tasks as T
from ddescent.evonet import EvoNetConfig, EvoNet, random_genome
from ddescent.baseline import best_nmse

# ---- Gate A config (D080/D081), so results are comparable to the flat Gate A ----
N, D, N_ENV, DENS = 50, 3, 200, 0.5   # 200 env = well-posed decode (D081)
NET = dict(N=N, n_in=10, d=D, bias=0.6, input_gain=10.0, noise_sigma=1.0,
           present_ms=50, readout_window_ms=20, nmda_frac=0.5)

# ---- Oja development hyperparameters (deliberately conservative first pass) ----
ETA = 0.01           # learning rate — small; we can sweep if convergence is marginal
MAX_EPOCHS = 200     # each epoch = one pass over the stimulus stream
CONVERGE_TOL = 1e-4  # ||dW|| / ||W|| below this for PATIENCE consecutive epochs = converged
PATIENCE = 5
N_GENOMES = 6        # a small pool — the mean convergence time is the calibration


def oja_develop(genome, net_cfg, task, eta=ETA, max_epochs=MAX_EPOCHS, seed=0):
    """Kind-A Oja development. Observe the network's own activity on the stimulus stream; update the
    magnitudes of EXISTING synapses only (support frozen). Returns (converged, epochs, trace).

    Oja per existing synapse (post i, pre j):   dW_ij = eta * y_i * (x_j - y_i * W_ij)
    where x = presynaptic state, y = postsynaptic state, from the network's actual behave() output.
    The -y^2 W term is Oja's built-in normalizer (the stabilizer that makes it converge, vs naive
    Hebb). Support mask frozen: dW is zeroed wherever W started at 0 -> P invariant (Kind A)."""
    net = EvoNet(genome, net_cfg)
    W0 = net.W.copy()
    support = (W0 != 0)                      # FROZEN — Kind-A invariant
    normW0 = np.linalg.norm(W0) + 1e-12

    trace = {"dW_rel": [], "normW": [], "support_ok": []}
    stable = 0
    for ep in range(max_epochs):
        B = net.behave(task.E_train)         # (n_env, N) state — the network's own activity
        S = B["state"]                       # rows = per-env postsynaptic AND presynaptic rates
        # Oja update accumulated over the stream. For each env row s (length N):
        #   y_i = s[i] (post), x_j = s[j] (pre).  dW_ij += eta * y_i (x_j - y_i W_ij)
        # Vectorized over synapses using the current W.
        W = net.W
        dW = np.zeros_like(W)
        for s in S:                          # one env (stimulus) at a time
            y = s[:, None]                   # (N,1) post
            x = s[None, :]                   # (1,N) pre
            dW += y * (x - y * W)            # Oja, broadcast over the full matrix
        dW *= eta / S.shape[0]
        dW[~support] = 0.0                   # FREEZE support (Kind A) -> P invariant

        Wnew = W + dW
        Wnew[~support] = 0.0                 # belt-and-suspenders: zeros stay zero
        rel = np.linalg.norm(Wnew - W) / normW0
        net.W = Wnew
        # push updated weights back into the Brian2 synapses so next behave() uses them
        net._reload_weights() if hasattr(net, "_reload_weights") else _reload_W(net)

        trace["dW_rel"].append(float(rel))
        trace["normW"].append(float(np.linalg.norm(Wnew)))
        trace["support_ok"].append(bool(((Wnew != 0) == support).all()))

        stable = stable + 1 if rel < CONVERGE_TOL else 0
        if stable >= PATIENCE:
            return True, ep + 1, trace
    return False, max_epochs, trace


def _reload_W(net):
    """Write net.W back into the Brian2 Synapses object so the next behave() uses updated weights."""
    post, pre = np.nonzero(net.W)
    # find the synapse group the same way __init__ did
    for obj in net.net.objects:
        if obj.__class__.__name__ == "Synapses" and hasattr(obj, "w"):
            obj.w = net.W[post, pre]
            break
    net.net.store("init")   # so restore('init') in behave() keeps the developed weights


def decode(Xtr, Ytr, Xte, Yte):
    return float(best_nmse(Xtr, Ytr, Xte, Yte, standardize=True)[0])


def readouts(genome, net_cfg, task, probe):
    """Level-1 (E-decode from output rates and from state) and a level-2 (context-decode) read."""
    net = EvoNet(genome, net_cfg)
    Btr = net.behave(probe["E_train"]); Bte = net.behave(probe["E_test"])
    e_rates = decode(Btr["rates"], probe["E_train"], Bte["rates"], probe["E_test"])
    e_state = decode(Btr["state"], probe["E_train"], Bte["state"], probe["E_test"])
    # level-2: can the STATE linearly predict the (held-out) context index? cheap classification-as-
    # regression: decode one-hot context from state; low NMSE = context is linearly present.
    ctr, cte = probe["C_train"], probe["C_test"]
    nc = int(max(ctr.max(), cte.max())) + 1
    Ytr = np.eye(nc)[ctr]; Yte = np.eye(nc)[cte]
    ctx = decode(Btr["state"], Ytr, Bte["state"], Yte)
    return e_rates, e_state, ctx


def main():
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("--genomes", type=int, default=N_GENOMES)
    ap.add_argument("--eta", type=float, default=ETA)
    ap.add_argument("--project-root", default=".")
    ap.add_argument("--runs-root", default=None)
    args = ap.parse_args()

    task = T.hierarchical_environments(K=10, d=D, r1=3, n_contexts=4, n_train=N_ENV, n_test=N_ENV,
                                       context_dwell=10, seed=0)
    probe = T.hierarchical_environments(K=10, d=D, r1=3, n_contexts=4, n_train=N_ENV, n_test=N_ENV,
                                        context_dwell=10, seed=12345)
    net_cfg = EvoNetConfig(**NET)

    run = P.new_run("E9", "exp", project_root=args.project_root, runs_root=args.runs_root,
                    config=dict(probe="dev_convergence", rule="oja", eta=args.eta, N=N, d=D,
                                n_env=N_ENV, density=DENS, genomes=args.genomes),
                    tag="dev-convergence-probe",
                    notes="D083/D085: does Kind-A Oja development converge? + what does it converge to?")
    run.start_log()
    print(f"run: {run.run_id}")
    print(f"Oja Kind-A development · {args.genomes} genomes · eta={args.eta} · "
          f"tol={CONVERGE_TOL} patience={PATIENCE} max_epochs={MAX_EPOCHS}\n")

    hr = task.headroom()
    print(f"task: memoryless_floor={hr['memoryless_floor']:.3f} oracle={hr['oracle_ceiling']:.3f} "
          f"(the floor->oracle gap is the level-2 reward region)\n")

    pb = {"E_train": probe.E_train, "E_test": probe.E_test,
          "C_train": probe.C_train, "C_test": probe.C_test}

    rows = []
    for g in range(args.genomes):
        genome = random_genome(net_cfg, DENS, w0=0.6, seed=g)
        P0 = genome.n_params()
        er0, es0, cx0 = readouts(genome, net_cfg, task, pb)   # BEFORE development
        conv, epochs, tr = oja_develop(genome, net_cfg, task, eta=args.eta, seed=g)
        er1, es1, cx1 = readouts(genome, net_cfg, task, pb)   # AFTER development
        P1 = int((EvoNet(genome, net_cfg).W != 0).sum())      # P must be unchanged (Kind A)
        support_held = all(tr["support_ok"])
        rows.append(dict(g=g, conv=conv, epochs=epochs, P0=P0, P1=P1, support_held=support_held,
                         er0=er0, er1=er1, es0=es0, es1=es1, cx0=cx0, cx1=cx1,
                         final_dW=tr["dW_rel"][-1]))
        print(f"genome {g}: {'CONVERGED' if conv else 'did NOT converge'} in {epochs} epochs "
              f"| P {P0}->{P1} {'OK' if P0==P1 and support_held else 'BROKEN'} "
              f"| final dW_rel={tr['dW_rel'][-1]:.2e}")
        print(f"          E|rates {er0:.3f}->{er1:.3f}  E|state {es0:.3f}->{es1:.3f}  "
              f"ctx|state {cx0:.3f}->{cx1:.3f}")

    import pandas as pd
    df = pd.DataFrame(rows)
    df.to_parquet(run.table_path("dev_convergence"))

    nconv = int(df.conv.sum())
    print("\n=== VERDICT (D083 sub-decision 3 · D085 a) ===")
    print(f"CONVERGENCE: {nconv}/{len(df)} genomes converged.")
    if nconv:
        mc = df[df.conv].epochs
        print(f"  converged-pool mean epochs = {mc.mean():.1f} (SD {mc.std():.1f}) "
              f"-> the SHORT/LONG-end calibration for the T-window (D083).")
    kindA = bool((df.P0 == df.P1).all() and df.support_held.all())
    print(f"KIND-A INVARIANT (P unchanged, support frozen): {'HELD' if kindA else '*** VIOLATED ***'}")
    print(f"LEVEL-1 (encoding) built?  E|rates {df.er0.mean():.3f}->{df.er1.mean():.3f} "
          f"(fell = development routed E; lower is better)")
    print(f"LEVEL-2 (context) built?   ctx|state {df.cx0.mean():.3f}->{df.cx1.mean():.3f} "
          f"(fell = context became linearly decodable from state)")
    print("\nread: if CONVERGED + KIND-A HELD -> convergence-based maturity is available (D083 3a).")
    print("      if E|rates fell but ctx|state did NOT -> Oja built level-1 not level-2, AS EXPECTED")
    print("      for a linear rule; BCM/nonlinear is the flagged next step (D085). NOT a failure.")
    print("      if did NOT converge -> fall back to demonstrating T-robustness (D083 3b).")

    run.finalize(status="complete", n_conditions=len(df),
                 notebook_note=f"Oja dev probe: {nconv}/{len(df)} converged; "
                               f"E|rates {df.er0.mean():.3f}->{df.er1.mean():.3f}; "
                               f"ctx {df.cx0.mean():.3f}->{df.cx1.mean():.3f}; "
                               f"Kind-A {'held' if kindA else 'VIOLATED'}")


if __name__ == "__main__":
    main()
