"""eSTDP EFFECTIVENESS LANDSCAPE over (per-synapse SNR, eta_e). ONE fixed randomized base network in
our built mold; the ONLY things that vary are noise_sigma (SNR: lower noise = higher SNR) and eta_e
(eSTDP rate at fixed dev_ms). Per cell, eSTDP-ON vs OFF, measure where eSTDP actually RESHAPES the
representation -- the cheap landscape that BOUNDS where cross-genome fitness spread could possibly
appear (no representational change -> no spread, necessarily). Run the expensive across-genome spread
test later ONLY in the live region this reveals.

Per-cell measures (single base genome, on vs off):
  - w_diff_std  : std of E->E weight change from eSTDP (does eSTDP move weights at all here?)
  - state_change: relative change in developed state between ON and OFF (does moving weights reshape
                  the representation?) -- ||state_on - state_off|| / ||state_off||
  - eff_rank_on / eff_rank_off : representational richness (collapsed vs high-dim)
Note: eta_e sweep at fixed dev_ms=800 is really "total plasticity" (eta_e x time); read "needs high
eta_e" as "needs more total plasticity", a knob not a wall. Logged (D102).
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, warnings; warnings.filterwarnings("ignore")
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig, EvoNet, random_genome
from ddescent.measures import effective_rank
from ddescent import tasks as T

SNRS = [0.1, 0.25, 0.5, 1.0]          # noise_sigma: LOW = high SNR ... 1.0 = current (~threshold)
ETAS = [5e-4, 2e-3, 5e-3, 2e-2]       # eSTDP rate (5e-4 = the weak default the spread probe used)
DEV_MS = 800.0
DENSITY = 0.3
BASE_SEED = 0                          # ONE fixed base genome across all cells

def develop_state(noise_sigma, eta_e, ee_on, seed=BASE_SEED):
    cfg = EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=noise_sigma,
                       present_ms=50, tau_slow=100.0, nmda_frac=0.5, dev_ee_stdp=ee_on)
    g = random_genome(cfg, DENSITY, w0=0.6, seed=seed)   # SAME genome every cell
    net = EvoNet(g, cfg)
    w_pre = np.asarray(net.con_ee.w).copy() if net.con_ee is not None else None
    net.develop(task.E_train, eta=1e-3, dev_ms=DEV_MS, warmup_ms=200.0, n_checkpoints=4,
                seed=seed + 500, eta_e=eta_e)
    w_post = np.asarray(net.con_ee.w) if net.con_ee is not None else None
    state = net.behave(task.E_test, noise_seed=seed + 7)["state"]
    wdiff = float(np.std(w_post - w_pre)) if w_pre is not None else 0.0
    return state, wdiff

with tee("estdp_effectiveness_landscape",
         header="where in (SNR, eta_e) does eSTDP reshape the representation? one fixed base network"):
    task = T.hierarchical_environments(K=10, d=3, r1=3, n_contexts=4, n_train=60, n_test=60,
                                       context_dwell=10, seed=0)
    print(f"base genome seed={BASE_SEED}, density={DENSITY}, dev_ms={DEV_MS}")
    print(f"SNR axis = noise_sigma {SNRS} (low=high SNR); eta_e axis = {ETAS}\n")

    # OFF baselines depend only on noise_sigma (eSTDP off), one per SNR row
    off_state = {}
    for ns in SNRS:
        s, _ = develop_state(ns, 0.0, ee_on=False)
        off_state[ns] = s
        print(f"[OFF baseline] noise_sigma={ns}: eff_rank={effective_rank(s)}")

    print("\n" + "=" * 78)
    print("eSTDP-ON landscape: state_change (vs OFF) | w_diff_std | eff_rank_on")
    print("=" * 78)
    hdr = "noise\\eta |" + "".join(f"{e:>18}" for e in ETAS)
    print(hdr)
    results = {}
    for ns in SNRS:
        base = off_state[ns]; base_norm = np.linalg.norm(base) + 1e-9
        row_cells = []
        for eta_e in ETAS:
            s_on, wdiff = develop_state(ns, eta_e, ee_on=True)
            state_change = float(np.linalg.norm(s_on - base) / base_norm)
            er_on = effective_rank(s_on)
            results[(ns, eta_e)] = (state_change, wdiff, er_on)
            row_cells.append(f"{state_change:.3f}/{wdiff:.3f}/{er_on:>2d}")
        print(f"{ns:>8} |" + "".join(f"{c:>18}" for c in row_cells))

    print("\n(cell = state_change / w_diff_std / eff_rank_on)")
    print("\nREADING: state_change is the key -- it's how much eSTDP reshaped the representation vs OFF.")
    print("  Look for the (SNR, eta_e) region where state_change is LARGE (eSTDP is live) vs where it's")
    print("  ~0 (eSTDP inert). w_diff_std shows if weights moved at all; if weights move but state_change")
    print("  stays ~0, moving weights isn't reshaping the representation (deeper problem than rate/SNR).")
    # summarize the landscape
    changes = np.array([[results[(ns, e)][0] for e in ETAS] for ns in SNRS])
    bi = np.unravel_index(np.argmax(changes), changes.shape)
    print(f"\nMAX state_change = {changes.max():.3f} at noise_sigma={SNRS[bi[0]]}, eta_e={ETAS[bi[1]]}")
    print(f"MIN state_change = {changes.min():.3f} (most inert cell)")
    if changes.max() < 0.05:
        print("=> eSTDP is INERT EVERYWHERE in this grid -- moving weights doesn't reshape representation")
        print("   at ANY (SNR, eta_e). Deeper than rate/noise; points to representation-formation itself.")
    else:
        strong = [(SNRS[i], ETAS[j]) for i in range(len(SNRS)) for j in range(len(ETAS)) if changes[i,j] > 0.5*changes.max()]
        print(f"=> eSTDP is LIVE in {len(strong)} cells (state_change > 50% of max). Live region: {strong}")
        print("   -> run the across-genome spread test HERE next.")
