"""Generate data-driven SVG figures for the international economics lecture.

This script intentionally stays lightweight: it is meant to be run manually while
preparing lecture slides, not deployed as a package. Still, the code is organized
around reusable data loaders, simple caching, and small plot-specific functions.

The script writes SVG files into the images/ directory. Network data are cached
under data/cache/ so repeated runs are fast and less dependent on external APIs.
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import squarify
from pandas.plotting import register_matplotlib_converters
from pandas.tseries.offsets import QuarterEnd

register_matplotlib_converters()

# -----------------------------------------------------------------------------
# Paths and global configuration
# -----------------------------------------------------------------------------

DATA_DIR = Path("data")
IMAGE_DIR = Path("images")
SCRIPT_IMAGE_DIR = Path("lecture/build/figure-svg")
CACHE_DIR = DATA_DIR / "cache"

HTTP_TIMEOUT = 60
CACHE_MAX_AGE_DAYS = 7

_OFFLINE = False
_FORCE_REFRESH = False


class OfflineCacheError(RuntimeError):
    """Raised when a network fetch is required but offline mode is enabled."""


def offline_mode() -> bool:
    return _OFFLINE


def force_refresh() -> bool:
    return _FORCE_REFRESH


def configure_runtime(*, offline: bool, force: bool) -> None:
    global _OFFLINE, _FORCE_REFRESH
    _OFFLINE = offline
    _FORCE_REFRESH = force


def _effective_force(force: bool) -> bool:
    return force or _FORCE_REFRESH


def _cache_hit(path: Path, *, force: bool, max_age_days: int | None) -> bool:
    if not path.exists():
        return False
    if _OFFLINE:
        return True
    if _effective_force(force):
        return False
    if max_age_days is None:
        return True
    return cache_is_fresh(path, max_age_days)


def _require_cache(path: Path, *, context: str) -> None:
    if _OFFLINE and not path.exists():
        raise OfflineCacheError(
            f"Offline mode: missing cache for {context} (expected {path})"
        )

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

@dataclass(frozen=True)
class PlotTheme:
    """Colors for slides (dark background) or script PDF (white background)."""

    name: str
    rcparams: dict[str, Any]
    label_color: str
    tick_color: str
    grid_color: str
    annotation_color: str
    source_color: str


_COMMON_RCPARAMS: dict[str, Any] = {
    "figure.figsize": (10, 6),
    "axes.labelsize": "large",
    "axes.titlesize": "x-large",
    "font.family": "sans-serif",
    "grid.linestyle": "--",
    "legend.frameon": True,
    "legend.framealpha": 0.7,
    "path.simplify": True,
}

DARK_THEME = PlotTheme(
    name="dark",
    rcparams={
        **_COMMON_RCPARAMS,
        "text.color": "#e6e6e6",
        "figure.facecolor": "#00000000",
        "axes.facecolor": "#00000000",
        "axes.edgecolor": "#333333",
        "axes.labelcolor": "#e6e6e6",
        "xtick.color": "#e6e6e6",
        "xtick.labelsize": "medium",
        "ytick.color": "#e6e6e6",
        "ytick.labelsize": "medium",
        "grid.color": "#000000",
    },
    label_color="lightgrey",
    tick_color="white",
    grid_color="gray",
    annotation_color="#e6e6e6",
    source_color="darkgrey",
)

LIGHT_THEME = PlotTheme(
    name="light",
    rcparams={
        **_COMMON_RCPARAMS,
        "text.color": "#333333",
        "figure.facecolor": "#ffffff",
        "axes.facecolor": "#ffffff",
        "axes.edgecolor": "#666666",
        "axes.labelcolor": "#333333",
        "xtick.color": "#333333",
        "xtick.labelsize": "medium",
        "ytick.color": "#333333",
        "ytick.labelsize": "medium",
        "grid.color": "#cccccc",
    },
    label_color="#333333",
    tick_color="#333333",
    grid_color="#cccccc",
    annotation_color="#333333",
    source_color="#666666",
)

_active_theme: PlotTheme = DARK_THEME


def use_theme(theme: PlotTheme) -> None:
    """Switch matplotlib styling (slides vs. script PDF)."""
    global _active_theme
    _active_theme = theme
    plt.rcParams.update(theme.rcparams)


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

    if _cache_hit(path, force=force, max_age_days=max_age_days):
        return path

    _require_cache(path, context=url)

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

    if _cache_hit(cache_path, force=force, max_age_days=CACHE_MAX_AGE_DAYS):
        text = cache_path.read_text(encoding="utf-8")
    else:
        _require_cache(cache_path, context=f"IMF STA {dataflow}/{key}")
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


# Annual net current account (goods, services, primary & secondary income), USD.
# Bulk key: all countries in one SDMX request (COUNTRY dimension left open).
IMF_CA_BULK_KEY = ".NETCD_T.CAB.USD.A"

# Regional / composite codes in older WDI-based charts (not ISO economies).
CA_BALANCE_EXCLUDE_NAMES = (
    "Euro area",
    "Arab World",
    "East Asia & Pacific",
    "European Union",
    "Latin America & Caribbean",
    "Middle East & North Africa",
    "North America",
    "South Asia",
    "Sub-Saharan Africa",
)

# IMF codes missing from the World Bank country list.
IMF_CA_COUNTRY_NAME_OVERRIDES: dict[str, str] = {
    "AIA": "Anguilla",
    "CWX": "Curaçao",
    "KOS": "Kosovo",
    "MSR": "Montserrat",
    "WBG": "West Bank and Gaza",
}


def _imf_obs_values_usd(df: pd.DataFrame) -> pd.Series:
    """Convert IMF STA ``OBS_VALUE`` + ``SCALE`` to levels in US dollars."""
    obs = pd.to_numeric(df["OBS_VALUE"], errors="coerce")
    if "SCALE" in df.columns:
        sc = pd.to_numeric(df["SCALE"], errors="coerce").fillna(0).astype("int64")
    else:
        sc = 0
    return obs * np.power(10.0, -sc)


def imf_bop_current_accounts(
    year: int,
    *,
    force: bool = False,
) -> pd.DataFrame:
    """Current-account balances for all reporting economies in one calendar year.

    Returns a DataFrame with columns ``iso3``, ``country``, and ``balance_usd``.
    """
    url = f"{IMF_SDMX_21_DATA}/BOP/{IMF_CA_BULK_KEY}"
    params = {"startPeriod": str(year), "endPeriod": str(year)}
    safe_key = IMF_CA_BULK_KEY.replace("/", "_")
    cache_path = CACHE_DIR / f"imf_sta_BOP_{safe_key}_{year}_{year}.csv"

    if _cache_hit(cache_path, force=force, max_age_days=CACHE_MAX_AGE_DAYS):
        text = cache_path.read_text(encoding="utf-8")
    else:
        _require_cache(cache_path, context=f"IMF BOP bulk CA {year}")
        r = requests.get(
            url,
            params=params,
            headers={"Accept": "text/csv", "User-Agent": "mwi-generate_figures/1.0"},
            timeout=HTTP_TIMEOUT,
        )
        r.raise_for_status()
        text = r.text
        cache_path.write_text(text, encoding="utf-8")

    raw = pd.read_csv(io.StringIO(text))
    if raw.empty or "COUNTRY" not in raw.columns:
        raise ValueError(f"No IMF current-account data for {year}.")

    raw = raw.dropna(subset=["OBS_VALUE"]).copy()
    # STA scale for USD BOP series is millions; convert to US dollars.
    raw["balance_usd"] = _imf_obs_values_usd(raw) * 1_000_000
    raw = raw.dropna(subset=["balance_usd"])
    raw = raw.loc[raw["COUNTRY"].astype(str).str.match(r"^[A-Z]{3}$", na=False)]

    by_country = (
        raw.groupby("COUNTRY", as_index=False)["balance_usd"]
        .sum()
        .rename(columns={"COUNTRY": "iso3"})
    )
    names = get_imf_country_names(force=force)
    by_country["country"] = by_country["iso3"].map(names)
    missing = by_country["country"].isna()
    if missing.any():
        unknown = sorted(by_country.loc[missing, "iso3"].astype(str))
        raise ValueError(f"No country labels for IMF codes: {unknown}")

    exclude = {n.casefold() for n in CA_BALANCE_EXCLUDE_NAMES}
    by_country = by_country.loc[
        ~by_country["country"].str.casefold().isin(exclude)
    ]
    return by_country.sort_values("balance_usd", key=np.abs, ascending=False)


def get_imf_country_names(*, force: bool = False) -> dict[str, str]:
    """Map ISO3 codes to English economy names (World Bank list + IMF overrides)."""
    cache_path = CACHE_DIR / "wb_country_names.json"
    if _cache_hit(cache_path, force=force, max_age_days=CACHE_MAX_AGE_DAYS):
        names = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        _require_cache(cache_path, context="World Bank country list")
        payload = request_json(
            "https://api.worldbank.org/v2/country",
            params={"format": "json", "per_page": 500},
        )
        if not isinstance(payload, list) or len(payload) < 2:
            raise ValueError(f"Unexpected World Bank country response: {payload!r}")
        names = {
            item["id"]: item["name"]
            for item in payload[1]
            if (item.get("region") or {}).get("value") != "Aggregates"
        }
        cache_path.write_text(json.dumps(names), encoding="utf-8")

    return {**names, **IMF_CA_COUNTRY_NAME_OVERRIDES}


def imf_latest_ca_year(
    *,
    probe_years: int = 6,
    coverage_ratio: float = 0.9,
    min_countries: int = 120,
    force: bool = False,
) -> int:
    """Newest year with near-complete IMF current-account coverage."""
    current = dt.date.today().year
    counts: dict[int, int] = {}
    for year in range(current, current - probe_years, -1):
        try:
            counts[year] = len(imf_bop_current_accounts(year, force=force))
        except (OfflineCacheError, ValueError):
            counts[year] = 0

    if not counts or max(counts.values()) == 0:
        raise ValueError("Could not determine a year with IMF current-account data.")

    threshold = max(int(max(counts.values()) * coverage_ratio), min_countries)
    for year in sorted(counts, reverse=True):
        if counts[year] >= threshold:
            return year
    return max(counts, key=counts.get)


def prepare_global_ca_treemap(
    year: int | None = None,
    *,
    min_countries: int = 20,
    max_countries: int = 40,
    force: bool = False,
) -> tuple[pd.DataFrame, int]:
    """Top economies by |CA| plus an aggregated *Other* row for the treemap."""
    if year is None:
        year = imf_latest_ca_year(force=force)

    data = imf_bop_current_accounts(year, force=force)
    data = data.assign(abs_balance=data["balance_usd"].abs()).sort_values(
        "abs_balance", ascending=False
    )

    best_num: int | None = None
    min_other = float("inf")
    for num in range(min_countries, max_countries + 1):
        top = data.head(num)
        rest = data.iloc[num:]
        if rest.empty:
            best_num = num
            break
        other_size = abs(rest["balance_usd"].sum())
        if other_size < min_other:
            best_num = num
            min_other = other_size

    if best_num is None:
        raise ValueError("Could not select a country count for the treemap.")

    top = data.head(best_num)
    rest = data.iloc[best_num:]
    if not rest.empty:
        other = pd.DataFrame(
            [
                {
                    "iso3": "OTH",
                    "country": "Other",
                    "balance_usd": rest["balance_usd"].sum(),
                }
            ]
        )
        top = pd.concat([top[["iso3", "country", "balance_usd"]], other], ignore_index=True)

    return top[["country", "balance_usd"]], year



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

        if _cache_hit(cache_path, force=force, max_age_days=CACHE_MAX_AGE_DAYS):
            payload = json.loads(cache_path.read_text(encoding="utf-8"))
        else:
            _require_cache(cache_path, context=f"World Bank WDI {indicator}")
            payload = request_json(url, params=params)
            cache_path.parent.mkdir(parents=True, exist_ok=True)
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

    if _cache_hit(cache_path, force=force, max_age_days=CACHE_MAX_AGE_DAYS):
        return json.loads(cache_path.read_text(encoding="utf-8"))

    _require_cache(cache_path, context=f"HDX package {package_id}")
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
    dashed: Sequence[str] | None = None,
    plot_type: str = "line",
    bar_width: float = 0.15,
    ymin: float | None = None,
    y2min: float | None = None,
    legend: bool = False,
) -> plt.Figure:
    """Create a lecture-style line or bar plot with optional secondary y-axis."""
    fig, ax = plt.subplots(figsize=(12, 6))

    secondary_y = list(secondary_y or [])
    dashed_cols = set(dashed or [])
    primary_cols = [col for col in data.columns if col not in secondary_y]

    if plot_type not in {"line", "bar"}:
        raise ValueError("plot_type must be either 'line' or 'bar'.")

    x_values = data.index
    if plot_type == "bar":
        x_values = np.arange(len(data))

    for i, col in enumerate(primary_cols):
        color = PRIMARY_COLORS[i % len(PRIMARY_COLORS)]
        linestyle = "--" if col in dashed_cols else "-"
        if plot_type == "line":
            ax.plot(data.index, data[col], label=col, color=color, linestyle=linestyle)
        else:
            offset = (i - len(primary_cols) / 2) * bar_width + bar_width / 2
            ax.bar(x_values + offset, data[col], label=col, color=color, width=bar_width)

    theme = _active_theme
    ax.set_xlabel(xlabel, fontsize=12, color=theme.label_color)
    ax.set_ylabel(ylabel, fontsize=12, color=theme.label_color)
    ax.set_ylim(bottom=ymin)
    ax.grid(True, which="both", color=theme.grid_color, linestyle="--", linewidth=0.5)
    ax.tick_params(colors=theme.tick_color, which="both")

    if plot_type == "bar" and isinstance(data.index, pd.DatetimeIndex):
        ax.set_xticks(x_values)
        ax.set_xticklabels(data.index.strftime("%Y-%m-%d"), rotation=45, ha="right")

    ax2 = None
    if secondary_y:
        ax2 = ax.twinx()
        for i, col in enumerate(secondary_y):
            color = SECONDARY_COLORS[i % len(SECONDARY_COLORS)]
            linestyle = "--" if col in dashed_cols else "-"
            if plot_type == "line":
                ax2.plot(data.index, data[col], label=col, color=color, linestyle=linestyle)
            else:
                offset = (i - len(secondary_y) / 2) * bar_width + bar_width / 2
                ax2.bar(x_values + offset, data[col], label=col, color=color, width=bar_width, alpha=0.7)
        ax2.set_ylim(bottom=y2min)
        ax2.set_ylabel(
            secondary_y_label or secondary_y[0],
            fontsize=12,
            color=theme.label_color,
        )
        ax2.tick_params(colors=theme.tick_color, which="both")

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
            color=theme.source_color,
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
TOTAL_CO2_EMISSIONS_INDICATOR = "EN.GHG.CO2.MT.CE.AR5"


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



# India: net direct investment inflows (financial account, USD, annual, millions).
# Key verified against legacy chart: 100 * series / WDI GDP ≈ FDI net inflows (% of GDP).
INDIA_FDI_BOP_KEY = "IND.L_NIL_T.D_F.USD.A"


def india_fdi_gdp(file_path: Path | str, *, force: bool = False) -> None:
    """Plot FDI net inflows as a share of GDP for India (IMF BOP + WDI GDP)."""
    fdi_usd_m = imf_sta_series("BOP", INDIA_FDI_BOP_KEY, 1990, 2024, freq="A", force=force)
    fdi_by_year = pd.Series(
        fdi_usd_m.to_numpy(),
        index=fdi_usd_m.index.year,
        dtype="float64",
    )

    gdp = get_wdi_data(
        ["NY.GDP.MKTP.CD"],
        ["IN"],
        start_year=1990,
        end_year=2024,
        force=force,
    )
    gdp_usd_m = gdp[("NY.GDP.MKTP.CD", "IND")] / 1e6
    gdp_usd_m.index = gdp_usd_m.index.year

    ratio = 100 * fdi_by_year / gdp_usd_m
    data = pd.DataFrame({"Indien": ratio}).dropna().sort_index()
    fig = create_plot(
        data,
        "Jahr",
        "% des BIP",
        "IMF Balance of Payments (BPM6); World Bank WDI (GDP, current USD)",
    )
    save_figure(fig, file_path)


def create_ca_treemap(
    data: pd.DataFrame,
    year: int,
    data_source: str,
) -> plt.Figure:
    """Treemap of current-account surpluses (green) and deficits (red) in billion USD."""
    wrap_length = 11
    surplus_color = PRIMARY_COLORS[1]
    deficit_color = PRIMARY_COLORS[0]
    theme = _active_theme

    surplus = data[data["balance_usd"] > 0].copy()
    deficit = data[data["balance_usd"] < 0].copy()

    def label_rows(frame: pd.DataFrame) -> pd.Series:
        names = frame["country"].astype(str).str.wrap(wrap_length)
        billions = (frame["balance_usd"] / 1e9).round(0).astype(int).astype(str)
        return names + "\n" + billions

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(20, 10))
    plt.subplots_adjust(left=0.01, right=0.99, top=0.99, bottom=0.06, wspace=0.1)

    if not surplus.empty:
        squarify.plot(
            sizes=surplus["balance_usd"],
            label=label_rows(surplus),
            alpha=0.8,
            ax=ax1,
            pad=True,
            color=surplus_color,
            text_kwargs={"color": theme.annotation_color},
        )
    ax1.axis("off")

    if not deficit.empty:
        squarify.plot(
            sizes=-deficit["balance_usd"],
            label=label_rows(deficit),
            alpha=0.7,
            ax=ax2,
            pad=True,
            color=deficit_color,
            text_kwargs={"color": theme.annotation_color},
        )
    ax2.axis("off")

    fig.text(
        0.99,
        0.04,
        f"Leistungsbilanzsaldo {year} (Mrd. USD). Quelle: {data_source}",
        ha="right",
        fontsize=12,
        color=theme.source_color,
    )
    return fig


def global_ca_balances(
    file_path: Path | str,
    *,
    year: int | None = None,
    force: bool = False,
) -> None:
    """Treemap of global current-account balances (IMF BOP, latest widely available year)."""
    plot_data, plot_year = prepare_global_ca_treemap(year=year, force=force)
    fig = create_ca_treemap(
        plot_data,
        plot_year,
        "IMF Balance of Payments (STA, BPM6)",
    )
    save_figure(fig, file_path)


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



def world_co2_total(file_path: Path | str) -> None:
    """Plot global total CO2 emissions excluding LULUCF (Gt CO2e)."""
    df = get_wdi_data(
        [TOTAL_CO2_EMISSIONS_INDICATOR],
        ["WLD"],
        start_year=1990,
        end_year=2025,
        source=None,
    )
    emissions_gt = df[(TOTAL_CO2_EMISSIONS_INDICATOR, "WLD")] / 1000
    data = pd.DataFrame({"Welt": emissions_gt})
    fig = create_plot(
        data,
        "Jahr",
        "Gt CO₂e",
        "World Bank World Development Indicators; EDGAR/JRC; IEA",
        ymin=20,
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



IMF_COMMODITY_XLSX_URL = (
    "https://www.imf.org/-/media/files/research/commodityprices/monthly/external-data.xlsx"
)

# IMF external-data.xlsx: row 0 = commodity codes, row 1 = descriptions, data from row 4.
IMF_COMMODITY_SERIES: dict[str, tuple[str | None, str | None]] = {
    "Erdöl (Brent)": ("POILBRE", None),
    "Steinkohle": ("PCOALAU", None),
    "Kupfer": ("PCOPP", None),
    "Nickel": ("PNICK", None),
    "Kobalt": ("PCOBA", None),
    "Lithium": (None, "lithium"),
    "Seltene Erden": (None, "rare earth"),
}


def load_imf_commodity_levels(*, force: bool = False) -> pd.DataFrame:
    """Load monthly IMF primary commodity prices (USD/metric ton) from external-data.xlsx."""
    cache_path = CACHE_DIR / "imf_external-data.xlsx"
    download_file(IMF_COMMODITY_XLSX_URL, cache_path, force=force)
    raw = pd.read_excel(cache_path, sheet_name="External", header=None)

    code_row = raw.iloc[0].astype(str)
    desc_row = raw.iloc[1].astype(str)
    dates = pd.to_datetime(
        raw.iloc[4:, 0].astype(str).str.replace("M", "-", regex=False),
        format="%Y-%m",
    )
    out: dict[str, pd.Series] = {}
    for label, (code, desc_hint) in IMF_COMMODITY_SERIES.items():
        col_idx: int | None = None
        if code is not None:
            matches = np.flatnonzero(code_row.values == code)
            if len(matches) != 1:
                raise ValueError(f"Expected one IMF column for {code}, found {len(matches)}.")
            col_idx = int(matches[0])
        elif desc_hint is not None:
            hint = desc_hint.lower()
            matches = [
                i
                for i in range(raw.shape[1])
                if hint in desc_row.iloc[i].lower()
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"Expected one IMF column matching {desc_hint!r}, found {len(matches)}."
                )
            col_idx = matches[0]
        values = pd.to_numeric(raw.iloc[4:, col_idx], errors="coerce")
        out[label] = pd.Series(values.to_numpy(), index=dates, name=label)
    return pd.DataFrame(out).sort_index()


def index_to_month(
    series: pd.Series,
    year: int,
    month: int = 1,
) -> pd.Series:
    """Index a monthly series to 100 in the given year-month (first obs in period if needed)."""
    s = series.dropna()
    if s.empty:
        raise ValueError(f"No data to index for {series.name!r}.")
    mask = (s.index.year == year) & (s.index.month == month)
    if mask.any():
        baseline = float(s.loc[mask].iloc[0])
    else:
        in_year = s[s.index.year == year]
        if in_year.empty:
            raise ValueError(f"No observations in {year} for {series.name!r}.")
        baseline = float(in_year.iloc[0])
    if baseline == 0:
        raise ValueError(f"Invalid baseline for {series.name!r} in {year}-{month:02d}.")
    return s / baseline * 100


def raw_materials(file_path: Path | str, *, force: bool = False) -> None:
    """Commodity prices indexed to June 2012 = 100 (IMF primary commodity prices)."""
    levels = load_imf_commodity_levels(force=force)
    labels = (
        "Erdöl (Brent)",
        "Steinkohle",
        "Kobalt",
        "Lithium",
        "Seltene Erden",
    )
    indexed = {label: index_to_month(levels[label], 2012, 6) for label in labels}
    data = pd.DataFrame(indexed).sort_index()
    fig = create_plot(
        data,
        "Jahr",
        "Index (Jun. 2012 = 100)",
        "IMF Primary Commodity Prices",
        legend=True,
        ymin=0,
    )
    save_figure(fig, file_path)



TRADE_POLICY_UNCERTAINTY_FRED = "EPUTRADE"
DEEP_SEA_FREIGHT_FRED = "PCU483111483111"


def trade_policy_uncertainty(file_path: Path | str) -> None:
    """Trade-policy uncertainty from US newspaper coverage (Baker, Bloom, Davis; monthly)."""
    df = get_fred_series(TRADE_POLICY_UNCERTAINTY_FRED, start_date="2005-01-01")
    data = df.rename(columns={TRADE_POLICY_UNCERTAINTY_FRED: "Handelspolitische Unsicherheit"})
    fig = create_plot(
        data,
        "Datum",
        "Index",
        "Baker, Bloom, Davis; Economic Policy Uncertainty via FRED (EPUTRADE)",
        ymin=0,
    )
    save_figure(fig, file_path)


def container_freight_costs(file_path: Path | str) -> None:
    """Deep sea freight PPI around the COVID-19 supply-chain shock (indexed to 2019 = 100)."""
    df = get_fred_series(DEEP_SEA_FREIGHT_FRED, start_date="2016-01-01")
    levels = df.rename(columns={DEEP_SEA_FREIGHT_FRED: "Hochseefracht"})
    baseline = levels.loc["2019"].mean()
    if baseline.isna().any() or (baseline == 0).any():
        raise ValueError(f"Invalid 2019 baseline for freight PPI: {baseline.to_dict()}")
    data = levels.divide(baseline).multiply(100)
    fig = create_plot(
        data,
        "Jahr",
        "Frachtpreisindex (2019 = 100)",
        "U.S. Bureau of Labor Statistics via FRED (Deep Sea Freight Transportation PPI)",
        ymin=70,
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
        color=_active_theme.annotation_color,
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


def _generate_managed_figures(output_dir: Path) -> None:
    """Write all matplotlib figures managed by this script."""
    global_ca_balances(output_dir / "global_ca_balances.svg")
    india_fdi_gdp(output_dir / "india_fdi_gdp.svg")
    raw_materials(output_dir / "raw_materials.svg")

    trade_openness_by_income_group(output_dir / "trade-as-share-of-gdp.svg")
    poverty_by_income_group(output_dir / "poverty-by-income-group.svg")
    asia_trade_openness(output_dir / "trade-as-share-of-gdp-asia.svg")
    asia_gdp_per_capita(output_dir / "gdp-per-capita-asia.svg")
    trade_policy_uncertainty(output_dir / "trade-policy-uncertainty.svg")

    india_catch_up(output_dir / "india_catch_up.svg")
    india_tech(output_dir / "india_tech_exports.svg")
    thailand_ca_balance(output_dir / "thailand_ca_balance.svg")
    thailand_forex(output_dir / "thailand_forex.svg")
    thailand_ext_debt(output_dir / "thailand_ext_debt.svg")
    thailand_gdp_per_capita(output_dir / "thailand_gdp_per_capita.svg")
    world_co2_total(output_dir / "world_co2_total.svg")
    world_co2(output_dir / "world_co2.svg")
    container_freight_costs(output_dir / "shipping-costs.svg")
    oil_prices_iran_2026(output_dir / "oil_prices_iran_2026.svg")

    chokepoint_trade_volume(
        output_dir / "hormuz_trade_volume_2026.svg",
        selected_chokepoints=("hormuz",),
        start_date="2025-01-01",
        rolling=7,
        index_baseline=("2025-01-01", "2025-12-31"),
    )


def build_all_figures() -> None:
    """Generate slide figures (dark theme) into images/."""
    ensure_directories()
    use_theme(DARK_THEME)
    _generate_managed_figures(IMAGE_DIR)


def build_script_figures() -> None:
    """Generate script-PDF figures (light theme) into lecture/build/figure-svg/."""
    ensure_directories()
    SCRIPT_IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    use_theme(LIGHT_THEME)
    _generate_managed_figures(SCRIPT_IMAGE_DIR)
    chokepoint_trade_volume(
        SCRIPT_IMAGE_DIR / "panama_suez_trade_capacity.svg",
        selected_chokepoints=("panama", "suez"),
        start_date="2019-01-01",
        rolling=28,
        index_baseline=("2019-01-01", "2023-12-31"),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--script",
        action="store_true",
        help="Build light-theme SVGs for the lecture script PDF (default: slide figures).",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Use only data/cache/; never call external APIs (also FIGURES_OFFLINE=1).",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Refresh cached downloads from the network (ignored with --offline).",
    )
    args = parser.parse_args()
    offline = args.offline or os.environ.get("FIGURES_OFFLINE", "").lower() in (
        "1",
        "true",
        "yes",
    )
    if args.force and offline:
        parser.error("--force cannot be used with --offline")
    configure_runtime(offline=offline, force=args.force)
    if args.script:
        build_script_figures()
    else:
        build_all_figures()


if __name__ == "__main__":
    use_theme(DARK_THEME)
    main()
