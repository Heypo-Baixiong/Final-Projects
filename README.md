# U.S. Severe-Weather Reports, 1996–2024

[Open the notebook](Extreme_Weather_Final%20Project.ipynb).

This project examines NOAA Storm Events reports alongside sea-surface temperature. Its main finding is that measurement choices can change the sign of a result: holding hail size at ≥1 inch reverses the count trend, while detrending reverses the SST correlation.

## Findings

- **H1 is sensitive to the 2007 transition.** The unadjusted slope is 777 reports/year (95% HAC interval 567 to 987). Adding a 2007 level shift gives 396/year (−88 to 880); the shift is 7,812 reports (−428 to 16,052). Later counts are higher, but the record cannot distinguish gradual growth from a reporting-regime jump. NCEI documents a database migration in October 2006.
- **H2 as stated is not supported.** The May–June share falls by 2.94 percentage points (three-year-block 95% interval −4.72 to −1.18). The July–August increase is less certain.
- **H3 lacks a stable positive association.** Raw r=0.289, detrended r=−0.636, and first-difference r=−0.269. Nine seasonal Gulf comparisons and the post hoc 2014-shift diagnostic appear in the appendix.
- **Recorded damages are not national loss totals.** The 2022 sum is $21.82 billion, less than one-fifth of NCEI's $112.9 billion estimate for Ian alone, in the same year's dollars. Damage-field fill rates change across coding regimes and do not measure comparable completeness.

## Data and methods

The notebook uses [Storm Events bulk files](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/), [ERSSTv5](https://psl.noaa.gov/data/gridded/data.noaa.ersst.v5.html), and [state boundaries](https://github.com/PublicaMundi/MappingAPI). Sources for reporting rules and external benchmarks are linked alongside the analysis. Annual totals retain all database locations; the map shows CONUS, and the exploratory Gulf checks use CONUS land reports.

Methods include report/episode audits, a 2007 level-shift model, a 2010 hail level-and-slope model, HAC uncertainty, and annual-profile block bootstraps. These are descriptive associations, not causal estimates.

## Running the notebook

Run cells in order with NumPy, Pandas, SciPy, statsmodels, Xarray, netCDF4, Matplotlib, matplotlib-inline, Seaborn, GeoPandas, and PyProj installed. Inputs are downloaded and cached in `data/`; the seven figures are saved in `figures/` and embedded in the notebook. NOAA may revise historical files, so exact results depend on the cached versions.
