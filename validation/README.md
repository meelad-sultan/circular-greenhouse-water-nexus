# Validation hook

**Status: validation against published data is PENDING.** The hook below is implemented and tested on a
synthetic round trip only (`python -m cgwn validate --selftest`), which proves the fitting code works and
validates nothing about the physical model. Do not describe the model as validated until you have run it on a
real published curve and reported the result, good or bad.

## Workflow
1. Pick a paper from `candidates.md` (single-metal column experiments with stated conditions).
2. From the methods section, fill in `conditions_template.yaml` (inlet concentration, flow rate, bed mass, time unit,
   and the full citation under `source`).
3. Digitise the breakthrough curve (C/C0 against time) from the figure, for example with WebPlotDigitizer, into
   `points_template.csv` (columns `t`, `c_over_c0`). Some papers publish the numbers in supplementary files.
4. Run: `python -m cgwn validate --points my_points.csv --conditions my_conditions.yaml --out validation/outputs/my_paper`
5. Read `validation_result.json` and `validation_curve.png`: fitted `q0` (mg/g) and `kTh` (mL/(min mg)), R2, and the
   relative error in the time to 10 % and 50 % breakthrough. `K_equivalent_for_simulator` is the steepness the
   simulator would use (`K = kTh * q0 * m / Q`).
6. Report what you find, including poor agreement, and cite the paper. Check the journal's reuse terms before
   reproducing a figure; plotting your model line against extracted points with a citation is the usual practice.

## What this does and does not validate
It checks the single-species Thomas breakthrough shape that every bed in the simulator is built on.
It does not validate the multi-species competition rule (which is a stylised heuristic), the PFAS bed
(exploratory), or any greenhouse or plant-scale behaviour.
