"""
Static-asset / file-download benchmarks.

Unlike the other benchmark scripts, static assets typically have environment-
specific full URLs (different CDN origins, bucket paths, etc.).  Each asset
is therefore registered with explicit URLs per environment rather than a
single relative path.

To add a new asset, extend the ``ASSETS`` list below.

Usage
-----
    python scripts/benchmark_download.py
    python scripts/benchmark_download.py --n 50
    python scripts/benchmark_download.py --target static_js
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config
from scripts.utils import run_benchmark, save_raw, merge_envs

# ---------------------------------------------------------------------------
# Asset registry
#
# Each entry maps a benchmark key to the exact URL for each environment.
# Set a URL to None to skip that environment for a particular asset.
#
# HOW TO DISCOVER ASSET URLS
# ---------------------------
# 1. Open the browser DevTools → Network tab.
# 2. Hard-reload the application page.
# 3. Filter by "JS" or "CSS" to find the hashed bundle filenames.
# 4. Copy the full URL and paste it below for the corresponding environment.
# ---------------------------------------------------------------------------
ASSETS: list[dict] = [
    {
        "key":   "static_js",
        "label": "JS Bundle",
        "urls": {
            # Replace these placeholder URLs with the actual hashed bundle URLs.
            # Example: "legacy": "https://legacy.cloud.outsight.ai/assets/index-Abc123.js"
            "legacy": None,
            "aws":    None,
        },
    },
    {
        "key":   "static_css",
        "label": "CSS Bundle",
        "urls": {
            "legacy": None,
            "aws":    None,
        },
    },
]


class AssetBenchmarkRunner:
    """
    Benchmark a static asset using per-environment full URLs.

    Unlike ``BenchmarkRunner``, this class does not consult the endpoint
    registry for path construction — URLs are fully specified in ``ASSETS``.
    """

    def __init__(self, asset: dict, n: int = config.N_REQUESTS) -> None:
        self.asset = asset
        self.n     = n

    def run_and_merge(self) -> None:
        key   = self.asset["key"]
        label = self.asset["label"]
        urls  = self.asset["urls"]

        any_ran = False

        for env_key, url in urls.items():
            if not url:
                print(f"[SKIP] {key} / {env_key}: URL not configured.")
                continue

            tag = f"{key} / {env_key}"
            print(f"\n── Benchmarking {tag} ({self.n} requests) ──")

            df = run_benchmark(url, n=self.n, label=tag)
            save_raw(df, key, env_key)
            any_ran = True

        if any_ran:
            # Only merge if at least one environment produced data.
            try:
                merge_envs(key)
            except FileNotFoundError as exc:
                print(f"WARNING: could not merge {key}: {exc}", file=sys.stderr)


def main(targets: list[str], n: int) -> None:
    assets = [a for a in ASSETS if a["key"] in targets]

    if not assets:
        print("No assets to benchmark. Check the --target flag or configure ASSETS.")
        return

    for asset in assets:
        runner = AssetBenchmarkRunner(asset, n=n)
        runner.run_and_merge()

    print("\nDownload benchmark complete.")


if __name__ == "__main__":
    all_keys = [a["key"] for a in ASSETS]

    parser = argparse.ArgumentParser(description="Static-asset download latency benchmark.")
    parser.add_argument(
        "--target",
        choices = all_keys + ["all"],
        default = "all",
        help    = "Which asset to benchmark (default: all).",
    )
    parser.add_argument(
        "--n",
        type    = int,
        default = config.N_REQUESTS,
        help    = f"Requests per environment (default: {config.N_REQUESTS}).",
    )
    args = parser.parse_args()

    selected = all_keys if args.target == "all" else [args.target]
    main(targets=selected, n=args.n)
