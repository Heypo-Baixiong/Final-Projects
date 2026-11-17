# Extreme Weather Reports in a Warming World

An analysis of US weather reports, seasonality, regional sea-surface temperature and reported damage, 1996–2024.

**[Read the project notebook](Extreme_Weather_Final%20Project.ipynb)**

The notebook presents the research question, methods, seven figures and findings in one reading sequence. It uses NOAA Storm Events, NOAA ERSSTv5 and BLS CPI-U data, covering the 48 contiguous states and Washington, DC.

Report counts are not counts of independent storms. The analysis is exploratory and does not identify a causal effect of climate change.

## Supporting material

The [support folder](support/README.md) contains the calculation scripts, data manifest, detailed result tables, tests and reproduction instructions. The notebook's displayed figures and numerical results use the validated November 9, 2026 data snapshot.

To rerun from the repository root, using Python 3.12:

```bash
python -m pip install -r support/requirements.txt
python support/execute_notebook.py
```

The first run downloads about 453 MB. See the supporting instructions before changing data revisions.
