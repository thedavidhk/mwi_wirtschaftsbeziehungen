"""Generate data-driven SVG figures for the international economics lecture.

This script intentionally stays lightweight: it is meant to be run manually while
preparing lecture slides, not deployed as a package. Still, the code is organized
around reusable data loaders, simple caching, and small plot-specific functions.

The script writes SVG files into the images/ directory. Network data are cached
under data/cache/ so repeated runs are fast and less dependent on external APIs.
"""

from __future__ import annotations

import datetime as dt
import io
import json
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
from pandas.plotting import register_matplotlib_converters
from pandas.tseries.offsets import QuarterEnd

register_matplotlib_converters()

# -----------------------------------------------------------------------------
# Paths and global configuration
# -----------------------------------------------------------------------------

DATA_DIR = Path("data")
IMAGE_DIR = Path("images")
CACHE_DIR = DATA_DIR / "cache"

HTTP_TIMEOUT = 60
CACHE_MAX_AGE_DAYS = 7

PRIMARY_COLORS = [
    "#cc241d",
    "#98971a",
    "#d79921",
    "#458588",
    "#b16286",
    "#689d6a",
    "#d65d0e",
]

SECONDARY_COLORS = [
    "#83a598",
    "#d3869b",
    "#8ec07c",
    "#fabd2f",
    "#b8bb26",
    "#fe8019",
    "#fb4934",
]

plt.rcParams.update(
    {
        "figure.figsize": (10, 6),
        "text.color": "#e6e6e6",
        "figure.facecolor": "#00000000",
        "axes.facecolor": "#00000000",
        "axes.edgecolor": "#333333",
        "axes.labelcolor": "#e6e6e6",
        "axes.labelsize": "large",
        "axes.titlesize": "x-large",
        "xtick.color": "#e6e6e6",
        "xtick.labelsize": "medium",
        "ytick.color": "#e6e6e6",
        "ytick.labelsize": "medium",
        "font.family": "sans-serif",
        "grid.color": "#000000",
        "grid.linestyle": "--",
        "legend.frameon": True,
        "legend.framealpha": 0.7,
        "path.simplify": True,
    }
)


# -----------------------------------------------------------------------------
# Generic helpers
# -----------------------------------------------------------------------------


def ensure_directories() -> None:
    """Create the expected data, image, and cache directories."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_DIR.mkdir(parents=True, exist_ok=True)



def cache_is_fresh(path: Path, max_age_days: int = CACHE_MAX_AGE_DAYS) -> bool:
    """Return True if a cache file exists and is younger than max_age_days."""
    if not path.exists():
        return False
    age_seconds = dt.datetime.now().timestamp() - path.stat().st_mtime
    return age_seconds < max_age_days * 24 * 60 * 60



def request_json(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    timeout: int = HTTP_TIMEOUT,
) -> Any:
    """Request JSON data and raise a useful HTTP error if the request fails."""
    response = requests.get(url, params=params, timeout=timeout)
    response.raise_for_status()
    return response.json()



def download_file(
    url: str,
    cache_path: Path | str,
    *,
    force: bool = False,
    max_age_days: int | None = CACHE_MAX_AGE_DAYS,
    timeout: int = HTTP_TIMEOUT,
) -> Path:
    """Download a file into the cache unless a fresh cached copy already exists."""
    path = Path(cache_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if not force and path.exists():
        if max_age_days is None or cache_is_fresh(path, max_age_days):
            return path

    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    path.write_bytes(response.content)
    return path



def read_cached_csv(
    url: str,
    cache_path: Path | str,
    *,
    force: bool = False,
    max_age_days: int | None = CACHE_MAX_AGE_DAYS,
    **read_csv_kwargs: Any,
) -> pd.DataFrame:
    """Download a CSV if needed and return it as a DataFrame."""
    path = download_file(url, cache_path, force=force, max_age_days=max_age_days)
    return pd.read_csv(path, **read_csv_kwargs)



def parse_period(value: str, frequency: str) -> pd.Timestamp:
    """Parse IMF period strings, including quarterly values such as '1997-Q3'."""
    if frequency == "Q":
        year, quarter = value.split("-Q")
        return pd.to_datetime(year) + QuarterEnd(int(quarter))
    if frequency == "A":
        return pd.to_datetime(value, format="%Y")
    return pd.to_datetime(value)



def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy with lower-case, underscore-separated column names."""
    out = df.copy()
    out.columns = (
        out.columns.astype(str)
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )
    return out



