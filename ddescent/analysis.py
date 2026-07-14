"""
Analysis pipeline: from the tidy results table to the five hypothesis tests.

Every function takes the DataFrame produced by experiments.fixed_n.run_sweep and
returns an interpretable result object. Nothing here re-runs the simulation, so
the same table can be re-analyzed, bootstrapped, and robustness-checked cheaply.

Predictors (standardized before modelling):
    log_synapse_count  -- Frank's raw 'parameter count'
    density            -- 'more wiring / connectivity'
    pr                 -- measured effective dimensionality (the hypothesized driver)
Outcome:
    a generalization error column (default 'novel_err'; 'test_err' also valid).

The mapping to hypotheses:
    H1  standardized_coefficients   -> PR coefficient dominant & significant
    H2  density_nonlinearity        -> significant quadratic term in density
    H3  pr_saturation               -> saturating fit beats linear; plateau near env dim
    H4  mediation_density_pr         -> significant indirect effect density -> PR -> gen
    H5  handled in the E0 interpolation-sweep analysis (peak_location_vs_pr)
"""
from __future__ import annotations
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf


PREDICTORS = ["log_synapse_count", "density", "pr"]


def _standardize(df: pd.DataFrame, cols) -> pd.DataFrame:
    out = df.copy()
    for c in cols:
        s = out[c].std(ddof=0)
        out[c + "_z"] = (out[c] - out[c].mean()) / (s if s > 0 else 1.0)
    return out


# --------------------------------------------------------------- H1
def standardized_coefficients(df: pd.DataFrame, outcome: str = "novel_err",
                              mixed: bool = True):
    """H1: which predictor explains generalization once all three are in the model?

    Fits generalization ~ log_synapses_z + density_z + pr_z. If `mixed`, adds a
    random intercept per seed (environments/seeds are the repeated-measures unit).
    Returns the fitted model; inspect .params / .pvalues. A dominant, significant
    negative pr_z coefficient with attenuated count/density coefficients supports H1.
    """
    d = _standardize(df, PREDICTORS)
    formula = f"{outcome} ~ log_synapse_count_z + density_z + pr_z"
    if mixed and d["seed"].nunique() > 1:
        model = smf.mixedlm(formula, d, groups=d["seed"]).fit(reml=False)
    else:
        model = smf.ols(formula, d).fit()
    return model


def univariate_r2(df: pd.DataFrame, outcome: str = "novel_err") -> pd.DataFrame:
    """Each predictor's marginal R^2 with the outcome (a quick H1 sanity view)."""
    rows = []
    for p in PREDICTORS:
        m = smf.ols(f"{outcome} ~ {p}", df).fit()
        rows.append(dict(predictor=p, r2=m.rsquared, coef=m.params[p], p=m.pvalues[p]))
    return pd.DataFrame(rows).sort_values("r2", ascending=False)


# --------------------------------------------------------------- H2
def density_nonlinearity(df: pd.DataFrame, outcome: str = "novel_err"):
    """H2: is density -> generalization non-monotonic?

    Compares linear vs quadratic-in-density fits and returns the quadratic term's
    significance plus the density that optimizes generalization. Also reports the
    density -> PR relationship, since the mechanism claim is that dense coupling can
    COLLAPSE PR (synchronization) rather than raise it.
    """
    lin = smf.ols(f"{outcome} ~ density", df).fit()
    quad = smf.ols(f"{outcome} ~ density + I(density**2)", df).fit()
    b1, b2 = quad.params.get("density", 0.0), quad.params.get("I(density ** 2)", 0.0)
    turning = (-b1 / (2 * b2)) if b2 != 0 else np.nan
    pr_vs_density = smf.ols("pr ~ density + I(density**2)", df).fit()
    return dict(
        linear_aic=lin.aic, quad_aic=quad.aic,
        quad_term_p=quad.pvalues.get("I(density ** 2)", np.nan),
        turning_point_density=turning,
        pr_peaks_interior=_has_interior_peak(df, "density", "pr"),
        pr_vs_density_quad_p=pr_vs_density.pvalues.get("I(density ** 2)", np.nan),
    )


def _has_interior_peak(df, x, y) -> bool:
    g = df.groupby(x)[y].mean()
    if len(g) < 3:
        return False
    vals = g.values
    return bool(vals.argmax() not in (0, len(vals) - 1))


