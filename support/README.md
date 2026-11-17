# Supporting methods and files

The [main notebook](../Extreme_Weather_Final%20Project.ipynb) is the reading version. This folder holds the calculations, detailed results and checks.

## Reproduce

From the repository root, with Python 3.12:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r support/requirements.txt
python -m unittest discover -s support -p 'test_*.py' -v
python support/execute_notebook.py
```

The notebook calls `support/weather_analysis.py`. Its runner executes all code cells in-process and saves their actual outputs, without requiring a networked Jupyter kernel. A Jupyter interface can also run the notebook using the same environment. To run only the calculations and figure generation, use `python support/weather_analysis.py`.

Raw files are cached in `data/` at the repository root; figures are written to `figures/`; both are excluded from Git. Tables are written to `support/results/`. The initial download is about 453 MB.

### Data revisions

`data_manifest.json` records exact NOAA filenames, URLs, retrieval times and SHA-256 hashes. Every run verifies the cached bytes. Retain the raw cache for exact long-term replication: NOAA may remove old storm revisions, and the SST URL is mutable.

A changed file causes a checksum error. To deliberately accept a newly downloaded SST release, run `python support/weather_analysis.py --accept-updated-sst`, then rerun the notebook. This accepts the cached file and does not force a new download. Storm revisions require deliberate manifest changes. After any data change, update the notebook's numerical prose to match the regenerated tables before sharing it; the reading version uses ordinary Markdown for those paragraphs.

## Method details

### Records and dates

The sample includes county and forecast-zone records from the 48 contiguous states and DC. `EVENT_ID` identifies records; `EPISODE_ID` is retained for inspection, not assumed to identify nationally independent storms. Exact duplicate rows are removed, while conflicting event IDs and invalid dates stop the run. Recorded start dates determine year and month. Source-year disagreements are exported without inventing replacement dates.

The coarser sensitivity unit collapses state, hazard group and start date. It can merge distinct storms and does not measure every day affected by long-duration events. Heat and Drought are separate. Tornado excludes funnel clouds and waterspouts; Flood / Rain includes heavy rain; Tropical / Surge includes storm surge. The full mapping is exported.

### SST

The regional series uses the 20–50°N, 130–60°W box, a 1991–2020 calendar-month baseline, cosine-latitude weights over valid ocean cells, and day-weighted annual means. The code checks all 408 months in 1991–2024. The context map compares equally weighted monthly means for two ten-year periods; it is not a significance map.

### Annual models

Trend models regress annual counts on centered year. SST models include both SST and centered year. HAC covariance uses a Bartlett kernel, two annual lags, finite-sample correction and t-based intervals. With 29 observations, these intervals remain approximate. Trend bands describe the fitted mean, not future observations.

The ten named hazards receive Holm correction separately within the trend family and the SST-association family. Total, Other and the alternate counting unit are outside those corrections. Raw, detrended and first-difference correlations are descriptive; independent-year Pearson p-values are not used.

Sensitivity checks cover HAC lags 1–3, quadratic time, first differences and leave-one-year-out coefficients. Deleting one year makes spacing irregular, so leave-one-year-out confidence intervals are not interpreted. Residual lag-one correlations are a limited diagnostic. Time adjustment does not resolve reporting changes, exposure or omitted physical processes.

### Seasonal comparison

Each year's 12 monthly counts are divided by that year's total, then the annual vectors are averaged within 1996–2010 and 2011–2024. Both periods give each year equal weight. The difference is late minus early, in percentage points.

The bootstrap resamples non-circular moving blocks of complete annual vectors within each period, truncates to the original period length and takes 4,000 draws with seed 42. Two-year blocks are primary; three-year blocks are a sensitivity check. The 95% percentile intervals are pointwise, not simultaneous. They assume approximate stability within each period and short-range dependence. Hazard-specific profiles are descriptive and report the number of observed years.

### Damage

Missing and invalid strings remain missing; explicit zeros remain zero. Available-component totals include either property or crop estimates when known. Complete-case totals require both. Annual CPI-U converts values to 2024 dollars. The period table reports annual means and medians, avoiding unequal-length totals.

Missingness changes sharply around 2007. CPI adjustment does not normalize exposed wealth, population or vulnerability. Source estimates may contain errors and dominate totals; the largest records are exported without automatic replacement or winsorization. The sums are not comprehensive economic loss or an unbiased lower bound.

## Supplementary tables

| Topic | Files |
| --- | --- |
| Annual counts and trends | [annual](results/annual.csv), [trends](results/trends.csv), [state comparison](results/state_summary.csv) |
| SST relationships | [associations](results/sst_associations.csv), [specification checks](results/sst_sensitivity.csv), [leave-one-year-out](results/leave_one_year_out.csv) |
| Seasonality | [annual monthly shares](results/monthly_shares.csv), [period differences](results/seasonal_differences.csv), [hazard profiles](results/hazard_seasonal_profiles.csv) |
| Reported damage | [annual totals and coverage](results/annual_damage.csv), [period comparison](results/damage_periods.csv), [largest records](results/largest_damage_records.csv), [CPI](results/cpi_u.csv) |
| Data checks | [quality summary](results/data_quality.json), [event mapping](results/event_type_mapping.csv), [date discrepancies](results/date_audit.csv), [damage parsing](results/damage_parse_audit.csv), [versions](results/package_versions.json) |

[Methodological revision history](REVISION_NOTES.md) · [Validation record](VALIDATION.md)
