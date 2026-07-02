"""
Homepage benchmark  –  GET /

Measures DNS, TCP, TLS, TTFB and total request time for 100 independent
requests against both the legacy (DigitalOcean) and the new AWS environment.

Usage
-----
    python scripts/benchmark_home.py
    python scripts/benchmark_home.py --n 200
"""

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config
from scripts.benchmark import BenchmarkRunner


def main(n: int = config.N_REQUESTS) -> None:
    runner = BenchmarkRunner(
        key   = "home",
        label = "Homepage (GET /)",
        n     = n,
        auth  = False,
    )
    runner.run_and_merge()
    print("\nHomepage benchmark complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Homepage latency benchmark.")
    parser.add_argument(
        "--n",
        type    = int,
        default = config.N_REQUESTS,
        help    = f"Number of requests per environment (default: {config.N_REQUESTS})",
    )
    args = parser.parse_args()
    main(n=args.n)
