"""
REST API endpoint benchmarks.

Benchmarks authenticated (and one public) API endpoints:
  - /api/v1/organizations
  - /api/v1/sites
  - /api/v1/simulations
  - /api/v1/public/simulations

Authentication
--------------
Set the environment variable before running:

    export OUTSIGHT_TOKEN='<your-bearer-token>'

The token is read once at startup.  If it is absent, authenticated
benchmarks are skipped with a clear warning.

Usage
-----
    python scripts/benchmark_api.py
    python scripts/benchmark_api.py --target api_organizations --n 50
    python scripts/benchmark_api.py --skip-auth   # only public endpoints
"""

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config
from scripts.benchmark import BenchmarkRunner
from scripts.utils import get_auth_token

# Ordered list of endpoint keys defined in config.ENDPOINTS that this
# script is responsible for.
API_TARGETS = [
    "api_organizations",
    "api_sites",
    "api_simulations",
    "api_public_simulations",
]


def run_target(key: str, n: int, skip_auth: bool) -> None:
    endpoint = config.ENDPOINTS[key]
    needs_auth = endpoint.get("auth", False)

    if needs_auth and skip_auth:
        print(f"[SKIP] {key} requires authentication (--skip-auth flag set).")
        return

    runner = BenchmarkRunner(
        key     = key,
        label   = endpoint["label"],
        n       = n,
        headers = endpoint.get("headers", {}),
        auth    = needs_auth,
    )

    try:
        runner.run_and_merge()
    except RuntimeError as exc:
        # Token missing — degrade gracefully
        print(f"[SKIP] {key}: {exc}", file=sys.stderr)


def main(targets: list[str], n: int, skip_auth: bool) -> None:
    token = get_auth_token()
    if token:
        print(f"Auth token detected ({config.AUTH_ENV_VAR} is set).")
    else:
        print(
            f"WARNING: {config.AUTH_ENV_VAR} is not set. "
            "Authenticated endpoints will be skipped."
        )

    for key in targets:
        run_target(key, n=n, skip_auth=skip_auth)

    print("\nAPI benchmark complete.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="REST API latency benchmark.")
    parser.add_argument(
        "--target",
        choices = API_TARGETS + ["all"],
        default = "all",
        help    = "Which API endpoint to benchmark (default: all).",
    )
    parser.add_argument(
        "--n",
        type    = int,
        default = config.N_REQUESTS,
        help    = f"Requests per environment (default: {config.N_REQUESTS}).",
    )
    parser.add_argument(
        "--skip-auth",
        action  = "store_true",
        help    = "Skip endpoints that require authentication.",
    )
    args = parser.parse_args()

    selected = API_TARGETS if args.target == "all" else [args.target]
    main(targets=selected, n=args.n, skip_auth=args.skip_auth)