def find_column(columns: Iterable[str], candidates: Sequence[str]) -> str:
    """First column whose name equals or contains one of the candidate substrings."""
    cols = list(columns)
    for candidate in candidates:
        needle = candidate.lower()
        for col in cols:
            haystack = str(col).lower()
            if needle == haystack or needle in haystack:
                return col

    raise ValueError(
        f"Could not find a column matching {list(candidates)}. Available columns: {cols}"
    )



def save_figure(fig: plt.Figure, file_path: Path | str) -> None:
    """Save a matplotlib figure as SVG and close it to avoid memory leaks."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, format="svg")
    plt.close(fig)


# -----------------------------------------------------------------------------
# Data loaders
# -----------------------------------------------------------------------------

# IMF STA SDMX 2.1 CSV: https://data.imf.org/en/Resource-Pages/IMF-API
# Series keys match each dataflow's CSV columns (…, TIME_PERIOD, OBS_VALUE, SCALE, …).
IMF_SDMX_21_DATA = "https://api.imf.org/external/sdmx/2.1/data"


def imf_sta_series(
    dataflow: str,
    key: str,
    start_period: str | int,
    end_period: str | int,
    *,
    freq: str,
    force: bool = False,
) -> pd.Series:
    """One IMF STA series as ``pd.Series`` indexed by parsed ``TIME_PERIOD``."""
    if freq not in {"A", "Q"}:
        raise ValueError("freq must be 'A' or 'Q'.")

    url = f"{IMF_SDMX_21_DATA}/{dataflow}/{key}"
    params = {"startPeriod": str(start_period), "endPeriod": str(end_period)}
    safe_key = key.replace("/", "_")
    cache_path = CACHE_DIR / f"imf_sta_{dataflow}_{safe_key}_{start_period}_{end_period}.csv"

    if cache_path.exists() and not force and cache_is_fresh(cache_path):
        text = cache_path.read_text(encoding="utf-8")
    else:
        r = requests.get(
            url,
            params=params,
            headers={"Accept": "text/csv", "User-Agent": "mwi-generate_figures/1.0"},
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        text = r.text
        cache_path.write_text(text, encoding="utf-8")

    df = pd.read_csv(io.StringIO(text))
    if "TIME_PERIOD" not in df.columns or "OBS_VALUE" not in df.columns:
        raise ValueError(f"Unexpected IMF CSV for {dataflow}/{key}: {list(df.columns)}")

    w = df.dropna(subset=["TIME_PERIOD", "OBS_VALUE"])
    if w.empty:
        raise ValueError(f"No IMF observations: {dataflow}/{key}")

    obs = pd.to_numeric(w["OBS_VALUE"], errors="coerce")
    if "SCALE" in w.columns:
        sc = pd.to_numeric(w["SCALE"], errors="coerce").fillna(0).astype("int64")
    else:
        sc = 0
    values = obs * np.power(10.0, -sc)
    index = w["TIME_PERIOD"].astype(str).map(lambda s: parse_period(s, freq))
    return pd.Series(values.to_numpy(), index=index, dtype="float64").sort_index()


def imf_sta_frame(
    series: dict[str, tuple[str, str]],
    start_period: str | int,
    end_period: str | int,
    *,
    freq: str,
    force: bool = False,
) -> pd.DataFrame:
    """Align several STA series into one ``DataFrame`` (column names = ``series`` keys)."""
    parts = {
        name: imf_sta_series(flow, key, start_period, end_period, freq=freq, force=force)
        for name, (flow, key) in series.items()
    }
    return pd.concat(parts, axis=1).sort_index()



def get_wdi_data(
    indicators: Sequence[str] | str,
    country_codes: Sequence[str] | str,
    *,
    start_year: int = 1980,
    end_year: int = 2025,
    source: int | None = 2,
    force: bool = False,
) -> pd.DataFrame:
    """World Bank WDI: columns are ``(indicator, iso3)`` MultiIndex, index is year."""
    inds = [indicators] if isinstance(indicators, str) else list(indicators)
    countries = [country_codes] if isinstance(country_codes, str) else list(country_codes)
    countries_part = ";".join(countries)

    rows: list[dict[str, Any]] = []
    for indicator in inds:
        url = f"https://api.worldbank.org/v2/country/{countries_part}/indicator/{indicator}"
        params: dict[str, Any] = {
            "format": "json",
            "date": f"{start_year}:{end_year}",
            "per_page": 20000,
        }
        if source is not None:
            params["source"] = source

        source_part = "all" if source is None else str(source)
        cache_path = CACHE_DIR / (
            f"wdi_{indicator}_{countries_part}_{start_year}_{end_year}_{source_part}.json".replace(
                ";", "-"
            )
        )

        if cache_path.exists() and not force and cache_is_fresh(cache_path):
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            payload = request_json(url, params=params)
            cache_path.write_text(json.dumps(payload), encoding="utf-8")

        if not isinstance(payload, list) or len(payload) < 2 or payload[1] is None:
            raise ValueError(f"Unexpected or empty World Bank response for {indicator}: {payload!r}")

        for item in payload[1]:
            country = item.get("countryiso3code") or (item.get("country") or {}).get("id")
            rows.append(
                {
                    "date": pd.to_datetime(item["date"]),
                    "indicator": indicator,
                    "country": country,
                    "value": item.get("value"),
                }
            )

    out = pd.DataFrame(rows)
    if out.empty:
        raise ValueError("World Bank API returned no rows.")
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.pivot_table(index="date", columns=["indicator", "country"], values="value").sort_index()



def get_fred_series(
    series_ids: Sequence[str] | str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
    force: bool = False,
) -> pd.DataFrame:
    """FRED CSV graph export: one column per series id."""
    ids = [series_ids] if isinstance(series_ids, str) else list(series_ids)
    parts: list[pd.DataFrame] = []
    for sid in ids:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"
        cache_path = CACHE_DIR / f"fred_{sid}.csv"
        df = read_cached_csv(url, cache_path, force=force)
        idx = pd.to_datetime(df["observation_date"])
        series = pd.to_numeric(df[sid], errors="coerce")
        parts.append(pd.DataFrame({sid: series.values}, index=idx))
    out = pd.concat(parts, axis=1).sort_index()
    if start_date is not None:
        out = out[out.index >= pd.to_datetime(start_date)]
    if end_date is not None:
        out = out[out.index <= pd.to_datetime(end_date)]
    return out


# -----------------------------------------------------------------------------
# PortWatch / HDX chokepoint data
# -----------------------------------------------------------------------------

PORTWATCH_PACKAGE_ID = "daily-chokepoint-transit-calls-and-shipment-volume-estimates"
HDX_PACKAGE_URL = "https://data.humdata.org/api/3/action/package_show"

CHOKEPOINTS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    # key -> (German label, canonical port id, lowercase substring aliases)
    "suez": ("Suezkanal", "chokepoint1", ("suez",)),
    "panama": ("Panama-Kanal", "chokepoint2", ("panama",)),
    "hormuz": ("Straße von Hormus", "chokepoint6", ("hormuz", "strait of hormuz")),
    "cape": ("Kap der Guten Hoffnung", "chokepoint7", ("cape of good hope", "cape")),
}


def get_hdx_package(package_id: str, *, force: bool = False) -> dict[str, Any]:
    """Fetch HDX/CKAN package metadata with a small JSON cache."""
    cache_path = CACHE_DIR / f"hdx_package_{package_id}.json"

    if cache_path.exists() and not force and cache_is_fresh(cache_path):
        return json.loads(cache_path.read_text(encoding="utf-8"))

    payload = request_json(HDX_PACKAGE_URL, params={"id": package_id})
    if not payload.get("success"):
        raise RuntimeError(f"HDX package lookup failed: {payload}")

    result = payload["result"]
    cache_path.write_text(json.dumps(result), encoding="utf-8")
    return result



def find_hdx_csv_resource_url(package_id: str, *, force: bool = False) -> str:
    """Return the preferred CSV resource URL for an HDX package."""
    package = get_hdx_package(package_id, force=force)
    resources = package.get("resources", [])
    csv_resources = [
        res
        for res in resources
        if (res.get("format") or "").lower() == "csv" and res.get("url")
    ]

    if not csv_resources:
        available = [
            {"name": res.get("name"), "format": res.get("format"), "url": res.get("url")}
            for res in resources
        ]
        raise RuntimeError(f"No CSV resource found in HDX package. Available: {available}")

    preferred_tokens = [
        "daily chokepoint",
        "transit calls",
        "shipment volume",
        "trade volume",
    ]
    for token in preferred_tokens:
        for resource in csv_resources:
            if token in (resource.get("name") or "").lower():
                return resource["url"]

    return csv_resources[0]["url"]



def get_portwatch_chokepoint_data(*, force: bool = False) -> pd.DataFrame:
    """Load the daily PortWatch chokepoint CSV from HDX."""
    csv_url = find_hdx_csv_resource_url(PORTWATCH_PACKAGE_ID, force=force)
    cache_path = CACHE_DIR / "portwatch_daily_chokepoints.csv"
    raw = read_cached_csv(csv_url, cache_path, force=force, max_age_days=CACHE_MAX_AGE_DAYS)
    return normalize_columns(raw)



def prepare_chokepoint_trade_volume(
    selected_chokepoints: Sequence[str],
    *,
    start_date: str = "2019-01-01",
    force: bool = False,
) -> pd.DataFrame:
    """Return daily estimated trade volume for selected chokepoints."""
    df = get_portwatch_chokepoint_data(force=force)

    date_col = find_column(df.columns, ["ymd", "date", "day", "time"])
    port_col = find_column(
        df.columns,
        ["portid", "port_id", "chokepoint", "portname", "port_name", "name"],
    )
    volume_col = find_column(
        df.columns,
        [
            "v_total",
            "volume_total",
            "trade_volume",
            "shipment_volume",
            "transit_volume",
            "estimated_volume",
            "capacity_total",
            "capacity",
            "deadweight",
            "dwt",
            "metric_tons",
            "tonnes",
            "tons",
            "volume",
        ],
    )

    if pd.api.types.is_numeric_dtype(df[date_col]):
        df["date"] = pd.to_datetime(df[date_col], unit="ms", errors="coerce", utc=True)
    else:
        df["date"] = pd.to_datetime(df[date_col], errors="coerce", utc=True)
    df["date"] = df["date"].dt.tz_convert(None)
    df[volume_col] = pd.to_numeric(df[volume_col], errors="coerce")

    port_values = df[port_col].astype(str).str.lower()
    series: list[pd.DataFrame] = []

    for key in selected_chokepoints:
        if key not in CHOKEPOINTS:
            raise ValueError(f"Unknown chokepoint {key!r}. Use one of: {list(CHOKEPOINTS)}")

        label, cp_id, aliases = CHOKEPOINTS[key]
        mask = port_values.eq(cp_id.lower())
        for alias in aliases:
            mask = mask | port_values.str.contains(alias.lower(), regex=False, na=False)

        temp = df.loc[mask, ["date", volume_col]].copy()
        if temp.empty:
            unique_ports = df[port_col].dropna().astype(str).unique()[:50]
            raise ValueError(
                f"No rows found for {label}. Detected port column: {port_col}. "
                f"Sample values: {unique_ports}"
            )

        temp = (
            temp.dropna()
            .groupby("date", as_index=True)[volume_col]
            .sum()
            .sort_index()
            .to_frame(label)
        )
        series.append(temp)

    data = pd.concat(series, axis=1).sort_index()
    data = data[data.index >= pd.to_datetime(start_date)]

    if data.empty:
        raise ValueError(f"No chokepoint observations available after {start_date}.")

    return data


# -----------------------------------------------------------------------------
# Plotting
# -----------------------------------------------------------------------------


def create_plot(
    data: pd.DataFrame,
    xlabel: str,
    ylabel: str,
    data_source: str | None = None,
    *,
    secondary_y: Sequence[str] | None = None,
    secondary_y_label: str | None = None,
    plot_type: str = "line",
    bar_width: float = 0.15,
    ymin: float | None = None,
    y2min: float | None = None,
    legend: bool = False,
) -> plt.Figure:
    """Create a lecture-style line or bar plot with optional secondary y-axis."""
    fig, ax = plt.subplots(figsize=(12, 6))

    secondary_y = list(secondary_y or [])
    primary_cols = [col for col in data.columns if col not in secondary_y]

    if plot_type not in {"line", "bar"}:
        raise ValueError("plot_type must be either 'line' or 'bar'.")

    x_values = data.index
    if plot_type == "bar":
        x_values = np.arange(len(data))

    for i, col in enumerate(primary_cols):
        color = PRIMARY_COLORS[i % len(PRIMARY_COLORS)]
        if plot_type == "line":
            ax.plot(data.index, data[col], label=col, color=color)
        else:
            offset = (i - len(primary_cols) / 2) * bar_width + bar_width / 2
            ax.bar(x_values + offset, data[col], label=col, color=color, width=bar_width)

    ax.set_xlabel(xlabel, fontsize=12, color="lightgrey")
    ax.set_ylabel(ylabel, fontsize=12, color="lightgrey")
    ax.set_ylim(bottom=ymin)
    ax.grid(True, which="both", color="gray", linestyle="--", linewidth=0.5)
    ax.tick_params(colors="white", which="both")

    if plot_type == "bar" and isinstance(data.index, pd.DatetimeIndex):
        ax.set_xticks(x_values)
        ax.set_xticklabels(data.index.strftime("%Y-%m-%d"), rotation=45, ha="right")

    ax2 = None
    if secondary_y:
        ax2 = ax.twinx()
        for i, col in enumerate(secondary_y):
            color = SECONDARY_COLORS[i % len(SECONDARY_COLORS)]
            if plot_type == "line":
                ax2.plot(data.index, data[col], label=col, color=color)
            else:
                offset = (i - len(secondary_y) / 2) * bar_width + bar_width / 2
                ax2.bar(x_values + offset, data[col], label=col, color=color, width=bar_width, alpha=0.7)
        ax2.set_ylim(bottom=y2min)
        ax2.set_ylabel(secondary_y_label or secondary_y[0], fontsize=12, color="lightgrey")
        ax2.tick_params(colors="white", which="both")

    lines, labels = ax.get_legend_handles_labels()
    if ax2 is not None:
        lines2, labels2 = ax2.get_legend_handles_labels()
        lines += lines2
        labels += labels2

    if legend or secondary_y:
        ax.legend(lines, labels)

    if data_source:
        ax.text(
            1,
            -0.15,
            "Quelle: " + data_source,
            transform=ax.transAxes,
            fontsize=8,
            va="bottom",
            ha="right",
            color="darkgrey",
        )

    fig.tight_layout()
    return fig



def apply_rolling_and_index(
    data: pd.DataFrame,
    *,
    rolling: int | None = None,
    index_baseline: tuple[str, str] | None = None,
) -> tuple[pd.DataFrame, str]:
    """Smooth and optionally index data to a baseline period."""
    plot_data = data.copy()

    if rolling:
        plot_data = plot_data.rolling(
            rolling,
            min_periods=max(3, rolling // 4),
        ).mean()

    if index_baseline is not None:
        baseline_start, baseline_end = index_baseline
        baseline_period = plot_data.loc[
            (plot_data.index >= pd.to_datetime(baseline_start))
            & (plot_data.index <= pd.to_datetime(baseline_end))
        ]
        baseline = baseline_period.mean()

        if baseline.isna().any() or (baseline == 0).any():
            raise ValueError(f"Invalid index baseline: {baseline.to_dict()}")

        plot_data = plot_data.divide(baseline).multiply(100)
        ylabel = f"Index, Durchschnitt {baseline_start[:4]}–{baseline_end[:4]} = 100"
    else:
        if plot_data.max().max() > 1_000_000:
            plot_data = plot_data / 1_000_000
            ylabel = "Mio. metrische Tonnen"
        else:
            ylabel = "Metrische Tonnen"

    if rolling:
        plot_data = plot_data.rename(
            columns={col: f"{col}, {rolling}-Tage-Durchschnitt" for col in plot_data.columns}
        )
        if index_baseline is None:
            ylabel = f"{ylabel}, {rolling}-Tage-Durchschnitt"

    return plot_data, ylabel


# -----------------------------------------------------------------------------
# Figure-specific functions
# -----------------------------------------------------------------------------

# World Bank income-group aggregates use non-ISO3 ids (XM, XN, XT, XD); see country/LIC etc.
INCOME_GROUP_CODES = {
    "XM": "Länder mit niedrigem Einkommen",
    "XN": "Länder mit unterem Mittel einkommen",
    "XT": "Länder mit oberem Mittel einkommen",
    "XD": "Länder mit hohem Einkommen",
    "WLD": "Welt",
}

ASIA_COUNTRY_CODES = {
    "KOR": "Südkorea",
    "IND": "Indien",
    "CHN": "China",
}

TRADE_OPENNESS_INDICATOR = "NE.TRD.GNFS.ZS"
POVERTY_HEADCOUNT_INDICATOR = "SI.POV.DDAY"
GDP_PER_CAPITA_REAL_INDICATOR = "NY.GDP.PCAP.KD"


def index_to_year(data: pd.DataFrame, year: int) -> pd.DataFrame:
    """Index all columns to 100 in the given calendar year."""
    baseline_date = pd.to_datetime(str(year))
    if baseline_date not in data.index:
        raise ValueError(f"Baseline year {year} not in data index.")
    baseline = data.loc[baseline_date]
    invalid = baseline.isna() | (baseline == 0)
    if invalid.any():
        raise ValueError(f"Invalid baseline for {year}: {baseline[invalid].to_dict()}")
    return data.divide(baseline).multiply(100)


def wdi_labeled_frame(
    indicator: str,
    code_to_label: Mapping[str, str],
    *,
    start_year: int,
    end_year: int = 2025,
    force: bool = False,
) -> pd.DataFrame:
    """Fetch WDI series and return a DataFrame with human-readable column names."""
    df = get_wdi_data(
        [indicator],
        list(code_to_label.keys()),
        start_year=start_year,
        end_year=end_year,
        force=force,
    )
    data = pd.DataFrame(index=df.index.sort_values())
    for code, label in code_to_label.items():
        col = (indicator, code)
        if col in df.columns:
            data[label] = df[col]
    if data.empty:
        raise ValueError(f"No WDI data for {indicator} and codes {list(code_to_label)}.")
    return data


def trade_openness_by_income_group(file_path: Path | str) -> None:
    """Trade (% of GDP) by World Bank income group since 1980."""
    data = wdi_labeled_frame(
        TRADE_OPENNESS_INDICATOR,
        INCOME_GROUP_CODES,
        start_year=1980,
    )
    fig = create_plot(
        data,
        "Jahr",
        "% des BIP",
        "World Bank World Development Indicators; OECD National Accounts",
        legend=True,
    )
    save_figure(fig, file_path)


def poverty_by_income_group(file_path: Path | str) -> None:
    """Extreme poverty headcount ($2.15/day, 2017 PPP) by World Bank income group."""
    data = wdi_labeled_frame(
        POVERTY_HEADCOUNT_INDICATOR,
        INCOME_GROUP_CODES,
        start_year=1980,
    )
    fig = create_plot(
        data,
        "Jahr",
        "Anteil in extremer Armut (%)",
        "World Bank Poverty and Inequality Platform (2,15 USD/Tag, KKP 2017)",
        legend=True,
    )
    save_figure(fig, file_path)


def asia_trade_openness(file_path: Path | str) -> None:
    """Trade (% of GDP) for South Korea, India, and China since 1960."""
    data = wdi_labeled_frame(
        TRADE_OPENNESS_INDICATOR,
        ASIA_COUNTRY_CODES,
        start_year=1960,
    )
    fig = create_plot(
        data,
        "Jahr",
        "% des BIP",
        "World Bank World Development Indicators; OECD National Accounts",
        legend=True,
    )
    save_figure(fig, file_path)


def asia_gdp_per_capita(file_path: Path | str) -> None:
    """Real GDP per capita indexed to 1960 = 100 for South Korea, India, and China."""
    levels = wdi_labeled_frame(
        GDP_PER_CAPITA_REAL_INDICATOR,
        ASIA_COUNTRY_CODES,
        start_year=1960,
    )
    data = index_to_year(levels, 1960)
    fig = create_plot(
        data,
        "Jahr",
        "BIP pro Kopf (1960 = 100)",
        "World Bank national accounts data",
        legend=True,
    )
    save_figure(fig, file_path)


def india_catch_up(file_path: Path | str) -> None:
    """Plot Indian GDP per capita as a percentage of US GDP per capita."""
    indicator = "NY.GDP.PCAP.CD"
    df = get_wdi_data([indicator], ["IN", "US"])
    data = pd.DataFrame({"Indien": 100 * df[(indicator, "IND")] / df[(indicator, "USA")]})
    fig = create_plot(
        data,
        "Jahr",
        "% des Pro-Kopf-Einkommens der USA",
        "World Bank national accounts data",
    )
    save_figure(fig, file_path)



def india_tech(file_path: Path | str) -> None:
    """Plot medium- and high-tech exports as a share of manufactured exports in India."""
    indicator = "TX.MNF.TECH.ZS.UN"
    df = get_wdi_data([indicator], ["IN"])
    data = pd.DataFrame({"Indien": df[(indicator, "IND")]})
    fig = create_plot(
        data,
        "Jahr",
        "% der Industrieexporte",
        "UNIDO Competitive Industrial Performance database via World Bank",
    )
    save_figure(fig, file_path)



def csv_plot(
    csv_path: Path | str,
    output_path: Path | str,
    xlabel: str,
    ylabel: str,
    source: str,
    *,
    y2: Sequence[str] | None = None,
    y2label: str | None = None,
) -> None:
    """Create a simple line plot from a local CSV file with a date index."""
    df = pd.read_csv(csv_path, index_col=0)
    df.index = pd.to_datetime(df.index)
    fig = create_plot(df, xlabel, ylabel, source, secondary_y=y2, secondary_y_label=y2label)
    save_figure(fig, output_path)



def thailand_ca_balance(file_path: Path | str) -> None:
    """Plot Thailand's current-account balance around the Asian financial crisis."""
    data = imf_sta_frame(
        {"Leistungsbilanzsaldo": ("BOP", "THA.NETCD_T.CAB.USD.Q")},
        1990,
        2002,
        freq="Q",
    )
    fig = create_plot(
        data,
        "Jahr",
        "Mio. USD",
        "International Monetary Fund (IMF), STA: Balance of Payments (BOP)",
    )
    save_figure(fig, file_path)


