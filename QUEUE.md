# Queue

Single source of truth for what's next. Updated 2026-07-16 (evening).
Claims live in `DECISIONS.md`; framing in `FRAMING.md`; narrative in `LAB_NOTEBOOK.md`.

## Where the project stands

**The reservoir is retired (D032).** It froze W, so it could not test a claim about regulatory
connections being the evolved parameters. It did its job: it clarified the questions and forced
the reckoning with the literature.

**The model is now an evolvable spiking network** (`ddescent/evonet.py`): **W is the genome**,
no trained readout, input neurons receive the environment, output neurons' behavior IS the
phenotype (D036), environments demand **response profiles**, and **density sweeps P = |W| across
the interpolation threshold** — Frank's Figure 1 x-axis made of regulatory connections.
Verified: N=100, d=10, n_env=50 → constraints=500; density 0.005→0.5 sweeps P 50→4950
(0.1x → 9.9x). **Dale's law with evolvable per-neuron identity** (D038): neurons can evolve
into inhibitory cells; violations 97/100 → 0.

**The question** (`FRAMING.md`): Frank fuses **P** (parameter count) with **D** (effective
capacity). Three modes of adding capacity — **grow nodes / densify / reorganize** — leave
different fingerprints on (P, D_max, D). Which mode selection uses should depend on
environments, tasks, and **cost structure**.

---

## Critical path

### 1. `ddescent/evolve.py` — the GA  ← START HERE
Population, selection, generations on the Dale genome (`Genome`, `mutate` already exist in
`evonet.py`). Fitness = distance between expressed output rates and the demanded profile, minus
metabolic cost. Spawn-safe, provenanced (D004/D007).

### 2. GATE A — baseline, **per density arm** (D030's rule, applied prospectively)
Can an evolved network beat a trivial baseline? **Per arm**, because density is confounded with
activity (D037): random genomes give output rate 0.044 at density 0.005 vs 2.124 at 0.5 — the
sparse end is nearly silent. **Hypothesis: evolution compensates** (W is a genome now; sparse
nets can evolve bigger weights). If low-density arms cannot compute even after evolution, the
double-descent sweep **has no left half** and P must be varied another way.
*NB (D037): low density → low activity → low fitness is **on the causal path**, not a confound.
D030's lesson is narrower: before interpreting a representational metric like PR, check the
system computes.*

### 3. GATE B — does a double-descent peak appear at all?
Sweep density; look for a peak in test error near P ≈ constraints (density ≈ 0.05).
**This is where the project lives or dies.** No peak ⇒ no phenomenon ⇒ the P/D question is
unaskable and the substrate needs rethinking. Cheap; do it before building anything on top.

### 4. GATE C — can the network reach the fluctuation-driven balanced regime? (D039)
**`noise_sigma = 0.0` and tonic `bias = 0.4` put us in the tonic regime, where inhibition is
purely subtractive and gain control is UNAVAILABLE.** Divisive regulation requires fluctuations
(Chance/Abbott/Reyes; Prescott & De Koninck). With Dale's law a balanced E/I net self-generates
them — but that must be verified. **Precondition for regulatory motifs to emerge at all.**

### 5. The experiment — three modes × cost structure
Cost per node discourages growing N; cost per synapse discourages growing N and densifying;
zero cost frees everything and lets **mutation bias** decide (where Louis's simplicity-bias work
becomes ours to use). Sweep cost structure; watch which mode evolution takes; measure the
(P, D_max, D) fingerprint.

---

## Open design questions (decide, don't default)

- **N as a gene** — needs a **high cost per node**, as in biology (PJM). Two separable questions:
  *does growing N produce a second descent?* needs only **fixed-N arms compared across N** (no
  gene, no muddied waters — tractable now); *would evolution choose to grow N?* needs the gene.
  **Superposition supplies the currency:** capacity ≤ N (Dambre); if N < features you superpose
  and pay in interference; pay for nodes to reduce it.
- **Interference vs abstraction** (PJM) — both lower PR and **PR cannot tell them apart**.
  Generalization may *emerge from* superposition: a low-dimensional latent shared across
  instantiations = "snakeness". **The discriminator is novel-but-related environments** (D029):
  abstraction predicts new instances of the class; interference destroys within-class
  discriminability.
- **Is PR the wrong measure?** Superposed features are non-orthogonal; PR measures linear
  dimensionality. Feature-recovery (sparse coding / SAE) may be the right instrument. Challenges
  D002/D016 — live, unresolved.
- **Regulatory measurement (D040)** — implement the three stages: potent/null screen →
  functional contribution → gain-vs-offset. Needs GATE C first.
- **Which neurons express the phenotype?** d is a niche property, fixed per arm (D037). But
  should the network choose *which* cells are outputs? Topology, not capacity. Biologically real
  (development).
- **Subtractive vs divisive** — settled for now: **no shunting** (D039). Revisit only if GATE C
  shows the balanced regime is unreachable.

## Deferred

Crossed net×task design (seeds aliased); Protocol T; systematic related-work review (D017);
E7 scaling/invariants; two GA arms (S- vs T-fitness); H2 restatement as a w0×density interaction;
"cells" → "conditions" rename.

## Standing rules (earned the hard way)

- **Search before building, not after.** Three times a PJM-requested search overturned my
  reasoning: D014 (normalization), D031 (memory–nonlinearity), D034 (implicit bias) — plus D039
  (shunting). The pattern is unambiguous.
- **Prove the system beats a trivial baseline before interpreting any representational metric**
  (D030).
- **Log-transform heavy-tailed error outcomes**; treat convergence warnings as results (D028).
- **Don't raise structural alarms from smoke-preset numbers** (D033).
- **Don't bolt on mechanisms; make the architecture capable and let selection build them** (D038).
- **Geometry does not imply mechanism** (D040).
- Commit before `reg` runs; PR stays confirmatory, the rest exploratory (D025).
