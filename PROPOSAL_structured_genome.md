# PROPOSAL — structured genome, interpretable P, and a task that can show two descents

**Status: PROPOSAL, not a decision.** Nothing here is memorialized. It is written to be argued with, and
several parts should probably be rejected. Post-D130; depends on HYPOTHESIS_LOG §ENCODING (E1–E3).

---

## 1. The problem the redesign has to solve

D130: the recurrent network contributes nothing, so P — which counts recurrent synapses — could never
have mattered. D092, independently and on a different task: random connectivity lacks the attractor
topology that persistent memory requires. Litwin-Kumar & Doiron: *modest clustering*, a statistical bias
in the connection distribution, is enough to produce network-level slow dynamics.

So the genome must be able to express connection STATISTICS. The current genome expresses individual
synapses, and clustered topologies are a vanishing fraction of that space.

---

## 2. P stays interpretable — but `P_syn` is a CONTROL, not a capacity (corrected, PJM)

Under the direct encoding, genome size and synapse count are the same number. Under any structured
encoding they decouple:

- **`P_gene`** — the count of evolvable genes. What selection acts on.
- **`P_syn`** — the count of realised synapses.

**⚠ CORRECTION to the first draft of this proposal.** It called `P_syn` "network capacity." That is
wrong, and the error made the design look incoherent: if capacity were fixed, `P_gene` would have nothing
to act through. Computational capacity depends on how synapses are ARRANGED, not only on how many exist,
and arrangement is precisely what varies here. **`P_syn` is only a synapse count, and holding it fixed is
a nuisance-variable control** — the same role `w0_for_density` plays for drive (D129) — to stop "more
genes" from silently importing "more synapses."

**What `P_gene` expresses is RESOLUTION.** Same number of synapses; the genome carves them into finer
arrangements as genes are added. Few genes express only coarse structure; many express fine distinctions.
That IS capacity in the double-descent sense — more genes means more expressible connectivity patterns,
hence more expressible network functions — but it acts through ORGANISATION rather than through count.

**⚠ `P_syn` is well-defined only if sparsity is IMPOSED.** Under the direct encoding it is natural: count
the nonzero weights. Under a generative encoding every neuron pair receives some weight and there is no
intrinsic sparsity. So the phenotype must impose it — **fix the density, generate all pairwise weights,
keep the top-M by magnitude** (M = density x N x (N-1)). That is a design choice, not a discovered
quantity, and must be stated as one wherever `P_syn` is reported. It also interacts with structure: a
strongly clustered genome will spend its M synapses within clusters, which is the intended behaviour but
should be verified rather than assumed.

**Proposal: `P_gene` is the double-descent axis; `P_syn` is held fixed as a control.** The justification
is the analogy the project already runs on — in ML, P is the number of parameters fitted to the training
set; in evolution the fitted object is the GENOME and the constraints are the task trials, so
overparameterization means more heritable degrees of freedom than the task constrains.

**Reporting rule if adopted:** every result states both numbers, and states how sparsity was imposed. Any
curve plotted against "P" without saying which is a defect.

## 3. Two candidate vocabularies

Both express the same idea: **the genome specifies connection statistics; the phenotype samples
synapses from them.** They differ in how the complexity knob behaves.

*Both knobs answer one question: HOW FINELY CAN THE GENOME DISTINGUISH ONE NEURON FROM ANOTHER? K does
it discretely (types); d does it continuously (coordinates).*

### Option A — block genome (stochastic block model). Simpler; recommended FIRST.

**Concretely:** sort every neuron into one of K types (N genes), then write down how strongly a type-a
neuron connects to a type-b neuron — a K x K table (K² genes). Any synapse's strength is a lookup on the
types of its two endpoints. Make within-type entries strong and between-type entries weak, and you have
clusters. At N=50, K=2 is 4 table entries plus 50 assignments = 54 genes specifying 735 synapses.

**K is "how many kinds of neuron the genome can name."** K=2 -> two kinds. K=8 -> eight kinds, finer
structure, 114 genes.

- Each neuron carries a block-assignment gene: `b_i in {1..K}`  ->  N genes
- A `K x K` matrix of block-to-block connection weights  ->  K² genes
- E/I identity per neuron (D038, unchanged)
- `P_gene = N + K^2 + c`; the knob is **K**

