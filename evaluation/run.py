#!/usr/bin/env python3
"""
Outsight Cloud Evaluation Framework — Main entry point.

This script orchestrates benchmarking and analysis in a reproducible pipeline.

Sub-commands
------------
benchmark   Run HTTP latency benchmarks against both environments.
analyze     Compute statistics and generate publication figures.
all         Run benchmark → merge → analyze in sequence.

Examples
--------
    # Full pipeline for the homepage
    python run.py all --target home

    # Full pipeline for everything
    python run.py all

    # Benchmark only (no analysis)
    python run.py benchmark --target home --n 200

    # Analysis only (data must already exist)
    python run.py analyze --target home

    # Analysis without regenerating figures
    python run.py analyze --target all --no-plots

    # Authenticated API benchmark
    export OUTSIGHT_TOKEN='<bearer-token>'
    python run.py benchmark --target api_organizations
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure the project root is in sys.path so all imports resolve correctly.
_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config   # noqa: E402  (must come after path manipulation)

# ---------------------------------------------------------------------------
# Benchmark target registry
#
# Maps target keys to the callable that runs that benchmark.  The callable
# receives a single ``n`` (int) keyword argument.
# ---------------------------------------------------------------------------

def _get_benchmark_registry() -> dict[str, callable]:
    """Lazily import benchmark modules to avoid circular imports."""
    from scripts.benchmark_home     import main as home_main
    from scripts.benchmark_api      import main as api_main
    from scripts.benchmark_download import main as download_main

    return {
        "home": lambda n: home_main(n=n),
        "api_organizations":      lambda n: api_main(
            targets=["api_organizations"], n=n, skip_auth=False,
        ),
        "api_sites":              lambda n: api_main(
            targets=["api_sites"], n=n, skip_auth=False,
        ),
        "api_simulations":        lambda n: api_main(
            targets=["api_simulations"], n=n, skip_auth=False,
        ),
        "api_public_simulations": lambda n: api_main(
            targets=["api_public_simulations"], n=n, skip_auth=False,
        ),
        "api":                    lambda n: api_main(
            targets=[
                "api_organizations",
                "api_sites",
                "api_simulations",
                "api_public_simulations",
            ],
            n=n, skip_auth=False,
        ),
        "static_js":  lambda n: download_main(targets=["static_js"],  n=n),
        "static_css": lambda n: download_main(targets=["static_css"], n=n),
        "download":   lambda n: download_main(
            targets=["static_js", "static_css"], n=n,
        ),
    }


ALL_BENCHMARK_TARGETS = [
    "home",
    "api_organizations",
    "api_sites",
    "api_simulations",
    "api_public_simulations",
    "static_js",
    "static_css",
]

ALL_ANALYSIS_TARGETS = [
    "home",
    "api_organizations",
    "api_sites",
    "api_simulations",
    "api_public_simulations",
    "static_js",
    "static_css",
]

BENCHMARK_CHOICES = sorted(set(ALL_BENCHMARK_TARGETS) | {"api", "download", "all"})
ANALYZE_CHOICES   = ALL_ANALYSIS_TARGETS + ["all"]


# ---------------------------------------------------------------------------
# Sub-command handlers
# ---------------------------------------------------------------------------

def cmd_benchmark(args: argparse.Namespace) -> None:
    registry = _get_benchmark_registry()
    n        = args.n

    if args.target == "all":
        targets = ALL_BENCHMARK_TARGETS
    else:
        targets = [args.target]

    for target in targets:
        if target not in registry:
            print(f"Unknown benchmark target: {target!r}", file=sys.stderr)
            sys.exit(1)
        print(f"\n{'#'*60}")
        print(f"#  BENCHMARK: {target}  (n={n})")
        print(f"{'#'*60}")
        registry[target](n)


def cmd_analyze(args: argparse.Namespace) -> None:
    from scripts.analyze import analyze_one, analyze_all

    generate_plots = not args.no_plots

    if args.target == "all":
        analyze_all(generate_plots=generate_plots)
    else:
        analyze_one(args.target, generate_plots=generate_plots)


def cmd_all(args: argparse.Namespace) -> None:
    """Run benchmark then analyze for the specified target(s)."""
    # Run benchmarks first
    cmd_benchmark(args)

    # Then analyze
    analyze_args         = argparse.Namespace(**vars(args))
    analyze_args.no_plots = getattr(args, "no_plots", False)

    # When --target=all was used for benchmark, also analyze all
    if args.target == "all":
        analyze_args.target = "all"

    cmd_analyze(analyze_args)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog        = "run.py",
        description = "Outsight Cloud Evaluation Framework.",
        formatter_class = argparse.RawDescriptionHelpFormatter,
        epilog      = __doc__,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # ── benchmark ────────────────────────────────────────────────────────
    bp = subparsers.add_parser("benchmark", help="Run HTTP latency benchmarks.")
    bp.add_argument(
        "--target",
        choices = BENCHMARK_CHOICES,
        default = "all",
        help    = "Which benchmark to run (default: all).",
    )
    bp.add_argument(
        "--n",
        type    = int,
        default = config.N_REQUESTS,
        help    = f"Requests per environment (default: {config.N_REQUESTS}).",
    )

    # ── analyze ──────────────────────────────────────────────────────────
    ap = subparsers.add_parser(
        "analyze",
        help="Compute statistics and generate figures from collected data.",
    )
    ap.add_argument(
        "--target",
        choices = ANALYZE_CHOICES,
        default = "all",
        help    = "Which benchmark to analyse (default: all).",
    )
    ap.add_argument(
        "--no-plots",
        action  = "store_true",
        help    = "Skip figure generation; only output statistics.",
    )

    # ── all ──────────────────────────────────────────────────────────────
    fp = subparsers.add_parser("all", help="Run benchmark → analyze in sequence.")
    fp.add_argument(
        "--target",
        choices = BENCHMARK_CHOICES,
        default = "all",
        help    = "Which benchmark to run and analyse (default: all).",
    )
    fp.add_argument(
        "--n",
        type    = int,
        default = config.N_REQUESTS,
        help    = f"Requests per environment (default: {config.N_REQUESTS}).",
    )
    fp.add_argument(
        "--no-plots",
        action  = "store_true",
        help    = "Skip figure generation during analysis.",
    )

    return parser


def main() -> None:
    parser = build_parser()
    args   = parser.parse_args()

    dispatch = {
        "benchmark": cmd_benchmark,
        "analyze":   cmd_analyze,
        "all":       cmd_all,
    }

    dispatch[args.command](args)


if __name__ == "__main__":
    main()