def thailand_forex(file_path: Path | str) -> None:
    """Plot Thailand's foreign-exchange reserves and THB/USD exchange rate."""
    data = imf_sta_frame(
        {
            "Währungsreserven der Zentralbank": ("IL", "THA.TRGMV_REVS.USD.Q"),
            "THB/USD (rechts)": ("ER", "THA.XDC_USD.PA_RT.Q"),
        },
        1990,
        2002,
        freq="Q",
    )
    fig = create_plot(
        data,
        "Jahr",
        "Mio. USD",
        "International Monetary Fund (IMF), STA: International Liquidity (IL) and Exchange Rates (ER)",
        secondary_y=["THB/USD (rechts)"],
        secondary_y_label="THB/USD",
    )
    save_figure(fig, file_path)


def thailand_ext_debt(file_path: Path | str) -> None:
    """Plot Thailand's foreign liabilities in USD and converted to Thai baht."""
    df = imf_sta_frame(
        {
            "liab_direct_investment": ("IIP", "THA.L_P.D.USD.A"),
            "liab_portfolio": ("IIP", "THA.L_P.P_F3_MV.USD.A"),
            "thb_usd": ("ER", "THA.XDC_USD.PA_RT.A"),
        },
        1990,
        1999,
        freq="A",
    )
    data = pd.DataFrame(index=df.index)
    data["Auslandsverschuldung in USD (links)"] = df["liab_direct_investment"] + df["liab_portfolio"]
    data["Auslandsverschuldung in THB (rechts)"] = (
        data["Auslandsverschuldung in USD (links)"] * df["thb_usd"]
    )

    fig = create_plot(
        data,
        "Jahr",
        "Mio. USD",
        "International Monetary Fund (IMF), STA: International Investment Position (IIP) and Exchange Rates (ER)",
        secondary_y=["Auslandsverschuldung in THB (rechts)"],
        secondary_y_label="Mio. THB",
        ymin=0,
        y2min=0,
    )
    save_figure(fig, file_path)



