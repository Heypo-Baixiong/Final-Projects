# Validation of the committed revision

Validated on 2026-11-09 with Python 3.12.14 and the package versions in `results/package_versions.json`.

- Verified SHA-256 checksums for all 29 Storm Events files and the ERSSTv5 netCDF.
- Ran the analysis on all 1,708,370 source rows and the 1,627,967 retained records.
- Executed all 10 notebook code cells, in order, in a fresh in-process IPython session using `execute_notebook.py`; saved seven embedded figures and actual calculation outputs. A separate networked Jupyter kernel could not start in the execution environment, so validation used the documented in-process runner.
- Passed four synthetic-data tests: missing/invalid versus zero damage; record versus state–hazard–start-day counts; removal of a known shared trend; preservation of full monthly-share vectors during resampling.
- Checked category totals, geographic exclusions, 29-year coverage, monthly shares summing to one, damage-coverage ordering, complete-case versus available-component sums, and ten-hazard Holm corrections.
- Validated the notebook format, confirmed no error outputs, visually inspected all seven figures, and checked Python compilation and whitespace errors.

These checks validate execution and selected calculations. They do not resolve source-reporting bias or establish causal identification.
