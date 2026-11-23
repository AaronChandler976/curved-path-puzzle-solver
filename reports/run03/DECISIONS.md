# Run 03 decisions made on Aaron's behalf

Each entry: choice / alternatives / why.

1. **R1 sweep step rule = max(ε/2, d + ε)** (d = current min SDF over the robot samples). *Alt:* a uniform ε/2 = 0.0025 step to
   D ≈ 2.6–3.5 (≈ 1,000–1,400 SDF evaluations per direction). *Why:* under a pure translation the SDF is 1-Lipschitz, so every pose
   skipped by a larger step is proven collision-free. The rule is therefore at least as strict as the uniform ε/2 sweep (it IS the ε/2
   sweep near contact) and about 10× cheaper. Recorded in `precheck.jsonl` (`step_rule`, `max_fixed_step` = 0.0025).
2. **R1 stops at the first clearing direction** (candidate order = adapter order). *Alt:* sweep all directions. *Why:* the prompt asks
   for `linear_free` and the first direction that clears. Blocked directions are always swept fully, so `linear_free` is exact either way.
3. **R1 robot samples = a fresh draw of the same size (3,888) after `seed_all(query seed)`.** trimesh 5.2's `sample_surface` uses an
   unseeded `default_rng`, so CMG-RRT's exact v1 sample set can't be reproduced from the logged seed. The agreement in start min-SDF is
   reported (`reports/run03/rotation.md`: median |Δ| 2.7e-8, p95 4.7e-4).
4. **R1 inconsistencies (124 linear-free but unsolved) stay `unsolved`/censored in the labels.** *Alt:* relabel them as successes.
   *Why:* hard rule 3, and the labels must be what the oracle returned. Adding a linear pre-check to the oracle is a run 04 item.