# --------------------------------------------------------------- H3
def pr_saturation(df: pd.DataFrame, outcome: str = "novel_err"):
    """H3: generalization improves with PR then saturates near env intrinsic dim.

    Compares a linear PR fit to a saturating (exponential-approach) fit via AIC and
    reports the fitted plateau location, to compare against env_intrinsic_dim.
    """
    from scipy.optimize import curve_fit
    x = df["pr"].values.astype(float)
    y = df[outcome].values.astype(float)
    lin = smf.ols(f"{outcome} ~ pr", df).fit()

    def sat(x, a, b, k):      # error = a + b*exp(-k*x): approaches floor a as PR grows
        return a + b * np.exp(-k * np.clip(x, 0, None))
    plateau, sat_aic, k = np.nan, np.nan, np.nan
    try:
        p0 = [y.min(), y.max() - y.min(), 1.0 / (x.mean() + 1e-9)]
        popt, _ = curve_fit(sat, x, y, p0=p0, maxfev=10000)
        resid = y - sat(x, *popt)
        n = len(y); rss = np.sum(resid ** 2)
        sat_aic = n * np.log(rss / n + 1e-12) + 2 * 3
        plateau = popt[0]; k = popt[2]
        knee = np.log(max(popt[1], 1e-9) / (0.05 * abs(popt[0]) + 1e-9)) / max(k, 1e-9)
    except Exception:
        knee = np.nan
    return dict(linear_aic=lin.aic, saturating_aic=sat_aic,
                fitted_plateau_error=plateau, saturation_rate_k=k,
                knee_pr=knee, mean_env_intrinsic_dim=float(df["env_intrinsic_dim"].mean()))


# --------------------------------------------------------------- H4
def mediation_density_pr(df: pd.DataFrame, outcome: str = "novel_err",
                         n_boot: int = 2000, seed: int = 0):
    """H4: does PR mediate the effect of density on generalization?

    Bootstrap of the indirect effect a*b, where
        a : density -> PR
        b : PR -> generalization (controlling density)
        c': direct density -> generalization (controlling PR)
    A significant indirect effect with a shrunken direct effect supports 'connectivity
    acts THROUGH effective dimensionality', which is the core of Frank's claim H.
    """
    d = _standardize(df, ["density", "pr"])
    rng = np.random.default_rng(seed)

    def effects(data):
        a = smf.ols("pr_z ~ density_z", data).fit().params["density_z"]
        m = smf.ols(f"{outcome} ~ density_z + pr_z", data).fit()
        b = m.params["pr_z"]; cprime = m.params["density_z"]
        return a * b, cprime

    ind0, dir0 = effects(d)
    boots = np.empty(n_boot)
    idx = np.arange(len(d))
    for i in range(n_boot):
        bs = d.iloc[rng.choice(idx, len(idx), replace=True)]
        try:
            boots[i] = effects(bs)[0]
        except Exception:
            boots[i] = np.nan
    boots = boots[~np.isnan(boots)]
    ci = np.percentile(boots, [2.5, 97.5])
    return dict(indirect_effect=ind0, direct_effect=dir0,
                indirect_ci_low=ci[0], indirect_ci_high=ci[1],
                mediation_significant=bool(ci[0] * ci[1] > 0))


# --------------------------------------------------------------- H5 (E0 bridge)
def peak_location_vs_pr(df_e0: pd.DataFrame):
    """H5: the interpolation-threshold location scales with PR, not nominal feature N.

    Expects the readout-feature sweep table (E0) with columns
    ['n_features', 'pr', 'test_err', 'group'] where each group is one reservoir
    swept over readout width. Returns, per group, the peak-error feature count and
    the PR there, and regresses peak location on PR.
    """
    rows = []
    for g, sub in df_e0.groupby("group"):
        sub = sub.sort_values("n_features")
        k = sub["test_err"].values.argmax()
        rows.append(dict(group=g, peak_n_features=sub["n_features"].values[k],
                         pr_at_peak=sub["pr"].values[k]))
    peaks = pd.DataFrame(rows)
    if len(peaks) >= 3:
        m = smf.ols("peak_n_features ~ pr_at_peak", peaks).fit()
        peaks.attrs["slope_p"] = m.pvalues["pr_at_peak"]
        peaks.attrs["r2"] = m.rsquared
    return peaks


# --------------------------------------------------------------- driver
def run_all(df: pd.DataFrame, outcome: str = "novel_err") -> dict:
    """Run the H1-H4 battery and return a dict of results for reporting."""
    return dict(
        univariate=univariate_r2(df, outcome),
        H1_model=standardized_coefficients(df, outcome),
        H2=density_nonlinearity(df, outcome),
        H3=pr_saturation(df, outcome),
        H4=mediation_density_pr(df, outcome),
    )
