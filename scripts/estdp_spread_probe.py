"""eSTDP SPREAD PROBE (unselected networks). Tests the NECESSARY PRECONDITION FOR SELECTION that the
pilot lacked: does eSTDP convert genotypic variation into usable FITNESS variation? Run on a population
of RANDOM (unselected) genomes; no selection acts. Measures, eSTDP-ON vs OFF:
  (1) REPRESENTATIONAL spread -- do different genomes develop into different representations?
      (spread of effective-rank of developed state across genomes) -- the mechanism check.
  (2) FITNESS spread -- does representational spread translate to fitness variance? -- THE HEADLINE
      (fitness variance is the raw fuel of selection; its absence killed the pilot).
  (3) GENOTYPE-LINKAGE -- develop the SAME genome twice: is fitness reproducible (usable/heritable
      spread) or just run-to-run noise (unusable by selection)? -- the "is the spread real" guard.
Interpretation (per discussion): ON >> OFF on fitness spread -> eSTDP generates the variation the pilot
lacked -> green light to build the full stack. ON ~= OFF -> eSTDP isn't fixing the degeneracy -> don't
build more; investigate (D105 noise-regime / low per-synapse SNR becomes prime suspect). Caveats: tests
the GRADIENT'S EXISTENCE, not selection's success or the task's solvability. Logged (D102).
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, warnings; warnings.filterwarnings("ignore")
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig, EvoNet, random_genome
from ddescent.evolve import evaluate, _fitness, EvolveConfig, _affine_nmse
from ddescent.measures import effective_rank, participation_ratio
from ddescent import tasks as T

N_GENOMES = 12
DENSITY = 0.3
DEV_MS = 800.0

def dev_and_measure(genome, net_cfg, task, seed):
    """Develop one genome, return (fitness, effective_rank_of_state, test_err)."""
    ecfg = EvolveConfig(n_assays=2, dev_ms=DEV_MS, dev_eta=1e-3, seed=seed)
    res = evaluate(genome, task, net_cfg, ecfg)
    fit = _fitness(res, int(np.count_nonzero(genome.mag)), ecfg)
    # representational descriptor: effective rank of the developed state response to the test battery
    net = EvoNet(genome, net_cfg)
    net.develop(task.E_train, eta=1e-3, dev_ms=DEV_MS, warmup_ms=200.0, n_checkpoints=4, seed=seed)
    state = net.behave(task.E_test, noise_seed=seed + 7)["state"]
    er = effective_rank(state); pr = participation_ratio(state)
    return fit, er, pr, res["encoding"], res["carrying"], res["regulation"]

def run_population(dev_ee_stdp, task, label):
    cfg = EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                       present_ms=50, tau_slow=100.0, nmda_frac=0.5, dev_ee_stdp=dev_ee_stdp)
    fits, ers, prs, encs, cars, regs = [], [], [], [], [], []
    for gi in range(N_GENOMES):
        g = random_genome(cfg, DENSITY, w0=0.6, seed=gi)
        fit, er, pr, enc, car, reg = dev_and_measure(g, cfg, task, seed=1000 + gi)
        fits.append(fit); ers.append(er); prs.append(pr)
        encs.append(enc); cars.append(car); regs.append(reg)
    fits = np.array(fits); ers = np.array(ers); prs = np.array(prs)
    print(f"\n[{label}] population of {N_GENOMES} unselected genomes:")
    print(f"  FITNESS: mean={fits.mean():.4f} SD={fits.std():.4f} range=[{fits.min():.4f},{fits.max():.4f}]"
          f"  <- SD is the headline (fuel for selection)")
    print(f"  eff_rank(state): mean={ers.mean():.2f} SD={ers.std():.2f}  (representational spread)")
    print(f"  participation_ratio: mean={prs.mean():.2f} SD={prs.std():.2f}")
    print(f"  components: enc SD={np.std(encs):.4f} car SD={np.std(cars):.4f} reg SD={np.std(regs):.4f}")
    return dict(fit_sd=fits.std(), fit_mean=fits.mean(), er_sd=ers.std(), fits=fits)

def genotype_linkage(task):
    """Develop the SAME genome 4x with different dev seeds (eSTDP on): is fitness reproducible?
    Compare within-genome fitness SD (noise) to across-genome SD (signal). Usable spread needs
    across >> within."""
    cfg = EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                       present_ms=50, tau_slow=100.0, nmda_frac=0.5, dev_ee_stdp=True)
    g = random_genome(cfg, DENSITY, w0=0.6, seed=0)
    reps = [dev_and_measure(g, cfg, task, seed=2000 + r)[0] for r in range(4)]
    reps = np.array(reps)
    print(f"\n[genotype-linkage] same genome developed 4x (eSTDP on):")
    print(f"  within-genome fitness: mean={reps.mean():.4f} SD={reps.std():.4f}  (this is dev+noise jitter)")
    return reps.std()

def main():
    with tee("estdp_spread_probe",
             header="does eSTDP convert genotypic variation into usable fitness variation? (unselected)"):
        task = T.hierarchical_environments(K=10, d=3, r1=3, n_contexts=4, n_train=60, n_test=60,
                                           context_dwell=10, seed=0)
        print(f"floor={task.headroom()['memoryless_floor']:.3f} ceiling={task.headroom()['oracle_ceiling']:.3f}")
        off = run_population(False, task, "eSTDP OFF")
        on = run_population(True, task, "eSTDP ON")
        within_sd = genotype_linkage(task)

        print("\n" + "=" * 68)
        print("VERDICT")
        print("=" * 68)
        ratio = on["fit_sd"] / (off["fit_sd"] + 1e-9)
        print(f"fitness spread (SD): OFF={off['fit_sd']:.4f}  ON={on['fit_sd']:.4f}  ratio ON/OFF={ratio:.2f}x")
        print(f"representational spread (eff_rank SD): OFF={off['er_sd']:.2f}  ON={on['er_sd']:.2f}")
        print(f"genotype linkage: across-genome ON SD={on['fit_sd']:.4f} vs within-genome SD={within_sd:.4f}"
              f"  (usable if across >> within: ratio {on['fit_sd']/(within_sd+1e-9):.2f}x)")
        print()
        if ratio > 1.5 and on["fit_sd"] > within_sd * 1.5:
            print("=> eSTDP GENERATES usable fitness spread (across-genome >> within-genome + >> eSTDP-off).")
            print("   The variation the pilot lacked is present. GREEN LIGHT to build the full stack.")
        elif ratio > 1.5:
            print("=> eSTDP increases fitness spread, BUT it's comparable to within-genome noise --")
            print("   spread may be dev-noise, not genotype-linked. Investigate before building.")
        else:
            print("=> eSTDP does NOT meaningfully increase fitness spread over OFF. The degeneracy is")
            print("   NOT fixed. Do not build more yet; investigate (D105 low per-synapse SNR is prime suspect).")

if __name__ == "__main__":
    main()
