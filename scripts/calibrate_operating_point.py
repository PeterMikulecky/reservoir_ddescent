"""OPERATING-POINT CALIBRATION — construct a READY-TO-LEARN substrate.

FRAMING (PJM, 2026-07-24). Three principles govern this:
  1. We are NOT building a reservoir anymore. Criteria inherited from the RC phase are artifacts of
     an abandoned framing and must not be reused. In particular the SKILL GATE — does a ridge on the
     50-dim state beat a ridge on the raw stimulus — is DROPPED. It measures the quality of a full
     mixing readout that D095 deliberately forbids: our readout is gain+offset per output, reading
     output j from neuron j, and cannot mix neurons at all. `input_gain=10` was itself chosen by that
     obsolete criterion ("the reservoir first beats baseline at 10"), so its original justification
     does not transfer.
  2. The substrate is a PRECONDITION we CONSTRUCT, not something we evolve: a ready-to-learn,
     E/I-balanced, near-critical context, on which development and selection then operate. Same
     status as Dale's law and E/I balance (A5): imposed by construction, not hypothesised.
  3. Criteria must be reliable and interpretable — which here means READOUT-FREE, so that no
     abandoned framing can smuggle itself back in.

WHAT SURVIVES FROM THE T0 HISTORY. The RC-era *criterion* is obsolete, but the *phenomenon* T0 rev3
discovered is framing-independent and still matters: at low input gain the state becomes nearly
independent of the input, and a network that ignores its input has nothing to learn from. We keep
that concern and test it directly, without a decoder.

CRITERIA (all readout-free, all measured on DEVELOPED networks, since development is part of the
architecture rather than a perturbation of it):
  1. RESPONSIVENESS  does the state depend on the STIMULUS rather than on the noise?
                     var across stimuli / (var across stimuli + var across noise seeds).
  2. HEALTHY         not silent, not saturated.
  3. DIMENSIONALITY  covariance power-law exponent alpha in the CORTICAL band 0.7-0.85
                     (Stringer et al. 2026; external published target, not an internal preference).

MEASURED AND SETTLED (2026-07-24): spectral normalisation does NOT move alpha — rescaling magnitudes
over a 9x rho range (0.5 -> 4.42) changed alpha by <0.1, because threshold/refractoriness/saturation
clamp the loop gain in a spiking network. Raw rho is not the operative quantity; INPUT DRIVE is.

Usage: python calibrate_operating_point.py [--n 3] [--quick] [--undeveloped]
"""
import sys, argparse, pathlib, itertools
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, warnings
warnings.filterwarnings("ignore")
from ddescent.runlog import tee
from ddescent.evonet import EvoNet, random_genome
from ddescent.evolve import covariance_powerlaw_exponent
from ddescent import study_config as SC

CORTEX_LO, CORTEX_HI = 0.7, 0.85


def responsiveness(net, task, n_seeds=3, n_stim=20):
    """READOUT-FREE: does the state track the STIMULUS, or only the noise?
    var_stim  = variance of the state across DIFFERENT stimuli (same noise seed)
    var_noise = variance of the state across NOISE SEEDS for the SAME stimuli
    Returns var_stim / (var_stim + var_noise) in [0,1]. Near 0 = the network ignores its input
    (the failure mode T0 rev3 identified); near 1 = stimulus-dominated.
    """
    E = task.E_test[:n_stim]
    states = [net.behave(E, noise_seed=100 + s)["state"] for s in range(n_seeds)]
    S = np.stack(states)                       # (seeds, stimuli, neurons)
    var_stim = float(np.mean(np.var(S.mean(0), axis=0)))      # across stimuli, noise averaged out
    var_noise = float(np.mean(np.var(S, axis=0)))             # across seeds, per stimulus
    return var_stim / (var_stim + var_noise + 1e-12)