def thailand_gdp_per_capita(file_path: Path | str) -> None:
    """Plot Thailand's GDP per capita around the Asian financial crisis."""
    indicator = "NY.GDP.PCAP.CD"
    df = get_wdi_data([indicator], ["TH"], start_year=1990, end_year=2002)
    data = pd.DataFrame({"Thailand": df[(indicator, "THA")]})
    fig = create_plot(
        data,
        "Jahr",
        "USD",
        "World Bank national accounts data, and OECD National Accounts data files",
    )
    save_figure(fig, file_path)



def world_co2(file_path: Path | str) -> None:
    """Plot global per-capita CO2 emissions and CO2 intensity of GDP."""
    indicators = {
        "EN.GHG.CO2.PC.CE.AR5": "CO₂-Emissionen pro Kopf",
        "EN.GHG.CO2.RT.GDP.PP.KD": "CO₂-Intensität des BIP",
    }
    df = get_wdi_data(list(indicators), ["WLD"], start_year=1990, end_year=2025, source=None)
    data = pd.DataFrame(
        {
            indicators["EN.GHG.CO2.PC.CE.AR5"]: df[("EN.GHG.CO2.PC.CE.AR5", "WLD")],
            indicators["EN.GHG.CO2.RT.GDP.PP.KD"]: df[("EN.GHG.CO2.RT.GDP.PP.KD", "WLD")],
        }
    )
    fig = create_plot(
        data,
        "Jahr",
        "t CO₂e pro Kopf",
        "World Bank World Development Indicators; EDGAR/JRC; IEA",
        secondary_y=["CO₂-Intensität des BIP"],
        secondary_y_label="kg CO₂e pro USD BIP in KKP",
        ymin=3.8,
        y2min=0.2,
        legend=True,
    )
    save_figure(fig, file_path)