**Why first.** It produces the thing already demonstrated to work at N=50 — clusters (D092's ceiling is
K=2 plus an inhibitory pool) — so it can be validated directly against a known positive. It is trivially
interpretable, easy to debug, and every gene has an obvious meaning.

**Weakness.** K² grows fast, so `P_gene` moves in coarse jumps; and block assignment is categorical,
which makes mutation less graded than the replicator dynamics assume.

### Option B — latent-position genome ("developmental coordinates"). More elegant; riskier.

**Concretely:** instead of discrete types, every neuron gets d numbers — a POSITION in an abstract space.
Connection strength is a function of how close two neurons are in that space: near = strong, far = weak.
Clusters then emerge from proximity rather than being declared. d=1 puts neurons on a line (a gradient);
d=2 on a plane (patches); d=5 allows richer arrangements.

**d is "how many independent identity dimensions the genome can specify."** Biologically this is the
literal story — connectivity is patterned by graded molecular cues (ephrins, cadherins), not by a synapse
list, and d is how many such gradients exist.

- Each neuron carries a latent position `z_i in R^d`  ->  `N*d` genes
- Connection weight `W_ij = e_j * g(z_i, z_j)`, with `g` a distance kernel (amplitude, range, baseline)
  or a bilinear form `z_i^T M z_j`  →  a few, or `d^2`, global genes
- `P_gene = N*d + d^2 + c`; the knob is **d**

**Why it is attractive.** `P_gene` is LINEAR in d, so the axis is smooth and finely tunable — exactly
what a P-sweep wants. Clustering emerges rather than being imposed: neurons near each other in latent
space are strongly connected. At `d -> N` it degenerates gracefully to the current direct encoding, so
the old regime is a limiting case rather than a discarded one. And it is biologically the right story —
latent position is molecular identity, and real connectivity is specified by graded molecular cues, not
a synapse list. This is the GENE encoding from the literature (arXiv:2403.14019), where genome size grows
linearly rather than quadratically in neuron count.

**Weakness, and it is a real one.** The CPPN-SNN work (Elbrecht & Schuman 2020) reports that a single
gene mutation can restructure a large fraction of the connectivity. An encoding where most mutations are
catastrophic is not evolvable and would break the graded-fitness assumption underlying replicator
selection. **Mutational smoothness must be measured before this is trusted** — see §6.

**Recommendation: build A, validate against the ceiling, then build B behind the same interface.** The
scientific claim rides on B's smooth axis; A is what proves the machinery works.

---

## 4. Task: the generalization dimension is the missing piece

*This is the part of the proposal I would defend hardest, because it addresses a gap in the study design
that predates all of the above.*

For a second descent to be observable there must be something to generalize TO. The task therefore needs
a train/test split over STIMULUS STRUCTURE, not merely over noise draws:

- `n_cues = K` patterns, shared set (DMTS, D126), relation-balanced (D126 amendment)
- All `K^2` ordered (cue, probe) pairs exist
- **The split is NESTED (PJM), because D113 requires fitness to come from val and test to be
  reporting-only. A flat pair-level split would have discarded that.**

**Pair level:** the `K^2` pairs split into SEEN and UNSEEN. Unseen pairs are touched by NOTHING — not
development, not fitness.
**Trial level, within seen pairs:** train trials drive development, val trials compute fitness. D113
preserved exactly.

This yields three error measures, and the third is new to the project:

| measure | drawn from | role |
|---|---|---|
| **val error** | seen pairs, fitness trials | what selection optimises (D113) |
| **test-on-SEEN** | seen pairs, held-out trials | generalization to new NOISE — what "test error" has meant here so far |
| **test-on-UNSEEN** | unseen pairs | generalization to new STIMULUS STRUCTURE |

**The decomposition is worth more than the fix.** Those are different phenomena, and separating them says
WHAT KIND of overfitting occurs past the interpolation threshold: a genome that memorises pairs shows a
gap between test-on-seen and test-on-unseen; one that has found the identity rule does not. Report both
curves against `P_gene`; a second descent that appears in one and not the other is itself a finding.

This creates the two solution modes double descent requires:
- **Memorize** — tune the network so each training pair happens to produce the right output. Fails on
  held-out pairs.
- **Generalize** — compute the identity comparison. Succeeds on held-out pairs.

