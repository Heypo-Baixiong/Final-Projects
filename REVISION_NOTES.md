# Methodological revision

The revised project supports discussion of data handling, quantitative methods and research design. It remains exploratory, with reporting and causal-identification problems stated openly.

| Original issue | Revision | Remaining limitation |
| --- | --- | --- |
| Reports described as disaster frequency | Retain identifiers; label counts as records; add state–hazard–start-day sensitivity | Neither counting unit identifies all independent storms |
| All-location counts alongside a CONUS geographic view | Use 48 contiguous states plus DC consistently | Alaska, Hawaii, territories and offshore regions are excluded |
| Tornado grouped with funnel clouds/waterspouts; Heat combined with Drought | Restrict Tornado; separate Heat and Drought; export the mapping | Categories still combine heterogeneous processes |
| Raw annual SST correlation used as climate evidence | Add a year term, detrending, HAC intervals, first differences and specification checks | Time adjustment cannot establish causality |
| Many hazard tests without multiplicity adjustment | Holm correction within each ten-hazard family | Tests remain exploratory; measurement bias remains |
| Pooled-record seasonal chi-square test | Equal-weight yearly shares; bootstrap whole annual vectors in blocks | Short periods, stationarity assumptions and hazard composition remain concerns |
| Missing losses treated as zero | Preserve unknowns; report coverage and complete-case sensitivity | Missingness changes sharply over time |
| Unequal-length period totals compared | Annual means and medians, with period lengths | Exposure and vulnerability are not normalized |
| Automatically selecting the latest sources | Exact filenames and hashes; explicit acceptance of changed SST | Exact reruns require source bytes if NOAA removes a revision |
| Conclusions could retain obsolete numbers | Generate numerical conclusions from executed outputs | Interpretation still requires substantive review |

## Data audit

The revised snapshot has 1,708,370 source records; 1,627,967 meet the geographic and record-type scope. There are no exact duplicate rows or conflicting event IDs. Three retained records lack an episode ID. Eight records have a source YEAR different from their recorded start year; the start dates are retained and discrepancies exported. Forty-four property strings and five crop strings fail parsing and remain missing.

These values describe the committed snapshot. `results/data_quality.json` is authoritative after a future rerun.

## Discussing the project with a faculty adviser

“This started as a course project using NOAA storm reports and sea-surface temperature data. The original analysis relied too much on raw counts and correlations. The revised version makes the counting unit explicit, checks shared time trends and serial correlation, and treats years as the unit for the seasonal comparison. The results change after detrending, so I would present this as exploratory evidence rather than climate attribution. I would like your advice on narrowing it to one hazard and choosing a more defensible research design.”

Before presenting, be able to explain the data pipeline, why records are not independent storms, the difference between raw and detrended correlation, what HAC does, and why missing damage is not zero.