def cell(input_gain, noise_sigma, task, n_genomes, develop=True):
    """Return readout-free criteria at this operating point, on DEVELOPED networks by default."""
    cfg = SC.make_net_cfg(input_gain=input_gain, noise_sigma=noise_sigma)
    resp, al, rate, sat = [], [], [], []
    for i in range(n_genomes):
        net = EvoNet(random_genome(cfg, 0.3, w0=0.6, seed=i), cfg)
        if develop:
            net.develop(task.E_train, eta=1e-3, dev_ms=SC.dev_ms(),
                        warmup_ms=SC.WARMUP_MS, seed=1000 + i, eta_e=5e-3)
        B = net.behave(task.E_test, noise_seed=2)
        st = B["state"]
        resp.append(responsiveness(net, task))
        al.append(covariance_powerlaw_exponent(st))
        rate.append(float(np.mean(st)))
        sat.append(float(np.mean(st > 0.95 * np.max(st))) if np.max(st) > 0 else 0.0)
    return (float(np.mean(resp)), float(np.nanmean(al)), float(np.mean(rate)), float(np.mean(sat)))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=3)
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--undeveloped", action="store_true",
                    help="measure BEFORE development (diagnostic contrast only)")
    args = ap.parse_args()

    gains = [0.5, 1.0, 2.0, 5.0, 10.0] if not args.quick else [1.0, 5.0, 10.0]
    noises = [0.5, 1.0, 2.0] if not args.quick else [1.0, 2.0]
    RESP_MIN = 0.20          # below this the state is noise-dominated (the T0 rev3 failure mode)

    with tee("calibrate_operating_point",
             header="Operating-point calibration: READOUT-FREE criteria for a ready-to-learn substrate"):
        task = SC.make_task()
        print(SC.summary())
        print(f"\nmeasured on {'UNDEVELOPED' if args.undeveloped else 'DEVELOPED'} networks")
        print(f"criteria: responsiveness > {RESP_MIN} | healthy (not silent/saturated) | "
              f"alpha in {CORTEX_LO}-{CORTEX_HI} (cortex)")
        print("NOTE the RC-era skill gate is DROPPED (PJM principle 1): it scores a full mixing readout")
        print("that D095 forbids. `input_gain=10` was chosen by that obsolete criterion.\n")
        print(f"{'gain':>6} {'noise':>6} | {'respons':>8} | {'alpha':>6} | {'rate':>6} | {'sat':>5} | verdict")
        rows = []
        for g, ns in itertools.product(gains, noises):
            r, a, rt, st = cell(g, ns, task, args.n, develop=not args.undeveloped)
            responsive = r > RESP_MIN
            healthy = (rt > 1e-3) and (st < 0.5)
            in_band = CORTEX_LO <= a <= CORTEX_HI
            verdict = ("noise-dominated" if not responsive
                       else "unhealthy" if not healthy
                       else "READY (cortical alpha)" if in_band
                       else "ready; alpha off-band")
            rows.append(dict(gain=g, noise=ns, resp=r, alpha=a, rate=rt, sat=st,
                             ok=responsive and healthy, in_band=in_band))
            print(f"{g:>6.1f} {ns:>6.2f} | {r:>8.3f} | {a:>6.2f} | {rt:>6.3f} | {st:>5.2f} | {verdict}")

        print("\n" + "=" * 78)
        ok = [r for r in rows if r["ok"]]
        if not ok:
            print("NO operating point is both responsive and healthy. That is a SUBSTRATE finding and")
            print("outranks any dimensionality tuning.")
        else:
            both = [r for r in ok if r["in_band"]]
            if both:
                b = max(both, key=lambda r: r["resp"])
                print(f"READY-TO-LEARN: input_gain={b['gain']} noise_sigma={b['noise']} "
                      f"(responsiveness={b['resp']:.3f}, alpha={b['alpha']:.2f}) — responsive, healthy, "
                      f"and cortex-like. Adopt as the constructed substrate (study_config).")
            else:
                b = min(ok, key=lambda r: abs(r["alpha"] - (CORTEX_LO + CORTEX_HI) / 2))
                print(f"No responsive+healthy cell reaches the cortical band. Closest: "
                      f"input_gain={b['gain']} noise_sigma={b['noise']} "
                      f"(responsiveness={b['resp']:.3f}, alpha={b['alpha']:.2f}).")
                print("Report the residual gap as a substrate property rather than tuning past the")
                print("responsiveness criterion — that is the trade T0 got wrong.")
        print("\nSettled: spectral normalisation does NOT move alpha (<0.1 over a 9x rho range).")


if __name__ == "__main__":
    main()
