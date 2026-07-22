"""S1 HERITABILITY PROBE (post-D108). The dev×beta sweep (D108) showed a FLAT landscape: transient
below-floor dips that never CONSOLIDATE. Two very different explanations, calling for different fixes:
  (a) NO usable variation — development produces near-identical phenotypes, nothing to select on.
  (b) NON-HERITABLE variation — variation exists but does NOT transmit parent→offspring, so selection
      can't compound it (the process is SELECTIONIST, "a population of hill-climbers," not truly
      DARWINIAN — Fernando & Szathmáry distinction, S1).
This probe discriminates (a) vs (b) directly, the way Fernando/Szathmáry prove a process is Darwinian:
measure the PARENT→OFFSPRING FITNESS CORRELATION (a realized-heritability h²-like quantity).

Method: build a population, develop+score every genome (this is the real fitness — developed phenotype).
Then for each genome, produce ONE mutated child (the GA's own mutation operator), develop+score the
child. Correlate parent fitness vs child fitness across the population. Also report the VARIATION present
(SD of fitness) to answer (a). Interpretation:
  - low fitness SD                      -> (a) no variation; selection has nothing to act on regardless
  - high SD but ~zero parent-child corr -> (b) variation not heritable; selectionist, not Darwinian
  - high SD and positive corr           -> heritable variation present; flatness is elsewhere
     (e.g. variation heritable but not aligned with the fitness axis we need, or too small to compound
      in 40 gens — points back at development QUALITY / the density-activity hypothesis, not heritability)
Logged (D102). n>=30 per the statistical rule. Measures at the SWEEP's settings (competition on/off both).
"""
import sys, pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import numpy as np, warnings; warnings.filterwarnings("ignore")
from ddescent.runlog import tee
from ddescent.evonet import EvoNetConfig, random_genome, mutate
from ddescent.evolve import EvolveConfig, evaluate, _fitness
from ddescent import tasks as T

N = 30           # population size (>= statistical rule)
DEV_MS = 800.0

def score(genome, task, net_cfg, cfg):
    r = evaluate(genome, task, net_cfg, cfg)
    return _fitness(r, r["n_params"], cfg), r["test_err"], r["regulation"]

def run_condition(wta, task, seed0=7000):
    net_cfg = EvoNetConfig(N=50, n_in=10, d=3, bias=0.6, input_gain=10.0, noise_sigma=1.0,
                           present_ms=50, tau_slow=100.0, nmda_frac=0.5,
                           dev_ee_stdp=True, dev_wta_comp=(wta > 0), wta_gain=max(wta, 1e-9))
    cfg = EvolveConfig(pop_size=N, n_generations=1, dev_ms=DEV_MS, dev_eta=1e-3,
                       n_assays=1, fitness_beta=5.0, seed=seed0)
    cfg._gen = 0
    rng = np.random.default_rng(seed0)
    pop = [random_genome(net_cfg, cfg.density, w0=cfg.w0, ei_split=cfg.ei_split, seed=seed0 + i)
           for i in range(N)]
    par_fit, chi_fit = [], []
    par_reg, chi_reg = [], []
    for i, g in enumerate(pop):
        pf, pt, pr = score(g, task, net_cfg, cfg)
        child = mutate(g, mag_sigma=cfg.mag_sigma, sign_flip_p=cfg.sign_flip_p,
                       rule=cfg.mutation_rule, rng=rng)
        cf, ct, cr = score(child, task, net_cfg, cfg)
        par_fit.append(pf); chi_fit.append(cf); par_reg.append(pr); chi_reg.append(cr)
    par_fit, chi_fit = np.array(par_fit), np.array(chi_fit)
    par_reg, chi_reg = np.array(par_reg), np.array(chi_reg)
    # realized heritability proxies
    fit_sd = par_fit.std()
    if fit_sd > 1e-9 and chi_fit.std() > 1e-9:
        r_fit = float(np.corrcoef(par_fit, chi_fit)[0, 1])
        # regression slope of child on parent = realized heritability h^2 (breeder's eqn sense)
        h2_fit = float(np.polyfit(par_fit, chi_fit, 1)[0])
    else:
        r_fit, h2_fit = float("nan"), float("nan")
    reg_sd = par_reg.std()
    r_reg = float(np.corrcoef(par_reg, chi_reg)[0, 1]) if reg_sd > 1e-9 and chi_reg.std() > 1e-9 else float("nan")
    return dict(fit_sd=fit_sd, r_fit=r_fit, h2_fit=h2_fit, reg_sd=reg_sd, r_reg=r_reg,
                par_fit=par_fit, chi_fit=chi_fit)

def verdict(label, m):
    print(f"\n[{label}] N={N} parent-child pairs")
    print(f"  fitness variation:   SD(parent fitness) = {m['fit_sd']:.4f}")
    print(f"  fitness heritability: parent-child corr r = {m['r_fit']:+.3f}   realized h^2 (slope) = {m['h2_fit']:+.3f}")
    print(f"  regulation variation: SD = {m['reg_sd']:.4f}   parent-child corr r = {m['r_reg']:+.3f}")
    # crude classification
    if m['fit_sd'] < 0.01:
        print("  => (a) NEARLY NO VARIATION in developed fitness — selection has little to act on regardless.")
    elif np.isnan(m['r_fit']) or abs(m['r_fit']) < 0.2:
        print("  => (b) VARIATION PRESENT but NOT HERITABLE (corr~0) — SELECTIONIST, not Darwinian.")
        print("        Selection cannot compound it. Development produces variation that doesn't transmit.")
    elif m['r_fit'] > 0.2:
        print("  => HERITABLE variation present (corr>0). Flatness is NOT a heritability failure —")
        print("        look to variation QUALITY/alignment or magnitude (density-activity hypothesis).")
    return m

def main():
    with tee("heritability_probe",
             header="S1: is developed-fitness HERITABLE parent->offspring? (Darwinian vs selectionist; post-D108)"):
        task = T.hierarchical_environments(K=10, d=3, r1=3, n_contexts=4, n_train=60, n_test=60,
                                           context_dwell=10, seed=0)
        print("Discriminates the D108 flat-landscape: (a) no variation vs (b) non-heritable variation.")
        m_off = verdict("eSTDP only (comp OFF)", run_condition(0.0, task))
        m_on  = verdict("eSTDP + competition (comp ON, wta_gain=1)", run_condition(1.0, task))
        print("\n" + "=" * 70)
        print("SUMMARY (heritability of developed fitness)")
        print("=" * 70)
        print(f"  comp OFF: SD={m_off['fit_sd']:.4f}  r={m_off['r_fit']:+.3f}  h^2={m_off['h2_fit']:+.3f}")
        print(f"  comp ON:  SD={m_on['fit_sd']:.4f}  r={m_on['r_fit']:+.3f}  h^2={m_on['h2_fit']:+.3f}")
        print("\nRECALL (D108): the sweep showed transient below-floor dips that never consolidate.")
        print("If r~0 here, that non-consolidation IS a heritability failure (selectionist) -> the fix is")
        print("about making variation transmit (e.g. the reverberation/structure-copying angle, S2), not")
        print("about more selection pressure. If r>0, heritability is fine and the density-activity")
        print("hypothesis (too much activity -> poor differentiation) is the live lead.")

if __name__ == "__main__":
    main()
