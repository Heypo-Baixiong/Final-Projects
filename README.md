# U.S. Severe-Weather Reports, 1996–2024

This notebook examines the frequency, seasonality, SST associations, and recorded damages of NOAA Storm Events reports. It retains the original nine working hazard categories, original database scope, and seven-figure sequence. A report is a local database entry; an episode groups related entries and is not necessarily one independent physical storm.

## Scientific question and hypotheses

The question is what these records show about changes in reported severe weather, once counting units, documented reporting rules, and uncertainty are made explicit.

1. **H1:** Annual report counts increased over 1996–2024.
2. **H2:** The May–June share increased in 2011–2024 relative to 1996–2010.
3. **H3:** Annual report counts are positively associated with annual SST anomalies over the broad U.S.-adjacent ocean box.

## Datasets

- [NOAA Storm Events Database](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/): local event reports, 1996–2024; [field definitions](https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/Storm-Data-Bulk-csv-Format.pdf).
- [NOAA ERSSTv5](https://psl.noaa.gov/data/gridded/data.noaa.ersst.v5.html): monthly SST on a 2° grid, with a 1991–2020 anomaly baseline.
- [U.S. state boundaries](https://github.com/PublicaMundi/MappingAPI): GeoJSON for the CONUS map and land-only Gulf sensitivity checks.

The notebook downloads and caches the inputs. Run all cells in order with NumPy, Pandas, SciPy, statsmodels, Xarray, netCDF4, Matplotlib, Seaborn, GeoPandas, and PyProj installed. NOAA can revise its yearly files, so exact results also depend on the downloaded file versions.

## Analysis summary

**H1 is supported for report counts:** the full-period slope is 777 reports/year (95% HAC interval 567 to 987). The notebook uses HAC uncertainty, category-wise Holm correction, episode audits, and a 2010 hail level/slope break test with a constant ≥1-inch comparison. Episode counts fall abruptly around 2006–2007, so recent report/episode comparisons use 2007–2024; neither recent total trend interval excludes zero. Counts should not be interpreted as independent storm frequency.

**H2 as stated is not supported:** the May–June share decreases by 2.94 percentage points (three-year-block 95% interval -4.72 to -1.18). July–August increases by 2.49 points, but its block interval includes zero. Whole-year and block bootstraps preserve each annual monthly profile; simultaneous monthly intervals address the twelve-month comparison.

**H3 is not supported as stated:** raw r=0.289, linearly detrended r=-0.636, and first-difference r=-0.269. The negative year-adjusted slope remains distinguishable from zero with HAC uncertainty, but evidence weakens after allowing a 2014 level shift or using differences. Gulf seasonal checks match spring hail/tornado and summer wind reports to the same season's SST; none of nine exploratory comparisons survives Holm correction. The notebook documents these specifications without treating them as causal estimates.

**Figure 7 describes incomplete recorded loss sums.** Annual coverage of at least one damage component ranges from 25.5% to 93.6%. The 2022 all-report sum is $21.82 billion in 2022 dollars, versus $112.9 billion for Ian alone in the NHC/NCEI assessment, which uses a broader accounting system. Neither inflation adjustment nor annualizing unequal periods corrects incomplete losses; the figure supports no national loss-trend conclusion. The notebook links the NWS reporting rules, hail-threshold notice, relevant studies, and Ian report alongside their interpretations.
