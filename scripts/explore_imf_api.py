"""Explore the new IMF SDMX API for migrating legacy lecture figures.

This script is intentionally separate from get_data.py. It is a temporary
exploration tool for finding new IMF dataflow IDs, dimension orders, codelists,
and candidate SDMX keys after the old dataservices.imf.org / IFS endpoint became
unreliable.

Typical workflow:

    python scripts/explore_imf_api.py dataflows
    python scripts/explore_imf_api.py search "balance of payments"
    python scripts/explore_imf_api.py search "international investment position"
    python scripts/explore_imf_api.py search "exchange rate"
    python scripts/explore_imf_api.py search "international liquidity"
    python scripts/explore_imf_api.py structure BOP
    python scripts/explore_imf_api.py structure IIP

The exact IMF dataflow IDs may differ from the examples above. Use the search
command first, then inspect likely dataflows with the structure command.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

import pandas as pd
import requests

# -----------------------------------------------------------------------------
# Configuration
# -----------------------------------------------------------------------------

CACHE_DIR = Path("data/cache/imf_exploration")
HTTP_TIMEOUT = 60
CACHE_MAX_AGE_DAYS = 7

# The IMF data API and the IMF structure registry are not always interchangeable.
# Data queries should use api.imf.org; structural metadata are more reliable via
# IMF SDMX Central. See also: https://data.imf.org/en/Resource-Pages/IMF-API
IMF_DATA_SDMX_21_BASE_URL = "https://api.imf.org/external/sdmx/2.1"
IMF_STRUCTURE_SDMX_21_BASE_URL = "https://sdmxcentral.imf.org/ws/public/sdmxapi/rest"

# IMF's SDMX API supports different response formats. JSON structure responses
# are most convenient for dataflows and datastructures.
SDMX_STRUCTURE_JSON_HEADERS = {
    "Accept": "application/vnd.sdmx.structure+json;version=1.0.0"
}

# CSV is easier to inspect for data queries once a valid dataflow/key is known.
SDMX_CSV_HEADERS = {"Accept": "text/csv"}


# -----------------------------------------------------------------------------
# Generic utilities
# -----------------------------------------------------------------------------


def ensure_cache_dir() -> None:
    """Create the cache directory if it does not exist."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)


def cache_is_fresh(path: Path, max_age_days: int = CACHE_MAX_AGE_DAYS) -> bool:
    """Return True if a cache file exists and is younger than max_age_days."""
    if not path.exists():
        return False
    age_seconds = dt.datetime.now().timestamp() - path.stat().st_mtime
    return age_seconds < max_age_days * 24 * 60 * 60


def safe_filename(value: str) -> str:
    """Return a filesystem-safe string for cache filenames."""
    return (
        value.replace("/", "_")
        .replace("\\", "_")
        .replace(":", "_")
        .replace("?", "_")
        .replace("&", "_")
        .replace("=", "_")
        .replace(".", "_")
        .replace(" ", "_")
    )


def request_json(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    cache_path: Path | None = None,
    force: bool = False,
) -> Any:
    """Fetch JSON from a URL with optional caching.

    Some IMF endpoints return XML or HTML error pages even when JSON was
    requested. In that case, save the raw response next to the JSON cache and
    raise a diagnostic error instead of a low-level JSONDecodeError.
    """
    ensure_cache_dir()

    if cache_path and cache_path.exists() and not force and cache_is_fresh(cache_path):
        return json.loads(cache_path.read_text(encoding="utf-8"))

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()

    try:
        payload = response.json()
    except requests.exceptions.JSONDecodeError as exc:
        debug_path = None
        if cache_path:
            debug_path = cache_path.with_suffix(".response.txt")
            debug_path.write_text(
                response.text[:20000],
                encoding="utf-8",
                errors="replace",
            )

        content_type = response.headers.get("Content-Type", "unknown")
        preview = response.text[:500].replace("\n", " ").replace("\r", " ")
        message = (
            "The endpoint did not return JSON. This usually means the IMF "
            "endpoint returned XML/HTML, the dataflow ID is wrong, or the "
            "structure endpoint differs from the data endpoint.\n\n"
            f"URL: {response.url}\n"
            f"Status: {response.status_code}\n"
            f"Content-Type: {content_type}\n"
            f"Response preview: {preview}\n"
            f"Raw response saved to: {debug_path}"
        )
        raise ValueError(message) from exc

    if cache_path:
        cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    return payload


