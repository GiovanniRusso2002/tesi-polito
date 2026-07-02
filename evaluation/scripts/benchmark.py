"""
Generic BenchmarkRunner.

Encapsulates the run → save → (optionally) merge workflow for a single
benchmark target. Individual benchmark scripts instantiate this class and
pass it environment-specific URLs (and headers).
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import pandas as pd

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config
from scripts.utils import run_benchmark, save_raw, merge_envs


class BenchmarkRunner:
    """
    Run a timed HTTP benchmark for every configured environment and persist
    the measurements to ``data/raw/``.

    Parameters
    ----------
    key     : Short identifier matching a key in ``config.ENDPOINTS``
              (e.g. ``"home"``, ``"api_organizations"``).
    label   : Human-readable name used in progress output.
    n       : Number of requests per environment. Defaults to ``config.N_REQUESTS``.
    headers : Extra HTTP headers applied to every request.
    auth    : If ``True``, the bearer token from the environment variable
              ``OUTSIGHT_TOKEN`` is attached to every request.
    delay   : Optional inter-request sleep in seconds.
    """

    def __init__(
        self,
        key: str,
        label: str,
        *,
        n: int = config.N_REQUESTS,
        headers: Optional[dict[str, str]] = None,
        auth: bool = False,
        delay: float = 0.0,
    ) -> None:
        self.key     = key
        self.label   = label
        self.n       = n
        self.headers = headers or {}
        self.auth    = auth
        self.delay   = delay

        self._results: dict[str, pd.DataFrame] = {}

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def run(self, environments: Optional[dict[str, str]] = None) -> dict[str, pd.DataFrame]:
        """
        Execute the benchmark for each environment.

        Parameters
        ----------
        environments : dict mapping env_key → base_url.
                       Defaults to ``config.ENVIRONMENTS``.

        Returns
        -------
        dict mapping env_key → raw DataFrame.
        """
        envs = environments or config.ENVIRONMENTS
        auth_token = self._resolve_token()

        for env_key, base_url in envs.items():
            url   = self._build_url(base_url)
            tag   = f"{self.key} / {env_key}"
            print(f"\n── Benchmarking {tag} ({self.n} requests) ──")

            df = run_benchmark(
                url,
                n          = self.n,
                label      = tag,
                headers    = self.headers,
                auth_token = auth_token,
                delay      = self.delay,
            )

            self._results[env_key] = df
            save_raw(df, self.key, env_key)

        return self._results

    def merge(self) -> pd.DataFrame:
        """
        Merge per-environment CSVs into a single processed DataFrame.
        Raw CSVs must exist on disk (i.e. ``run()`` must have been called first).
        """
        return merge_envs(self.key)

    def run_and_merge(self, environments: Optional[dict[str, str]] = None) -> pd.DataFrame:
        """Convenience: ``run()`` followed by ``merge()``."""
        self.run(environments)
        return self.merge()

    # ------------------------------------------------------------------
    # URL construction — subclasses may override
    # ------------------------------------------------------------------

    def _build_url(self, base_url: str) -> str:
        """
        Construct the full URL for a given environment base URL.

        The default implementation appends the ``path`` from the endpoint
        registry.  Subclasses that use full URLs (e.g. benchmark_download)
        can override this method.
        """
        endpoint = config.ENDPOINTS.get(self.key, {})
        path = endpoint.get("path") or "/"
        return base_url.rstrip("/") + path

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _resolve_token(self) -> Optional[str]:
        if not self.auth:
            return None
        from scripts.utils import require_auth_token
        return require_auth_token()

    def __repr__(self) -> str:
        return (
            f"BenchmarkRunner(key={self.key!r}, label={self.label!r}, "
            f"n={self.n}, auth={self.auth})"
        )
