| example | detector | seed | solved | stop | iterations | planner s | s / iteration | path fine-valid | busy_frac | confounded |
|---|---|---|---|---|---|---|---|---|---|---|
| general/16505 | exact | 0 | no | iterations | 5000 | 3169 | 0.634 | - | 0.104 | True |
| general/16505 | exact | 1 | no | iterations | 5000 | 3115 | 0.623 | - | 0.016 | False |
| general/16505 | exact | 2 | no | iterations | 5000 | 2973 | 0.595 | - | 0.025 | False |
| general/16505 | learned | 0 | yes | solved | 2557 | 570 | 0.223 | - | 0.635 | True |
| general/16505 | learned | 1 | yes | solved | 1534 | 346 | 0.225 | - | 0.000 | False |
| general/16505 | learned | 2 | yes | solved | 2346 | 508 | 0.217 | - | 0.000 | False |
| puzzle/alpha | exact | 0 | no | iterations | 5000 | 3364 | 0.673 | - | 0.033 | False |
| puzzle/alpha | exact | 1 | no | iterations | 5000 | 3227 | 0.645 | - | 0.128 | True |
| puzzle/alpha | exact | 2 | no | iterations | 5000 | 3171 | 0.634 | - | 0.061 | True |
| puzzle/alpha | learned | 0 | no | iterations | 5000 | 943 | 0.189 | - | 0.000 | False |
| puzzle/alpha | learned | 1 | no | iterations | 5000 | 945 | 0.189 | - | 0.000 | False |
| puzzle/alpha | learned | 2 | no | iterations | 5000 | 930 | 0.186 | - | 0.000 | False |

| example | detector | solved / runs | mean iterations (solved) | mean planner s (all runs) |
|---|---|---|---|---|
| general/16505 | exact | 0 / 3 | 0 | 3086 |
| general/16505 | learned | 3 / 3 | 2146 | 475 |
| puzzle/alpha | exact | 0 / 3 | 0 | 3254 |
| puzzle/alpha | learned | 0 / 3 | 0 | 939 |

**Are the learned successes real?** Every solved path was re-checked with the exact SDF of 0.obj at step ≤ ε/2, on
the run's own robot samples (`scripts/t5_validate_paths.py`, `path_recheck_exact.json`):

| run | edges | edges that penetrate (exact) | deepest point |
|---|---|---|---|
| 16505 learned seed 0 | 2,275 | 614 (27%) | −0.133 |
| 16505 learned seed 1 | 2,580 | 1,275 (49%) | −0.148 |
| 16505 learned seed 2 | 2,370 | 1,091 (46%) | −0.149 |

All three learned "solutions" pass through the obstacle by about 30× the contact tolerance. This fits run 02's finding
that the learned SDF errs toward "free" near the surface (`reports/run02/r3_exact_sdf.md` §2).

**Decision (DECISIONS #23):** counting physically valid solutions, exact and learned are tied (0/3 on 16505 and
0/3 on alpha). The exact detector is not clearly worse; it refuses paths that the learned SDF accepts wrongly. So the
run 02 hybrid fix (exact decisions + smoothed guidance gradient) is not triggered and oracle v2 is unchanged. The
hybrid is implemented (`exact_sdf.make_detector(grad_dx=...)`, `repro_cmgrrt.py --grad-dx`, `query(grad_dx=...)`)
but not evaluated in this run. The exact detector costs about 3× more per iteration on these large meshes
(0.60–0.67 vs 0.19–0.23 s), as in run 02.

Confounding: 4 of 12 runs are flagged (busy_frac 0.104 / 0.635 / 0.128 / 0.061). In every flagged sample outside CPU
was ≤ 0.17 cores; the flags come from the load criterion. Our single process ran up to ~12 library threads plus CUDA
synchronisation waits, which raise the load average beyond our measured CPU. For the first two runs this was before
the our-load fix (DECISIONS #22). The flags affect only s/iteration, not the solved/unsolved results above.