def request_csv(
    url: str,
    *,
    params: Mapping[str, Any] | None = None,
    headers: Mapping[str, str] | None = None,
    cache_path: Path | None = None,
    force: bool = False,
) -> pd.DataFrame:
    """Fetch CSV from a URL with optional caching."""
    ensure_cache_dir()

    if cache_path and cache_path.exists() and not force and cache_is_fresh(cache_path):
        return pd.read_csv(cache_path)

    response = requests.get(
        url,
        params=params,
        headers=headers,
        timeout=HTTP_TIMEOUT,
    )
    response.raise_for_status()

    if cache_path:
        cache_path.write_bytes(response.content)
        return pd.read_csv(cache_path)

    from io import StringIO

    return pd.read_csv(StringIO(response.text))


def extract_text(value: Any) -> str | None:
    """Extract English text from SDMX name/description fields."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("en") or value.get("en-US") or next(iter(value.values()), None)
    return str(value)


def print_dataframe(df: pd.DataFrame, max_rows: int = 50) -> None:
    """Print a DataFrame without truncating important columns too aggressively."""
    with pd.option_context(
        "display.max_rows",
        max_rows,
        "display.max_columns",
        20,
        "display.width",
        180,
        "display.max_colwidth",
        120,
    ):
        print(df)


# -----------------------------------------------------------------------------
# IMF SDMX discovery
# -----------------------------------------------------------------------------


def get_imf_dataflows(*, force: bool = False) -> pd.DataFrame:
    """Return IMF SDMX dataflows as a searchable DataFrame."""
    url = f"{IMF_STRUCTURE_SDMX_21_BASE_URL}/dataflow/all/all/latest"
    cache_path = CACHE_DIR / "imf_sdmx_dataflows.json"

    payload = request_json(
        url,
        headers=SDMX_STRUCTURE_JSON_HEADERS,
        cache_path=cache_path,
        force=force,
    )

    dataflows = payload.get("data", {}).get("dataflows", [])
    if isinstance(dataflows, dict):
        dataflows = dataflows.values()

    rows: list[dict[str, Any]] = []
    for flow in dataflows:
        rows.append(
            {
                "id": flow.get("id"),
                "name": extract_text(flow.get("name")),
                "description": extract_text(flow.get("description")),
                "agency": flow.get("agencyID") or flow.get("agency"),
                "version": flow.get("version"),
            }
        )

    if not rows:
        raise ValueError(
            "Could not parse dataflows from IMF response. "
            f"Inspect cached file: {cache_path}"
        )

    return pd.DataFrame(rows).sort_values(["id", "name"], na_position="last")


def search_imf_dataflows(query: str, *, force: bool = False) -> pd.DataFrame:
    """Search IMF dataflow IDs, names, and descriptions for a keyword."""
    flows = get_imf_dataflows(force=force)
    query_lower = query.lower()

    searchable = (
        flows["id"].fillna("").str.lower()
        + " "
        + flows["name"].fillna("").str.lower()
        + " "
        + flows["description"].fillna("").str.lower()
    )
    return flows.loc[searchable.str.contains(query_lower, regex=False), :].reset_index(
        drop=True
    )


def get_imf_datastructure(dataflow_id: str, *, force: bool = False) -> dict[str, Any]:
    """Fetch the SDMX datastructure for an IMF dataflow."""
    url = f"{IMF_STRUCTURE_SDMX_21_BASE_URL}/datastructure/all/{dataflow_id}/latest"
    cache_path = CACHE_DIR / f"imf_sdmx_structure_{safe_filename(dataflow_id)}.json"

    return request_json(
        url,
        headers=SDMX_STRUCTURE_JSON_HEADERS,
        cache_path=cache_path,
        force=force,
    )


def parse_sdmx_urn(urn: str) -> dict[str, str]:
    """Parse a common SDMX codelist URN into agency, id, and version."""
    if "=" not in urn:
        raise ValueError(f"Could not parse SDMX URN: {urn}")

    resource = urn.split("=", 1)[1]
    agency, rest = resource.split(":", 1)
    resource_id, version = rest.rsplit("(", 1)

    return {
        "agency": agency,
        "id": resource_id,
        "version": version.rstrip(")"),
    }


def get_dimension_codelists(dataflow_id: str, *, force: bool = False) -> pd.DataFrame:
    """Return dimensions and their referenced codelist URNs for a dataflow."""
    payload = get_imf_datastructure(dataflow_id, force=force)
    data = payload.get("data", {})
    structures = data.get("dataStructures") or data.get("datastructures") or []

    if isinstance(structures, dict):
        structures = list(structures.values())

    if not structures:
        raise ValueError(f"Could not locate dataStructures for {dataflow_id}.")

    components = structures[0].get("dataStructureComponents", {})
    dimensions = (components.get("dimensionList") or {}).get("dimensions", [])

    rows = []

    for position, dim in enumerate(dimensions):
        local_rep = dim.get("localRepresentation", {}) or {}
        enumeration = local_rep.get("enumeration")

        enum_ref = None
        if isinstance(enumeration, dict):
            enum_ref = enumeration.get("id") or enumeration.get("urn")
        elif isinstance(enumeration, str):
            enum_ref = enumeration

        rows.append(
            {
                "position": position,
                "id": dim.get("id"),
                "name": extract_text(dim.get("name")) or extract_text(dim.get("names")),
                "codelist": enum_ref,
            }
        )

    return pd.DataFrame(rows)


def get_codelist(codelist_urn: str, *, force: bool = False) -> pd.DataFrame:
    """Fetch a codelist referenced by an IMF datastructure dimension."""
    parts = parse_sdmx_urn(codelist_urn)

    agency = parts["agency"]
    codelist_id = parts["id"]
    version = parts["version"]

    url = (
        f"{IMF_STRUCTURE_SDMX_21_BASE_URL}/codelist/"
        f"{agency}/{codelist_id}/{version}"
    )

    cache_path = (
        CACHE_DIR
        / f"imf_codelist_{safe_filename(agency)}_{safe_filename(codelist_id)}_{safe_filename(version)}.json"
    )

    payload = request_json(
        url,
        headers=SDMX_STRUCTURE_JSON_HEADERS,
        cache_path=cache_path,
        force=force,
    )

    codelists = payload.get("data", {}).get("codelists", [])
    if isinstance(codelists, dict):
        codelists = list(codelists.values())

    rows = []

    for codelist in codelists:
        codes = codelist.get("items", []) or codelist.get("codes", [])
        for code in codes:
            rows.append(
                {
                    "id": code.get("id"),
                    "name": extract_text(code.get("name")) or extract_text(code.get("names")),
                    "description": extract_text(code.get("description"))
                    or extract_text(code.get("descriptions")),
                }
            )

    if not rows:
        raise ValueError(
            f"Could not parse codelist {codelist_urn}. "
            f"Inspect cached file: {cache_path}"
        )

    return pd.DataFrame(rows).sort_values("id", na_position="last")


def summarize_datastructure(dataflow_id: str, *, force: bool = False) -> None:
    """Print a readable first-pass summary of an IMF datastructure payload."""
    payload = get_imf_datastructure(dataflow_id, force=force)
    cache_path = CACHE_DIR / f"imf_sdmx_structure_{safe_filename(dataflow_id)}.json"

    print(f"\nDataflow: {dataflow_id}")
    print(f"Raw structure cache: {cache_path}")

    # The SDMX JSON layout can vary. Print a few useful top-level hints first.
    print("\nTop-level keys:")
    print(list(payload.keys()))

    data = payload.get("data", {})
    print("\n'data' keys:")
    print(list(data.keys()))

    # Try to locate dimension information in common SDMX JSON shapes.
    structures = data.get("dataStructures") or data.get("datastructures") or []
    if isinstance(structures, dict):
        structures = list(structures.values())

    if not structures:
        print("\nCould not locate dataStructures automatically.")
        print("First 5000 chars of payload:")
        print(json.dumps(payload, indent=2)[:5000])
        return

    structure = structures[0]
    print("\nStructure keys:")
    print(list(structure.keys()))

    dimension_lists = []

    # Common SDMX-JSON structure layout.
    data_structure_components = structure.get("dataStructureComponents", {})
    dimension_list = data_structure_components.get("dimensionList")
    if dimension_list:
        dimensions = dimension_list.get("dimensions", [])
        if dimensions:
            dimension_lists.append(dimensions)

    # Fallback: inspect anything named dimensions.
    if not dimension_lists:
        for key, value in structure.items():
            if "dimension" in key.lower():
                print(f"\nPossible dimension field: {key}")
                print(json.dumps(value, indent=2)[:3000])

    if dimension_lists:
        print("\nDimensions in apparent key order:")
        rows = []
        for i, dim in enumerate(dimension_lists[0]):
            local_rep = dim.get("localRepresentation", {}) or {}
            enum_ref = None
            enumeration = local_rep.get("enumeration")
            if isinstance(enumeration, dict):
                enum_ref = enumeration.get("id") or enumeration.get("urn")
            elif isinstance(enumeration, str):
                enum_ref = enumeration
            rows.append(
                {
                    "position": i,
                    "id": dim.get("id"),
                    "name": extract_text(dim.get("name")),
                    "codelist": enum_ref,
                }
            )
        print_dataframe(pd.DataFrame(rows), max_rows=100)

    print("\nFirst 5000 chars of raw structure payload:")
    print(json.dumps(payload, indent=2)[:5000])


def search_structure_payload(
    dataflow_id: str, query: str, *, force: bool = False
) -> None:
    """Print snippets from a datastructure JSON payload that contain a query string."""
    payload = get_imf_datastructure(dataflow_id, force=force)
    text = json.dumps(payload, indent=2)
    query_lower = query.lower()
    text_lower = text.lower()

    hits = []
    start = 0
    while True:
        idx = text_lower.find(query_lower, start)
        if idx == -1:
            break
        hits.append(idx)
        start = idx + len(query)

    if not hits:
        print(
            f"No occurrences of '{query}' found in structure payload for {dataflow_id}."
        )
        return

    print(
        f"Found {len(hits)} occurrence(s) of '{query}' in {dataflow_id}. Showing first 10:\n"
    )
    for idx in hits[:10]:
        snippet_start = max(0, idx - 500)
        snippet_end = min(len(text), idx + 1000)
        print("-" * 100)
        print(text[snippet_start:snippet_end])


# -----------------------------------------------------------------------------
# Experimental data query helper
# -----------------------------------------------------------------------------


def get_imf_sdmx_csv(
    dataflow_id: str,
    key: str,
    *,
    start_period: str | int | None = None,
    end_period: str | int | None = None,
    force: bool = False,
) -> pd.DataFrame:
    """Fetch an IMF SDMX data query as CSV.

    The key must match the dimension order of the selected dataflow. Use the
    structure command first to determine that order.
    """
    url = f"{IMF_DATA_SDMX_21_BASE_URL}/data/{dataflow_id}/{key}"
    params: dict[str, Any] = {}
    if start_period is not None:
        params["startPeriod"] = start_period
    if end_period is not None:
        params["endPeriod"] = end_period

    cache_name = f"imf_sdmx_data_{dataflow_id}_{key}_{start_period}_{end_period}.csv"
    cache_path = CACHE_DIR / safe_filename(cache_name)

    return request_csv(
        url,
        params=params,
        headers=SDMX_CSV_HEADERS,
        cache_path=cache_path,
        force=force,
    )


def run_test_query(args: argparse.Namespace) -> None:
    """Run an experimental SDMX CSV query and print the resulting DataFrame."""
    df = get_imf_sdmx_csv(
        args.dataflow_id,
        args.key,
        start_period=args.start,
        end_period=args.end,
        force=args.force,
    )
    print_dataframe(df.head(args.rows), max_rows=args.rows)
    print("\nColumns:")
    print(list(df.columns))


def list_dimension_codelists(args: argparse.Namespace) -> None:
    """Print dataflow dimensions and their codelist URNs."""
    df = get_dimension_codelists(args.dataflow_id, force=args.force)
    print_dataframe(df, max_rows=100)


def print_codelist(args: argparse.Namespace) -> None:
    """Print a codelist by URN, optionally filtered by a search term."""
    df = get_codelist(args.codelist_urn, force=args.force)

    if args.query:
        query = args.query.lower()
        searchable = (
            df["id"].fillna("").str.lower()
            + " "
            + df["name"].fillna("").str.lower()
            + " "
            + df["description"].fillna("").str.lower()
        )
        df = df.loc[searchable.str.contains(query, regex=False), :]

    print_dataframe(df.head(args.rows), max_rows=args.rows)


# -----------------------------------------------------------------------------
# CLI
# -----------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    parser = argparse.ArgumentParser(
        description="Explore IMF SDMX dataflows and structures for migration work."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    dataflows_parser = subparsers.add_parser("dataflows", help="List IMF dataflows.")
    dataflows_parser.add_argument(
        "--force", action="store_true", help="Refresh cached metadata."
    )
    dataflows_parser.add_argument(
        "--rows", type=int, default=100, help="Maximum rows to print."
    )

    search_parser = subparsers.add_parser("search", help="Search IMF dataflows.")
    search_parser.add_argument("query", help="Search term.")
    search_parser.add_argument(
        "--force", action="store_true", help="Refresh cached metadata."
    )
    search_parser.add_argument(
        "--rows", type=int, default=50, help="Maximum rows to print."
    )

    structure_parser = subparsers.add_parser(
        "structure", help="Inspect a dataflow's SDMX datastructure."
    )
    structure_parser.add_argument(
        "dataflow_id", help="IMF dataflow ID, e.g. BOP or IIP."
    )
    structure_parser.add_argument(
        "--force", action="store_true", help="Refresh cached metadata."
    )

    find_parser = subparsers.add_parser(
        "find-in-structure", help="Search raw structure JSON for a string."
    )
    find_parser.add_argument("dataflow_id", help="IMF dataflow ID.")
    find_parser.add_argument("query", help="String to search in the structure JSON.")
    find_parser.add_argument(
        "--force", action="store_true", help="Refresh cached metadata."
    )

    query_parser = subparsers.add_parser(
        "query", help="Run an experimental SDMX CSV data query."
    )
    query_parser.add_argument("dataflow_id", help="IMF dataflow ID.")
    query_parser.add_argument(
        "key", help="SDMX key matching the dataflow dimension order."
    )
    query_parser.add_argument(
        "--start", default=None, help="startPeriod, e.g. 1990 or 1990-Q1."
    )
    query_parser.add_argument(
        "--end", default=None, help="endPeriod, e.g. 2002 or 2002-Q4."
    )
    query_parser.add_argument("--rows", type=int, default=20, help="Rows to print.")
    query_parser.add_argument(
        "--force", action="store_true", help="Refresh cached data."
    )

    dimensions_parser = subparsers.add_parser(
        "dimensions", help="List dimensions and codelist URNs for a dataflow."
    )
    dimensions_parser.add_argument("dataflow_id", help="IMF dataflow ID.")
    dimensions_parser.add_argument("--force", action="store_true", help="Refresh cached metadata.")

    codelist_parser = subparsers.add_parser(
        "codelist", help="Fetch and print a codelist referenced by a dimension."
    )
    codelist_parser.add_argument("codelist_urn", help="Full SDMX codelist URN.")
    codelist_parser.add_argument("--query", default=None, help="Optional search term.")
    codelist_parser.add_argument("--rows", type=int, default=100, help="Rows to print.")
    codelist_parser.add_argument("--force", action="store_true", help="Refresh cached metadata.")

    return parser


def main() -> None:
    """Run the command-line interface."""
    parser = build_parser()
    args = parser.parse_args()
    ensure_cache_dir()

    if args.command == "dataflows":
        df = get_imf_dataflows(force=args.force)
        print_dataframe(
            df[["id", "name", "description"]].head(args.rows), max_rows=args.rows
        )
        return

    if args.command == "search":
        df = search_imf_dataflows(args.query, force=args.force)
        print_dataframe(
            df[["id", "name", "description"]].head(args.rows), max_rows=args.rows
        )
        return

    if args.command == "structure":
        summarize_datastructure(args.dataflow_id, force=args.force)
        return

    if args.command == "find-in-structure":
        search_structure_payload(args.dataflow_id, args.query, force=args.force)
        return

    if args.command == "query":
        run_test_query(args)
        return

    if args.command == "dimensions":
        list_dimension_codelists(args)
        return

    if args.command == "codelist":
        print_codelist(args)
        return

    parser.error(f"Unknown command: {args.command}")


if __name__ == "__main__":
    main()