def raw_materials(file_path: Path | str) -> None:
    """Plot selected commodity-price indices normalized to 1990 = 100."""
    df = pd.read_csv(DATA_DIR / "raw_materials.csv", index_col=0)
    df.index = pd.to_datetime(df.index)
    first_row = df.iloc[0]
    data = pd.DataFrame(
        {
            "Kupfer": df["copper"] / first_row["copper"] * 100,
            "Steinkohle": df["coal"] / first_row["coal"] * 100,
            "Erdöl": df["oil"] / first_row["oil"] * 100,
        },
        index=df.index,
    )
    fig = create_plot(
        data,
        "Jahr",
        "Index (1990: 100)",
        "Federal Reserve Bank of St. Louis",
        legend=True,
    )
    save_figure(fig, file_path)



def oil_prices_iran_2026(file_path: Path | str) -> None:
    """Plot Brent and WTI oil spot prices during the 2026 Hormuz/Iran crisis."""
    series = {"DCOILBRENTEU": "Brent", "DCOILWTICO": "WTI"}
    df = get_fred_series(
        list(series),
        start_date="2025-07-01",
        end_date=dt.date.today().isoformat(),
    ).rename(columns=series)

    fig = create_plot(
        df,
        xlabel="Datum",
        ylabel="USD pro Barrel",
        data_source="U.S. Energy Information Administration via FRED",
        ymin=0,
        legend=True,
    )

    ax = fig.axes[0]
    event_start = pd.to_datetime("2026-02-27")
    event_label_date = pd.to_datetime("2026-03-10")
    ax.axvline(event_start, color="#d79921", linestyle="--", linewidth=1.5)
    ax.text(
        event_label_date,
        ax.get_ylim()[1] * 0.1,
        "Beginn der akuten\nHormus-/Iran-Krise",
        color="#e6e6e6",
        fontsize=10,
        va="top",
    )
    save_figure(fig, file_path)



