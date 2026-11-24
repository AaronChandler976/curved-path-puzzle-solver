# Campaign decisions (choice / alternatives / why)

1. **Run 04 artefacts stay in reports/run04/; campaign bookkeeping in reports/campaign/.** As the prompt says.
2. **PREREG reading choices for Phase 1 (written 2026-11-24 ~14:20, before any v2 training or v2 val number).**
   - *Holm family.* PREREG §5 lists 9 GNN-Surv comparisons and says the intervention contrasts are "in the same family".
     Two contrasts are not among the 9: GNN-BCE vs MLP-BCE (GNN vs MLP, BCE head) and MLP-Surv vs MLP-BCE (survival vs
     BCE, MLP). So the family has **11** comparisons per evaluation and configuration (`scripts/eval_v2.py` COMPARISONS).
     *Alt:* 9 only (drops two registered contrasts) or a separate family for them (contradicts "same family").
   - *CMG-RRT-only configuration.* A state is scored there if it has ≥ 1 CMG-RRT-only success, mirroring the §0 rule for the
     main config. A state with a pre-check success but no CMG-RRT success costs the same under every order in that config.
   - *Training states.* §0: states with ≥ 1 main-config success. All their nodes are targets (unsolved ones are censored).
   - *Solve rate (§4 secondary).* Fraction of scored states whose first success is found within T = 30 s of planner time
     for that state. The PREREG doesn't define it further.
   - *HL CI.* Bootstrap over assemblies with 2,000 resamples, because HL is O(n²) per resample. Ratio CIs use 10,000 as registered.
   - *Live random seed.* The random shuffle seed is sha1("run05-live-random", assembly, state). Planner seeds follow §6.
   - *ASAP contact graph in val/test.* ASAP's own redmax graph (`scripts/asap_contact_graphs.py`, env asap) for every v2
     assembly. It is computed from geometry only, no labels.
