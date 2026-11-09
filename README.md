# Extreme Weather Reports in a Warming World

An exploratory analysis of NOAA Storm Events reports and regional sea-surface temperature (SST), 1996–2024. The project examines reporting trends, record-start seasonality, SST associations and available reported property/crop damage.

**The unit is a database record, not an independent physical storm.** Results describe the 48 contiguous US states and Washington, DC, using county and forecast-zone records. They do not identify a causal effect of climate change or correct changes in reporting and exposure.

Open [the executed notebook](Extreme_Weather_Final%20Project.ipynb) for the analysis, seven figures and current results. Computations are in [weather_analysis.py](weather_analysis.py); [REVISION_NOTES.md](REVISION_NOTES.md) explains the methodological changes.

## Main changes

- Retain event identifiers, check duplicates and dates, and export data-quality audits. Separate Heat from Drought and exclude funnel clouds/waterspouts from Tornado.
- Compare records with a coarser state–hazard–start-day unit, without claiming either identifies independent storms.
- Use annual regressions with HAC uncertainty; compare raw, detrended and first-differenced SST relationships. Include alternative HAC lags, a quadratic trend, leave-one-year-out checks and Holm correction for each ten-hazard testing family.
- Compare equal-weight annual monthly shares. Resample complete annual vectors in two- and three-year blocks instead of treating individual records as independent seasonal observations.
- Preserve missing damage. Display coverage and complete-case sensitivity, and compare **mean annual** CPI-adjusted damage across unequal-length periods.
- Pin source revisions and hashes, export aggregate tables, and generate numerical conclusions from the current run.

## Reproduce

Tested with Python 3.12.14. From the repository root:

```bash
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m unittest -v test_analysis.py
python weather_analysis.py
python execute_notebook.py
```

The analysis downloads about 453 MB on the first run, verifies cached input hashes, and writes CSV/JSON tables to `results/` and seven PNG figures to `figures/`. Allow several minutes for downloading and processing.

`execute_notebook.py` runs every code cell in order in a fresh, in-process IPython session and saves actual text, table and figure outputs. This avoids a separate Jupyter kernel's socket requirement in restricted environments. It stops on any cell error. A Jupyter interface can also open the notebook using this environment; the notebook and script share the same calculations.

### Data revisions

`data_manifest.json` lists exact filenames, URLs, retrieval times and SHA-256 checksums. Raw inputs are cached in `data/` and excluded from Git. Retain that cache for exact long-term replication: NOAA may remove older storm revisions, and the SST URL is updated in place.

A changed input fails verification. If a newly downloaded SST release is intentional, run:

```bash
python weather_analysis.py --accept-updated-sst
python execute_notebook.py
```

This explicitly accepts the cached SST file's new hash and regenerates results. It does **not** force a download when a cache already exists. Review changed results before committing. Storm-source revisions require deliberate manifest updates and a full rerun; the code never silently selects a newer revision.

## Reading the results

`results/annual.csv` contains 29 annual observations. `sst_associations.csv` reports raw, detrended and first-difference correlations and the SST coefficient conditional on linear time. `sst_sensitivity.csv` contains alternative specifications. Trend and association tables report separate Holm adjustments over the ten named hazards; these are exploratory families, not one correction covering every calculation.

`seasonal_differences.csv` contains late-minus-early monthly shares with **pointwise** bootstrap intervals, not a simultaneous seasonal test. `hazard_seasonal_profiles.csv` helps assess whether aggregate seasonality reflects the mixture of hazards.

`annual_damage.csv` shows available-component and complete-case sums and coverage. `damage_periods.csv` compares annual means and medians. Unknown losses are not imputed. Inflation adjustment does not normalize exposed wealth or population. The largest records and inconsistent source/start years are exported for audit.

## Limits

Twenty-nine annual observations provide limited information. HAC and bootstrap intervals are approximate, the time trend is a modeling choice, and the broad SST box is not a validated predictor for every hazard. Reporting changes, hazard composition and exposure remain unresolved. A negative time-adjusted association must not be interpreted as evidence that warming prevents disasters; first-difference and alternative specifications may support different levels of precision.

A defensible next step is a narrower hazard/region question with validated reporting, an exposure denominator and a physically motivated climate indicator.

## Sources

- [NOAA Storm Events bulk data](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/) and [field definitions](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/Storm-Data-Bulk-csv-Format.pdf).
- [NOAA ERSSTv5](https://psl.noaa.gov/data/gridded/data.noaa.ersst.v5.html), monthly 2° grid; 1991–2020 anomaly baseline; regional box 20–50°N, 130–60°W; cosine-latitude spatial weights and day-weighted annual means.
- [BLS historical CPI-U](https://www.bls.gov/cpi/tables/supplemental-files/historical-cpi-u-202412.pdf), annual US city average, all items, not seasonally adjusted; 2024 dollars.
- [Statsmodels HAC covariance documentation](https://www.statsmodels.org/stable/generated/statsmodels.regression.linear_model.OLSResults.get_robustcov_results.html).
