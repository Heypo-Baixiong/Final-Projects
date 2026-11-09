"""Reproducible, descriptive analysis of NOAA weather reports, 1996–2024.

Run from the repository root: python weather_analysis.py
The notebook uses the same functions. No causal effect is estimated.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.metadata
import json
import urllib.request

import numpy as np
import pandas as pd
import scipy.stats as st
import statsmodels.api as sm
from statsmodels.stats.multitest import multipletests
import xarray as xr
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
YEARS = np.arange(1996, 2025)
RESULTS = ROOT / "results"
FIGURES = ROOT / "figures"
SEED = 42
CONUS = set("""ALABAMA|ARIZONA|ARKANSAS|CALIFORNIA|COLORADO|CONNECTICUT|
DELAWARE|DISTRICT OF COLUMBIA|FLORIDA|GEORGIA|IDAHO|ILLINOIS|INDIANA|IOWA|
KANSAS|KENTUCKY|LOUISIANA|MAINE|MARYLAND|MASSACHUSETTS|MICHIGAN|MINNESOTA|
MISSISSIPPI|MISSOURI|MONTANA|NEBRASKA|NEVADA|NEW HAMPSHIRE|NEW JERSEY|
NEW MEXICO|NEW YORK|NORTH CAROLINA|NORTH DAKOTA|OHIO|OKLAHOMA|OREGON|
PENNSYLVANIA|RHODE ISLAND|SOUTH CAROLINA|SOUTH DAKOTA|TENNESSEE|TEXAS|UTAH|
VERMONT|VIRGINIA|WASHINGTON|WEST VIRGINIA|WISCONSIN|WYOMING""".replace("\n", "").split("|"))
CATEGORIES = {
    "Tornado": ["Tornado"],
    "Flood / Rain": ["Flood", "Flash Flood", "Coastal Flood", "Lakeshore Flood", "Heavy Rain"],
    "Hail": ["Hail"],
    "Severe Wind": ["Thunderstorm Wind", "High Wind", "Strong Wind"],
    "Heat": ["Heat", "Excessive Heat"],
    "Drought": ["Drought"],
    "Winter / Cold": ["Cold/Wind Chill", "Extreme Cold/Wind Chill", "Winter Storm",
                      "Winter Weather", "Heavy Snow", "Blizzard", "Ice Storm", "Sleet",
                      "Frost/Freeze", "Lake-Effect Snow"],
    "Tropical / Surge": ["Hurricane", "Hurricane (Typhoon)", "Tropical Storm",
                         "Tropical Depression", "Storm Surge/Tide"],
    "Lightning": ["Lightning"],
    "Wildfire": ["Wildfire"],
}
LOOKUP = {raw.casefold(): group for group, names in CATEGORIES.items() for raw in names}
# Annual, non-seasonally-adjusted CPI-U, all items, US city average (1982–84=100).
# https://www.bls.gov/cpi/tables/supplemental-files/historical-cpi-u-202412.pdf
CPI = dict(zip(YEARS, [156.9, 160.5, 163.0, 166.6, 172.2, 177.1, 179.9, 184.0,
    188.9, 195.3, 201.6, 207.342, 215.303, 214.537, 218.056, 224.939, 229.594,
    232.957, 236.736, 237.017, 240.007, 245.120, 251.107, 255.657, 258.811,
    270.970, 292.655, 304.702, 313.689]))


def sha256(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def fetch_inputs(accept_updated_sst=False):
    """Download pinned revisions and verify bytes, including cached inputs.

    NOAA's SST URL is mutable. A changed SST file requires explicit acceptance;
    accepting it updates the manifest and requires rerunning all results.
    """
    manifest_path = ROOT / "data_manifest.json"
    manifest = json.loads(manifest_path.read_text())
    for item in manifest["files"]:
        path = ROOT / item["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            partial = path.with_suffix(path.suffix + ".part")
            print(f"Downloading {path.name}", flush=True)
            urllib.request.urlretrieve(item["url"], partial)
            partial.replace(path)
        actual = sha256(path)
        if actual != item["sha256"]:
            if item["kind"] == "sst" and accept_updated_sst:
                item.update(sha256=actual, bytes=path.stat().st_size,
                            retrieved_utc=pd.Timestamp.now(tz="UTC").isoformat())
                manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
            else:
                raise ValueError(f"Checksum mismatch: {path}. Do not mix data revisions. "
                                 "For a changed NOAA SST release, explicitly rerun with "
                                 "--accept-updated-sst and regenerate every output.")
    return manifest


def parse_damage(series):
    """Keep unknown/invalid values missing. Explicit zero is a valid zero."""
    text = series.astype("string").str.strip().str.upper()
    parts = text.str.extract(r"^(\d+(?:\.\d*)?|\.\d+)\s*([HKMBT]?)$")
    scale = parts[1].map({"": 1, "H": 100, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12})
    values = pd.to_numeric(parts[0], errors="coerce") * scale
    invalid = text.notna() & text.ne("") & values.isna()
    return values.astype(float), invalid.fillna(False)


def load_storms(manifest):
    columns = ["EVENT_ID", "EPISODE_ID", "STATE", "CZ_TYPE", "CZ_FIPS", "YEAR",
               "BEGIN_YEARMONTH", "BEGIN_DAY", "BEGIN_DATE_TIME", "END_DATE_TIME",
               "EVENT_TYPE", "DAMAGE_PROPERTY", "DAMAGE_CROPS"]
    frames = []
    for item in manifest["files"]:
        if item["kind"] != "storm":
            continue
        frame = pd.read_csv(ROOT / item["path"], usecols=columns, encoding="latin-1",
                            dtype={"DAMAGE_PROPERTY": "string", "DAMAGE_CROPS": "string"})
        if not frame.YEAR.eq(item["year"]).all():
            raise ValueError(f"File/year mismatch: {item['path']}")
        frames.append(frame)
    raw = pd.concat(frames, ignore_index=True)
    if raw.EVENT_ID.isna().any():
        raise ValueError("Missing EVENT_ID: resolve before counting records.")
    before = len(raw)
    raw = raw.drop_duplicates()  # exact duplicate rows only
    if raw.EVENT_ID.duplicated().any():
        raise ValueError("Conflicting rows share EVENT_ID; inspect rather than silently drop.")
    raw["STATE"] = raw.STATE.str.strip().str.upper()
    storms = raw.loc[raw.STATE.isin(CONUS) & raw.CZ_TYPE.isin(["C", "Z"])].copy()
    storms["date"] = pd.to_datetime(dict(year=storms.BEGIN_YEARMONTH // 100,
        month=storms.BEGIN_YEARMONTH % 100, day=storms.BEGIN_DAY), errors="coerce")
    if storms.date.isna().any():
        raise ValueError("Invalid event start dates; inspect before analysis.")
    storms["year"] = storms.date.dt.year
    storms["month"] = storms.date.dt.month
    if set(storms.year) != set(YEARS):
        raise ValueError("At least one study year is absent.")
    label = storms.EVENT_TYPE.str.strip().str.replace(r"\s+", " ", regex=True)
    storms["category"] = label.str.casefold().map(LOOKUP).fillna("Other")
    quality = {"raw_rows": before, "exact_duplicates_removed": before - len(raw),
               "conus_records": len(storms), "excluded_geography_rows": len(raw) - len(storms),
               "missing_episode_ids": int(storms.EPISODE_ID.isna().sum()),
               "source_year_differs_from_start_year": int(storms.year.ne(storms.YEAR).sum())}
    for name, column in [("property", "DAMAGE_PROPERTY"), ("crop", "DAMAGE_CROPS")]:
        storms[name], invalid = parse_damage(storms[column])
        storms[name + "_invalid"] = invalid
        quality[f"invalid_{name}_strings"] = int(invalid.sum())
        quality[f"missing_{name}_values"] = int(storms[name].isna().sum())
    components = storms[["property", "crop"]]
    storms["damage_available"] = components.sum(axis=1, min_count=1)
    storms["damage_complete"] = components.sum(axis=1, min_count=2)
    storms["damage_2024"] = storms.damage_available * storms.year.map(lambda y: CPI[2024] / CPI[y])
    storms["damage_complete_2024"] = storms.damage_complete * storms.year.map(lambda y: CPI[2024] / CPI[y])
    return storms, quality


def load_sst(manifest):
    item = next(i for i in manifest["files"] if i["kind"] == "sst")
    with xr.open_dataset(ROOT / item["path"]) as source:
        sst = source.sst.sel(time=slice("1991-01-01", "2024-12-31")).load()
    sst = sst.assign_coords(lon=((sst.lon + 180) % 360) - 180).sortby("lon").sortby("lat")
    expected = pd.period_range("1991-01", "2024-12", freq="M")
    observed = pd.DatetimeIndex(sst.time.values).to_period("M")
    if not observed.equals(expected):
        raise ValueError("Missing, duplicate or out-of-order SST months.")
    baseline = sst.sel(time=slice("1991", "2020")).groupby("time.month").mean("time")
    anomaly = sst.groupby("time.month") - baseline
    region = anomaly.sel(lat=slice(20, 50), lon=slice(-130, -60))
    weights = np.cos(np.deg2rad(region.lat))
    monthly = region.weighted(weights).mean(("lat", "lon"))
    days = monthly.time.dt.days_in_month
    annual = ((monthly * days).groupby("time.year").sum("time") /
              days.groupby("time.year").sum("time")).sel(year=YEARS)
    if not np.isfinite(annual.values).all():
        raise ValueError("Non-finite regional annual SST.")
    series = pd.Series(annual.values, index=YEARS, name="sst_anomaly_c")
    # Display a difference of decadal means; no significance is inferred from this map.
    contrast = (sst.sel(time=slice("2015", "2024")).mean("time") -
                sst.sel(time=slice("1996", "2005")).mean("time"))
    return series, contrast


def annual_counts(storms):
    counts = storms.groupby(["year", "category"]).size().unstack(fill_value=0)
    counts = counts.reindex(index=YEARS, columns=[*CATEGORIES, "Other"], fill_value=0)
    counts["Total"] = counts.sum(axis=1)
    # A sensitivity unit, NOT a unique physical storm: several distinct storms may
    # occur in the same state/day/category, and long events may span many days.
    coarse = storms.drop_duplicates(["STATE", "category", "date"])
    days = coarse.groupby("year").size().reindex(YEARS, fill_value=0)
    return counts, days.rename("state_hazard_start_days")


def hac_model(y, predictors, lag=2):
    design = sm.add_constant(pd.DataFrame(predictors), has_constant="add")
    return sm.OLS(np.asarray(y, dtype=float), design).fit(
        cov_type="HAC", cov_kwds={"maxlags": lag, "use_correction": True}, use_t=True)


def coefficient(model, variable):
    interval = model.conf_int().loc[variable]
    return {"estimate": float(model.params[variable]), "ci_low": float(interval.iloc[0]),
            "ci_high": float(interval.iloc[1]), "p_hac": float(model.pvalues[variable])}


def detrend(values):
    x = sm.add_constant(np.arange(len(values)))
    return sm.OLS(np.asarray(values, dtype=float), x).fit().resid


def analyze_relationships(counts, days, sst):
    time = YEARS - YEARS.mean()
    trends, associations = [], []
    outcomes = {name: counts[name] for name in counts.columns}
    outcomes[days.name] = days
    for name, y in outcomes.items():
        trend = hac_model(y, {"year": time})
        trends.append({"outcome": name, **coefficient(trend, "year")})
        adjusted = hac_model(y, {"sst": sst.values, "year": time})
        associations.append({"outcome": name, "n_years": len(y),
            "raw_r": float(st.pearsonr(sst, y).statistic),
            "detrended_r": float(st.pearsonr(detrend(sst), detrend(y)).statistic),
            "first_difference_r": float(st.pearsonr(np.diff(sst), np.diff(y)).statistic),
            **coefficient(adjusted, "sst"),
            "residual_lag1_r": float(pd.Series(adjusted.resid).autocorr(1))})
    trends = pd.DataFrame(trends)
    associations = pd.DataFrame(associations)
    # Ten pre-specified hazard groups constitute one exploratory testing family.
    # Total, Other and the alternate counting unit are not part of that family.
    for table in (trends, associations):
        selected = table.outcome.isin(CATEGORIES)
        table.loc[selected, "p_holm_10_hazards"] = multipletests(
            table.loc[selected, "p_hac"], method="holm")[1]
    sensitivity = []
    for lag in (1, 2, 3):
        model = hac_model(counts.Total, {"sst": sst.values, "year": time}, lag)
        sensitivity.append({"check": f"HAC lag {lag}", **coefficient(model, "sst")})
    # First differences reduce shared linear drift but amplify measurement noise.
    model = hac_model(np.diff(counts.Total), {"sst": np.diff(sst)}, lag=2)
    sensitivity.append({"check": "First differences, HAC lag 2", **coefficient(model, "sst")})
    model = hac_model(counts.Total, {"sst": sst.values, "year": time, "year_squared": time ** 2})
    sensitivity.append({"check": "Quadratic time trend, HAC lag 2", **coefficient(model, "sst")})
    leave_one_out = []
    for i, year in enumerate(YEARS):
        keep = np.arange(len(YEARS)) != i
        model = hac_model(counts.Total.values[keep],
                          {"sst": sst.values[keep], "year": time[keep]})
        # Only coefficients: deleting a year makes HAC spacing irregular.
        leave_one_out.append({"excluded_year": int(year), "sst_slope": float(model.params["sst"])})
    return trends, associations, pd.DataFrame(sensitivity), pd.DataFrame(leave_one_out)


def block_means(array, block_length, rng, repetitions):
    """Non-circular moving blocks of complete annual 12-month vectors."""
    n = len(array)
    starts = rng.integers(0, n - block_length + 1,
                          size=(repetitions, int(np.ceil(n / block_length))))
    indices = (starts[..., None] + np.arange(block_length)).reshape(repetitions, -1)[:, :n]
    return array[indices].mean(axis=1)


def seasonality(storms, repetitions=4000):
    monthly = storms.groupby(["year", "month"]).size().unstack(fill_value=0)
    monthly = monthly.reindex(index=YEARS, columns=range(1, 13), fill_value=0)
    shares = monthly.div(monthly.sum(axis=1), axis=0)
    early, late = shares.loc[1996:2010].values, shares.loc[2011:2024].values
    rows = []
    for length in (2, 3):
        rng = np.random.default_rng(SEED)
        draws = (block_means(late, length, rng, repetitions) -
                 block_means(early, length, rng, repetitions)) * 100
        low, high = np.quantile(draws, [.025, .975], axis=0)
        for month in range(12):
            rows.append({"month": month + 1, "block_years": length,
                "early_share_pct": early.mean(axis=0)[month] * 100,
                "late_share_pct": late.mean(axis=0)[month] * 100,
                "difference_pp": (late.mean(axis=0)[month] - early.mean(axis=0)[month]) * 100,
                "pointwise_ci_low": low[month], "pointwise_ci_high": high[month]})
    # Hazard-specific descriptive profiles help distinguish timing from composition.
    detailed = storms.groupby(["category", "year", "month"]).size().unstack(fill_value=0)
    detailed = detailed.reindex(columns=range(1, 13), fill_value=0)
    detailed = detailed.div(detailed.sum(axis=1), axis=0)
    profile = detailed.stack().rename("share").reset_index()
    profile["period"] = np.where(profile.year <= 2010, "1996–2010", "2011–2024")
    profile = profile.groupby(["category", "period", "month"]).agg(
        mean_share=("share", "mean"), years_observed=("year", "nunique")).reset_index()
    return shares, pd.DataFrame(rows), profile


def damage_tables(storms):
    annual = storms.groupby("year").agg(
        reports=("EVENT_ID", "size"), property_known=("property", "count"),
        crop_known=("crop", "count"), any_component_known=("damage_available", "count"),
        both_components_known=("damage_complete", "count"),
        available_damage_2024=("damage_2024", lambda x: x.sum(min_count=1)),
        complete_case_damage_2024=("damage_complete_2024", lambda x: x.sum(min_count=1)))
    for column in ["property_known", "crop_known", "any_component_known", "both_components_known"]:
        annual[column + "_share"] = annual[column] / annual.reports
    periods = []
    for lo, hi in [(1996, 1999), (2000, 2009), (2010, 2019), (2020, 2024)]:
        sub = annual.loc[lo:hi]
        periods.append({"period": f"{lo}–{hi}", "years": len(sub),
            "mean_annual_available_2024": sub.available_damage_2024.mean(),
            "median_annual_available_2024": sub.available_damage_2024.median(),
            "mean_annual_complete_case_2024": sub.complete_case_damage_2024.mean()})
    top = storms.nlargest(15, "damage_2024")[["EVENT_ID", "EPISODE_ID", "date", "STATE",
        "EVENT_TYPE", "DAMAGE_PROPERTY", "DAMAGE_CROPS", "damage_2024"]]
    return annual, pd.DataFrame(periods), top


def run_analysis(accept_updated_sst=False):
    RESULTS.mkdir(exist_ok=True)
    FIGURES.mkdir(exist_ok=True)
    manifest = fetch_inputs(accept_updated_sst)
    storms, quality = load_storms(manifest)
    sst, contrast = load_sst(manifest)
    counts, days = annual_counts(storms)
    trends, associations, sensitivity, loo = analyze_relationships(counts, days, sst)
    shares, seasonal, profiles = seasonality(storms)
    damage, periods, top = damage_tables(storms)
    annual = counts.join(days).join(sst)
    mapping = storms.groupby(["EVENT_TYPE", "category"]).size().rename("records").reset_index()
    state = storms.groupby("STATE").size().sort_values(ascending=False).rename("records").to_frame()
    state["reports_per_year"] = state.records / len(YEARS)
    state["state_hazard_start_days_per_year"] = (storms.drop_duplicates(["STATE", "category", "date"])
        .groupby("STATE").size() / len(YEARS))
    date_audit = storms.loc[storms.year.ne(storms.YEAR), ["EVENT_ID", "STATE", "EVENT_TYPE",
        "YEAR", "date", "BEGIN_DATE_TIME", "END_DATE_TIME"]]
    damage_audit = storms.loc[storms.property_invalid | storms.crop_invalid,
        ["EVENT_ID", "year", "STATE", "EVENT_TYPE", "DAMAGE_PROPERTY", "DAMAGE_CROPS",
         "property_invalid", "crop_invalid"]]
    tables = {"annual": annual, "trends": trends, "sst_associations": associations,
        "sst_sensitivity": sensitivity, "leave_one_year_out": loo,
        "monthly_shares": shares, "seasonal_differences": seasonal,
        "hazard_seasonal_profiles": profiles, "annual_damage": damage,
        "damage_periods": periods, "largest_damage_records": top,
        "event_type_mapping": mapping, "state_summary": state, "date_audit": date_audit,
        "damage_parse_audit": damage_audit}
    indexed = {"annual", "monthly_shares", "annual_damage", "state_summary"}
    for name, table in tables.items():
        table.to_csv(RESULTS / f"{name}.csv", index=name in indexed)
    (RESULTS / "data_quality.json").write_text(json.dumps(quality, indent=2) + "\n")
    versions = {p: importlib.metadata.version(p) for p in ["numpy", "pandas", "scipy", "xarray",
        "netCDF4", "statsmodels", "matplotlib", "nbformat", "nbclient", "ipykernel"]}
    (RESULTS / "package_versions.json").write_text(json.dumps(versions, indent=2) + "\n")
    pd.Series(CPI, name="cpi_u_annual").rename_axis("year").to_csv(RESULTS / "cpi_u.csv")
    print(f"Analyzed {len(storms):,} CONUS records over {len(YEARS)} years.")
    return {**tables, "quality": quality, "contrast": contrast}


def save_figure(fig, name):
    fig.savefig(FIGURES / f"{name}.png", dpi=140, bbox_inches="tight")
    return fig


def make_figures(result):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False,
                         "axes.spines.right": False, "figure.dpi": 110})
    figures = []
    annual = result["annual"]
    fig, ax = plt.subplots(figsize=(10, 4), layout="constrained")
    result["contrast"].plot(ax=ax, cmap="RdBu_r", vmin=-2, vmax=2,
        cbar_kwargs={"label": "SST difference (°C)"})
    from matplotlib.patches import Rectangle
    ax.add_patch(Rectangle((-130, 20), 70, 30, fill=False, ec="black", lw=1.5))
    ax.set(title="Mean SST: 2015–2024 minus 1996–2005", xlabel="Longitude", ylabel="Latitude")
    figures.append(save_figure(fig, "01_sst_context"))

    fig, axes = plt.subplots(4, 3, figsize=(12, 10), layout="constrained")
    for ax, name in zip(axes.flat, ["Total", *CATEGORIES, "Other"]):
        y = annual[name]
        fit = hac_model(y, {"year": YEARS - YEARS.mean()})
        prediction = fit.get_prediction().summary_frame()
        ax.plot(YEARS, y, color="#28688c", lw=1.3)
        ax.plot(YEARS, fit.fittedvalues, color="#c65b28", lw=1.2)
        ax.fill_between(YEARS, prediction.mean_ci_lower, prediction.mean_ci_upper,
                        color="#c65b28", alpha=.15)
        ax.set_title(name, fontsize=10)
        ax.ticklabel_format(axis="y", style="sci", scilimits=(0, 4))
    fig.suptitle("Reported records by year · linear fit and pointwise 95% HAC mean intervals")
    fig.supylabel("Database records (not independent storms)")
    figures.append(save_figure(fig, "02_annual_reports"))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    sub = result["seasonal_differences"].query("block_years == 2")
    axes[0].plot(sub.month, sub.early_share_pct, "o-", label="1996–2010 (15 years)")
    axes[0].plot(sub.month, sub.late_share_pct, "o-", label="2011–2024 (14 years)")
    axes[0].set(xlabel="Start month", ylabel="Mean annual share (%)", title="Each year receives equal weight")
    axes[0].legend(fontsize=8)
    axes[1].vlines(sub.month, sub.pointwise_ci_low, sub.pointwise_ci_high, color="#28688c")
    axes[1].plot(sub.month, sub.difference_pp, "o", color="#28688c")
    axes[1].axhline(0, color="gray", lw=1)
    axes[1].set(xlabel="Start month", ylabel="Late minus early (percentage points)",
                title="Pointwise 95% moving-block bootstrap intervals")
    for ax in axes:
        ax.set_xticks(range(1, 13))
    figures.append(save_figure(fig, "03_seasonality"))

    fig, axes = plt.subplots(1, 2, figsize=(11, 6), layout="constrained")
    sub = result["state_summary"].head(15).iloc[::-1]
    axes[0].barh(sub.index.str.title(), sub.reports_per_year, color="#28688c")
    axes[1].barh(sub.index.str.title(), sub.state_hazard_start_days_per_year, color="#a36e35")
    axes[0].set(title="Average reports per year", xlabel="Records")
    axes[1].set(title="Same states, coarser counting unit", xlabel="State–hazard–start-day combinations per year")
    axes[1].set_xlim(0, sub.state_hazard_start_days_per_year.max() * 1.18)
    fig.suptitle("Top 15 states by report count · not adjusted for area, population or exposure")
    figures.append(save_figure(fig, "04_geographic_counts"))

    fig, axes = plt.subplots(2, 1, figsize=(10, 5), sharex=True, layout="constrained")
    for name, label in [("Total", "Reports"), ("state_hazard_start_days", "State–hazard–start-days")]:
        z = (annual[name] - annual[name].mean()) / annual[name].std()
        axes[0].plot(YEARS, z, label=label)
    axes[0].set(ylabel="Standard deviations", title="Counting-unit sensitivity")
    axes[0].legend(fontsize=8)
    axes[1].plot(YEARS, annual.sst_anomaly_c, color="#c65b28")
    axes[1].axhline(0, color="gray", lw=.7)
    axes[1].set(xlabel="Year", ylabel="SST anomaly (°C)", title="20–50°N, 130–60°W · 1991–2020 baseline")
    figures.append(save_figure(fig, "05_time_series"))

    fig, axes = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    row = result["sst_associations"].set_index("outcome").loc["Total"]
    for ax, x, y, title in [(axes[0], annual.sst_anomaly_c, annual.Total, f"Raw association: r = {row.raw_r:.3f}"),
                            (axes[1], detrend(annual.sst_anomaly_c), detrend(annual.Total),
                             f"Linear trends removed: r = {row.detrended_r:.3f}")]:
        dots = ax.scatter(x, y, c=YEARS, cmap="viridis", s=32)
        slope, intercept = np.polyfit(x, y, 1)
        xx = np.array([min(x), max(x)])
        ax.plot(xx, intercept + slope * xx, color="#c65b28")
        ax.set_title(title)
    axes[0].set(xlabel="SST anomaly (°C)", ylabel="Annual reports")
    axes[1].set(xlabel="Detrended SST (°C)", ylabel="Detrended annual reports")
    fig.colorbar(dots, ax=list(axes), label="Year", shrink=.8)
    figures.append(save_figure(fig, "06_sst_association"))

    fig, axes = plt.subplots(3, 1, figsize=(10, 9), layout="constrained")
    damage = result["annual_damage"]
    axes[0].plot(YEARS, damage.available_damage_2024 / 1e9, "o-", label="Available components")
    axes[0].plot(YEARS, damage.complete_case_damage_2024 / 1e9, "--", label="Both components known")
    axes[0].set(ylabel="Billion 2024 dollars", title="Reported property and crop damage · CPI adjusted")
    axes[0].legend(fontsize=8)
    axes[1].plot(YEARS, damage.any_component_known_share * 100, label="At least one component")
    axes[1].plot(YEARS, damage.both_components_known_share * 100, label="Both components")
    axes[1].set(ylabel="Records with values (%)", xlabel="Year", ylim=(0, 105))
    axes[1].legend(fontsize=8)
    periods = result["damage_periods"]
    axes[2].bar(periods.period, periods.mean_annual_available_2024 / 1e9, color="#28688c")
    axes[2].set(ylabel="Billion 2024 dollars / year", title="Mean annual reported damage, not period totals")
    for i, row in periods.iterrows():
        axes[2].text(i, row.mean_annual_available_2024 / 1e9, f"n = {row.years} years", ha="center", va="bottom")
    axes[2].margins(y=.18)
    figures.append(save_figure(fig, "07_reported_damage"))
    return figures


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--accept-updated-sst", action="store_true")
    args = parser.parse_args()
    result = run_analysis(args.accept_updated_sst)
    make_figures(result)
    print(result["sst_associations"].set_index("outcome").loc[["Total", "state_hazard_start_days"]].to_string())
