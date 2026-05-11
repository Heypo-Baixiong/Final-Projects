# Extreme Weather in a Warming World

This notebook investigates how the frequency, seasonality, and economic impact of severe weather events in the United States have changed over 1996–2024, and whether year-to-year variation in event counts tracks year-to-year variation in U.S.-adjacent ocean temperatures.

## Scientific question and hypotheses

The overall question is whether U.S. severe weather has become more frequent and more costly as the climate has warmed, and what the climate signal looks like once reporting-practice changes and inflation are factored out. I test three hypotheses:

1. The annual count of reported severe-weather events has increased significantly across 1996–2024.
2. The seasonal distribution of events has shifted, with a larger share of events occurring in late spring and early summer in the late period than in the early period.
3. Annual SST anomalies over the U.S.-adjacent ocean basins are positively correlated with annual event counts.

## Datasets

- **NOAA Storm Events Database** (per-event records, 1996–2024) — https://www.ncei.noaa.gov/pub/data/swdi/stormevents/csvfiles/
- **NOAA ERSSTv5** (monthly extended reconstructed sea-surface temperature, 2°×2° grid) — https://psl.noaa.gov/data/gridded/data.noaa.ersst.v5.html
- **U.S. state boundaries** (public-domain GeoJSON) — https://github.com/PublicaMundi/MappingAPI

All three are downloaded programmatically from inside the notebook; nothing is loaded from a local path.

## Analysis summary

I download the Storm Events files for each year and clean them into a single Pandas DataFrame, parsing damage strings into floats, converting dates, and collapsing the 50+ raw event types into nine working categories. ERSSTv5 is loaded with Xarray and reduced to an area-weighted annual SST anomaly time series over the U.S.-adjacent ocean basins, using a 1991–2020 climatology. The three hypotheses are then tested with linear regression (with 95% confidence bands), a chi-square test comparing the early and late halves of the seasonal distribution, and a Pearson correlation between annual SST anomalies and annual event counts.
