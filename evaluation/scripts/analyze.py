"""
Analysis orchestrator.

For a given benchmark key (or all benchmarks), this module:
  1. Loads the processed (merged) CSV from data/processed/
  2. Computes descriptive statistics (statistics.py)
  3. Generates all publication figures (plots.py)
  4. Saves statistics CSV and a LaTeX table to results/

Usage
-----
    python scripts/analyze.py --target home
    python scripts/analyze.py --target all
    python scripts/analyze.py --target home --no-plots
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config
from scripts.statistics import (
    compute_stats_for_benchmark,
    save_stats,
    format_latex_table,
    print_summary,
)
from scripts.plots import generate_all_plots
from scripts.utils import processed_csv_path

import pandas as pd

# ---------------------------------------------------------------------------
# Registry of analysable benchmark keys (those expected to have processed CSVs)
# ---------------------------------------------------------------------------
ANALYSABLE_KEYS: list[str] = [
    "home",
    "api_organizations",
    "api_sites",
    "api_simulations",
    "api_public_simulations",
    "static_js",
    "static_css",
]


def analyze_one(benchmark_key: str, generate_plots: bool = True) -> None:
    """
    Full analysis pipeline for a single benchmark.

    Parameters
    ----------
    benchmark_key : Key from the ANALYSABLE_KEYS registry.
    generate_plots: If False, only statistics are computed and saved.
    """
    proc_path = processed_csv_path(benchmark_key)
    if not proc_path.exists():
        print(
            f"[SKIP] {benchmark_key}: processed CSV not found at "
            f"{proc_path.relative_to(config.BASE_DIR)}. "
            "Run the benchmark first."
        )
        return

    print(f"\n{'='*60}")
    print(f"  Analysing: {benchmark_key}")
    print(f"{'='*60}")

    df       = pd.read_csv(proc_path)
    stats_df = compute_stats_for_benchmark(benchmark_key)

    print_summary(stats_df)
    save_stats(stats_df, benchmark_key)

    # Write LaTeX table to results/
    latex = format_latex_table(stats_df, benchmark_key)
    tex_path = config.RESULTS_DIR / f"{benchmark_key}_table.tex"
    tex_path.write_text(latex)
    print(f"LaTeX table saved → {tex_path.relative_to(config.BASE_DIR)}")

    if generate_plots:
        generate_all_plots(df, stats_df, benchmark_key)


def analyze_all(generate_plots: bool = True) -> None:
    """Run the analysis pipeline for every key that has a processed CSV."""
    ran = 0
    for key in ANALYSABLE_KEYS:
        if processed_csv_path(key).exists():
            analyze_one(key, generate_plots=generate_plots)
            ran += 1

    if ran == 0:
        print(
            "No processed data found. Run benchmarks first:\n"
            "  python run.py benchmark --target all"
        )
    else:
        # Optionally generate a combined CDF figure for all loaded benchmarks
        _try_combined_cdf()


def _try_combined_cdf() -> None:
    """Generate a combined TTFB CDF figure if multiple datasets are available."""
    from scripts.plots import plot_combined_cdf

    datasets = {}
    for key in ANALYSABLE_KEYS:
        path = processed_csv_path(key)
        if path.exists():
            df = pd.read_csv(path)
            if "ttfb" in df.columns:
                datasets[key] = df

    if len(datasets) >= 2:
        print("\n── Generating combined TTFB CDF ──")
        plot_combined_cdf(datasets)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Analyse benchmark data and generate publication figures."
    )
    parser.add_argument(
        "--target",
        choices = ANALYSABLE_KEYS + ["all"],
        default = "all",
        help    = "Which benchmark to analyse (default: all).",
    )
    parser.add_argument(
        "--no-plots",
        action  = "store_true",
        help    = "Skip figure generation; only compute and save statistics.",
    )
    args = parser.parse_args()

    generate_plots = not args.no_plots

    if args.target == "all":
        analyze_all(generate_plots=generate_plots)
    else:
        analyze_one(args.target, generate_plots=generate_plots)

    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()
