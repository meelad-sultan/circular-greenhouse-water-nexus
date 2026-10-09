# Next steps for the repository owner

1. Run `python -m pytest` and `python -m cgwn run --config configs/quick.yaml --out results/quick`.
2. Read `docs/method.md` and `src/cgwn/simulate.py` until you can explain every line of the hourly loop.
3. **Validation:** pick one paper from `validation/candidates.md`, run the hook, and add the result to the README
   (including poor agreement).
4. **Parameters:** open `data/parameters.csv`; for each key parameter find a source and change its status from
   `illustrative` to `verified` with the citation. Check the limits for your target jurisdiction.
5. **Your own data:** replace the S3 placeholder concentrations with ranges from your thesis (with permission).
6. Increase `experiments.sensitivity.N` to 256 or more (and `replicates`) and re-run for tighter intervals.
7. Add a tuned fixed-schedule comparator (scan the interval) so the policy comparison is not against two fixed points.
8. Tag `v0.1.0`, enable Zenodo, and add the DOI to the README and `CITATION.cff`.