`n_train_pairs` is then the constraint count, and it is a FREE KNOB. That matters more than it first
appears: FRAMING's two-failure-mode problem (a flat curve could mean "too hard" or "too simple") exists
because P_crit's location was never controllable. Here it is — the interpolation threshold can be
POSITIONED inside the accessible `P_gene` range by choosing how many pairs to train on, rather than hoped
to fall there.

Chance floor is preserved by construction, and `omit_cue` / `scramble` remain valid.

**First descent is plausible** because the task has a genuinely learnable general rule that clustered
connectivity can implement (cue selects a cluster; probe either re-activates it or does not).
**Second descent is plausible** because past the interpolation threshold the encoding's smoothness is an
implicit regularizer — many genomes fit the training pairs, and the encoding biases which one is found.
That is the mechanism-(1) story the project already runs on, now with a place to act.

---

## 5. N: yes to 100, but the argument is not what it looks like

N does not buy bigger clusters. At N=50 (40E/10I) with K=2 you get ~20 E per cluster; at N=100 (80E/20I)
with K=4 you get ~20 E per cluster. **N buys MORE clusters, not larger ones.**

So the decision follows the task: `n_cues = 2` needs 2 clusters and N=50 suffices; `n_cues = 4` (D126's
rung 2, and a far better generalization split — 16 pairs instead of 4) needs ~4 clusters and therefore
N≈100.

**Cost is the real constraint.** Simulation scales with synapse count, so N=100 is roughly 4x per run.
D130's sweep was 75 minutes at N=50; the same design at N=100 is ~5 hours. Recommendation: **develop and
debug at N=50 with K=2, then move to N=100 for the actual sweep**, where the pair-generalization split
has enough pairs to be meaningful. Do not pay 4x while the machinery is still being validated.

---

## 6. Build order — each step gates the next, nothing expensive before its precondition

1. **Block genome behind the existing `Genome` interface.** `random_genome` gains a structured variant;
   `EvoNet` unchanged. Verify `P_syn` is held to target as K varies.
2. **Known-positive check.** Does a hand-set block genome (K=2 + inhibitory pool) reproduce the D092
   ceiling's carry — cue selects the matching cluster, persists, and DECAYS across the delay? If not, the
   implementation is wrong and nothing after this matters.
3. **⚠ GEN-0 PRIOR CHECK — the E2 falsification condition.** Random structured genomes must be AT CHANCE
   on the task. A structured prior that already performs is a seeded genome under another name. This is a
   required output, not a diagnostic.
4. **Ablation, repeated.** Re-run D130's intact-vs-ablated on structured genomes at a delay past
   `tau_slow`. **If recurrence still contributes nothing, E1 is refuted and the redesign has failed** —
   stop rather than proceeding to a sweep.
5. **Mutational smoothness.** Distribution of |fitness change| per single-gene mutation. If most mutations
   are catastrophic, selection has no gradient regardless of expressivity — this is the Elbrecht &
   Schuman hazard and it kills Option B specifically.
6. **Low-P solvability screen** (D126 step 3), then the `P_gene` sweep with D127's localization
   instrumentation already attached.

Steps 2–5 are cheap and each can end the line. Only step 6 is expensive.

---

## 7. What I am least sure about

- **`P_syn` fixed while `P_gene` varies** is the crux, and it is arguable. The alternative — let `P_syn`
  follow from the genome and report both — is more natural biologically but reintroduces the confound
  D129 spent a sweep controlling.
- **Whether pair-generalization is really a second-descent setup.** It is a clean interpolation/
  generalization structure, but nobody has shown that an evolved spiking network memorizes pairs in the
  way the argument assumes. It may simply fail at both.
- **Whether E2 survives.** If a reviewer reads "we gave the genome the ability to make clusters, and then
  it made clusters," the at-chance gen-0 prior is the entire defence. It needs to be reported prominently
  and early, not buried.
- **Whether K or d is even the right knob.** Both conflate "how much structure can be expressed" with
  "how many genes exist." Those might need separating.
- **Whether top-M sparsification is neutral.** Imposing a fixed synapse count on a generative encoding is
  an intervention, and it may itself shape which structures are reachable — a clustered genome and a
  diffuse one spend their M synapses very differently. This wants a check, not an assumption.
- **How many pairs can be held out at all.** At `n_cues = 2` there are only 4 pairs, so an unseen set is
  barely definable; at `n_cues = 4`, 16 pairs make a 12/4 split feasible. This is an independent argument
  for N=100, and it may be the binding one.