def chokepoint_trade_volume(
    file_path: Path | str,
    *,
    selected_chokepoints: Sequence[str] = ("panama", "suez", "hormuz"),
    start_date: str = "2019-01-01",
    rolling: int | None = 28,
    index_baseline: tuple[str, str] | None = ("2019-01-01", "2023-12-31"),
    force: bool = False,
) -> None:
    """Plot estimated daily transit trade volume for selected maritime chokepoints."""
    data = prepare_chokepoint_trade_volume(
        selected_chokepoints,
        start_date=start_date,
        force=force,
    )
    plot_data, ylabel = apply_rolling_and_index(
        data,
        rolling=rolling,
        index_baseline=index_baseline,
    )
    fig = create_plot(
        plot_data,
        xlabel="Datum",
        ylabel=ylabel,
        data_source="IMF PortWatch / HDX",
        ymin=0,
        legend=True,
    )
    save_figure(fig, file_path)


def build_all_figures() -> None:
    """Generate all lecture figures managed by this script."""
    ensure_directories()

    csv_plot(
        DATA_DIR / "india_fdi_gdp.csv",
        IMAGE_DIR / "india_fdi_gdp.svg",
        "Jahr",
        "% des BIP",
        "United Nations Conference on Trade and Development (UNCTAD) statistical data",
    )
    csv_plot(
        DATA_DIR / "world_co2.csv",
        IMAGE_DIR / "world_co2_old.svg",
        "Jahr",
        "kt",
        "Climate Watch",
    )
    raw_materials(IMAGE_DIR / "raw_materials.svg")

    trade_openness_by_income_group(IMAGE_DIR / "trade-as-share-of-gdp.svg")
    poverty_by_income_group(IMAGE_DIR / "poverty-by-income-group.svg")
    asia_trade_openness(IMAGE_DIR / "trade-as-share-of-gdp-asia.svg")
    asia_gdp_per_capita(IMAGE_DIR / "gdp-per-capita-asia.svg")

    india_catch_up(IMAGE_DIR / "india_catch_up.svg")
    india_tech(IMAGE_DIR / "india_tech_exports.svg")
    thailand_ca_balance(IMAGE_DIR / "thailand_ca_balance.svg")
    thailand_forex(IMAGE_DIR / "thailand_forex.svg")
    thailand_ext_debt(IMAGE_DIR / "thailand_ext_debt.svg")
    thailand_gdp_per_capita(IMAGE_DIR / "thailand_gdp_per_capita.svg")
    world_co2(IMAGE_DIR / "world_co2.svg")
    oil_prices_iran_2026(IMAGE_DIR / "oil_prices_iran_2026.svg")

    chokepoint_trade_volume(
        IMAGE_DIR / "panama_suez_trade_volume.svg",
        selected_chokepoints=("panama", "suez"),
        start_date="2019-01-01",
        rolling=28,
        index_baseline=("2019-01-01", "2023-12-31"),
    )
    chokepoint_trade_volume(
        IMAGE_DIR / "cape_trade_volume.svg",
        selected_chokepoints=("cape",),
        start_date="2019-01-01",
        rolling=28,
        index_baseline=("2019-01-01", "2023-12-31"),
    )
    chokepoint_trade_volume(
        IMAGE_DIR / "hormuz_trade_volume_2026.svg",
        selected_chokepoints=("hormuz",),
        start_date="2025-01-01",
        rolling=7,
        index_baseline=("2025-01-01", "2025-12-31"),
    )


if __name__ == "__main__":
    build_all_figures()
