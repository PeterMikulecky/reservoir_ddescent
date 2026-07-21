"""Run the D101 diagnostic panel on a completed pilot's parquet, plus best_train vs density (A1)
and fit_std trajectory (B1). Usage: python scripts/analyze_pilot.py <path-to-pilot_history.parquet>"""
import sys, numpy as np, pandas as pd
from ddescent.diagnostics import run_panel, format_panel

df = pd.read_parquet(sys.argv[1])
print(format_panel(run_panel(df, last_k=10)))

print("\n" + "="*70)
print("A1 -- INTERPOLATION THRESHOLD (best_train vs density)")
print("="*70)
print("best_train ~0 at low density -> OVERparameterized, sweep SPARSER.")
print("best_train stays HIGH at high density -> UNDERparameterized, sweep denser.\n")
for dens, s in df.groupby("density"):
    s = s.sort_values("gen")
    print(f"  P={dens}: best_train {s['best_train'].iloc[0]:.3f} -> {s['best_train'].iloc[-1]:.3f}"
          f"  (final best_test {s['best_test'].iloc[-1]:.3f})")

print("\n" + "="*70)
print("B1 -- SELECTION PRESSURE (fit_std trajectory: is selection acting?)")
print("="*70)
print("fit_std ~constant while fit_mean drifts -> selection NOT discriminating (weak beta).")
print("fit_std shrinks as fit_mean climbs -> selection IS acting.\n")
for dens, s in df.groupby("density"):
    s = s.sort_values("gen")
    early = s["fit_std"].iloc[:10].mean(); late = s["fit_std"].iloc[-10:].mean()
    print(f"  P={dens}: fit_std {early:.4f}->{late:.4f} | "
          f"fit_mean {s['fit_mean'].iloc[0]:.4f}->{s['fit_mean'].iloc[-1]:.4f}")

print("\nWITHIN-CELL fitness shape (% of steps upward; 50%=random walk, >>50%=directed):")
for dens, s in df.groupby("density"):
    s = s.sort_values("gen"); fm = s["fit_mean"].values
    print(f"  P={dens}: {np.mean(np.diff(fm)>0)*100:.0f}% upward")