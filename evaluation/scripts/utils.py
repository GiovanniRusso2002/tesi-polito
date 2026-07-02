"""
Low-level measurement utilities.

Provides:
  - measure_curl   : single timed HTTP request via curl
  - run_benchmark  : N repeated measurements → DataFrame
  - load_raw       : load a saved raw CSV → DataFrame
  - merge_envs     : merge per-environment DataFrames into one with an 'env' column
"""

import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

import pandas as pd

# Ensure the project root is importable regardless of how this module is called.
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config

# ---------------------------------------------------------------------------
# curl format string — values are written to stdout, separated by commas.
# All times are in seconds (floating point).
# Fields:
#   time_namelookup   – DNS resolution complete
#   time_connect      – TCP handshake complete
#   time_appconnect   – TLS handshake complete  (0 for plain HTTP)
#   time_starttransfer– time to first byte (TTFB)
#   time_total        – full request-response cycle
#   http_code         – HTTP response status code
# ---------------------------------------------------------------------------
_CURL_FORMAT = (
    "%{time_namelookup},"
    "%{time_connect},"
    "%{time_appconnect},"
    "%{time_starttransfer},"
    "%{time_total},"
    "%{http_code}"
)


def measure_curl(
    url: str,
    *,
    headers: Optional[dict[str, str]] = None,
    auth_token: Optional[str] = None,
    timeout: int = config.REQUEST_TIMEOUT,
) -> Optional[dict]:
    """
    Issue a single HTTP GET request and return timing measurements.

    Parameters
    ----------
    url        : Full URL to request.
    headers    : Optional extra HTTP headers (dict).
    auth_token : If provided, adds ``Authorization: Bearer <token>``.
    timeout    : Maximum request time in seconds (curl --max-time).

    Returns
    -------
    dict with keys ``dns``, ``tcp``, ``tls``, ``ttfb``, ``total``
    (all in seconds, as floats) and ``http_code`` (int), or ``None``
    if the request fails.
    """
    cmd = [
        "curl",
        "--silent",
        "--output", "/dev/null",
        "--max-time", str(timeout),
        "--write-out", _CURL_FORMAT,
    ]

    if auth_token:
        cmd += ["--header", f"Authorization: Bearer {auth_token}"]

    for key, value in (headers or {}).items():
        cmd += ["--header", f"{key}: {value}"]

    cmd.append(url)

    try:
        raw = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip()
        parts = raw.split(",")
        if len(parts) != 6:
            return None
        dns, tcp, tls, ttfb, total, http_code = parts
        return {
            "dns":       float(dns),
            "tcp":       float(tcp),
            "tls":       float(tls),
            "ttfb":      float(ttfb),
            "total":     float(total),
            "http_code": int(http_code),
        }
    except (subprocess.CalledProcessError, ValueError):
        return None


def run_benchmark(
    url: str,
    n: int = config.N_REQUESTS,
    *,
    label: str = "",
    headers: Optional[dict[str, str]] = None,
    auth_token: Optional[str] = None,
    retry: bool = config.RETRY_ON_ERROR,
    delay: float = 0.0,
) -> pd.DataFrame:
    """
    Execute *n* independent HTTP measurements against *url*.

    Each successful measurement is stored as one row. Failed requests
    are retried once (if ``retry=True``) and then skipped with a warning.

    Parameters
    ----------
    url        : Target URL.
    n          : Number of repetitions.
    label      : Descriptive label printed to stdout during collection.
    headers    : Extra HTTP headers forwarded to every request.
    auth_token : Bearer token for authenticated endpoints.
    retry      : Retry a failed request once before skipping it.
    delay      : Optional inter-request sleep in seconds (avoid rate-limiting).

    Returns
    -------
    DataFrame with columns: run, dns, tcp, tls, ttfb, total, http_code
    """
    rows = []
    skipped = 0

    for i in range(1, n + 1):
        result = measure_curl(url, headers=headers, auth_token=auth_token)

        if result is None and retry:
            time.sleep(0.5)
            result = measure_curl(url, headers=headers, auth_token=auth_token)

        if result is None:
            skipped += 1
            prefix = f"[{label}] " if label else ""
            print(f"{prefix}run {i}/{n}  FAILED (skipped)", file=sys.stderr)
            continue

        rows.append({"run": i, **result})

        if label:
            print(f"[{label}]  {i:>3}/{n}  "
                  f"ttfb={result['ttfb']*1000:6.1f} ms  "
                  f"total={result['total']*1000:6.1f} ms  "
                  f"HTTP {result['http_code']}")

        if delay > 0:
            time.sleep(delay)

    if skipped:
        print(f"WARNING: {skipped}/{n} requests skipped.", file=sys.stderr)

    return pd.DataFrame(rows, columns=["run", "dns", "tcp", "tls", "ttfb", "total", "http_code"])


# ---------------------------------------------------------------------------
# I/O helpers
# ---------------------------------------------------------------------------

def raw_csv_path(benchmark_key: str, env_key: str) -> Path:
    """Return the canonical path for a raw CSV file."""
    return config.DATA_RAW_DIR / f"{benchmark_key}_{env_key}.csv"


def processed_csv_path(benchmark_key: str) -> Path:
    """Return the canonical path for a processed (merged) CSV file."""
    return config.DATA_PROCESSED_DIR / f"{benchmark_key}.csv"


def save_raw(df: pd.DataFrame, benchmark_key: str, env_key: str) -> Path:
    """Persist a raw measurement DataFrame to ``data/raw/``."""
    path = raw_csv_path(benchmark_key, env_key)
    df.to_csv(path, index=False)
    print(f"Saved → {path.relative_to(config.BASE_DIR)}")
    return path


def load_raw(benchmark_key: str, env_key: str) -> pd.DataFrame:
    """Load a raw CSV for one (benchmark, environment) pair."""
    path = raw_csv_path(benchmark_key, env_key)
    if not path.exists():
        raise FileNotFoundError(
            f"Raw data not found: {path}\n"
            f"Run the benchmark first: python run.py benchmark --target {benchmark_key}"
        )
    return pd.read_csv(path)


def merge_envs(benchmark_key: str) -> pd.DataFrame:
    """
    Merge per-environment CSVs into a single DataFrame with an ``env`` column.

    The merged file is written to ``data/processed/{benchmark_key}.csv`` and
    the DataFrame is returned for immediate use.
    """
    frames = []
    for env_key in config.ENVIRONMENTS:
        df = load_raw(benchmark_key, env_key)
        df.insert(0, "env", env_key)
        frames.append(df)

    merged = pd.concat(frames, ignore_index=True)
    path = processed_csv_path(benchmark_key)
    merged.to_csv(path, index=False)
    print(f"Merged → {path.relative_to(config.BASE_DIR)}")
    return merged


def get_auth_token() -> Optional[str]:
    """
    Read the bearer token from the ``OUTSIGHT_TOKEN`` environment variable.
    Returns ``None`` if the variable is not set (no error is raised here;
    callers that require auth should call ``require_auth_token()`` instead).
    """
    return os.environ.get(config.AUTH_ENV_VAR)


def require_auth_token() -> str:
    """
    Read the bearer token or raise a descriptive ``RuntimeError``.
    Use this in benchmark scripts that target authenticated endpoints.
    """
    token = get_auth_token()
    if not token:
        raise RuntimeError(
            f"Environment variable {config.AUTH_ENV_VAR!r} is not set.\n"
            "Obtain a bearer token from the Outsight Cloud UI and export it:\n"
            f"  export {config.AUTH_ENV_VAR}='<your-token>'"
        )
    return token
