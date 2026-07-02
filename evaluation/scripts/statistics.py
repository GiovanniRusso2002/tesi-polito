"""
Descriptive statistics module.

For every (benchmark, environment, metric) triple, computes:
    mean, median, minimum, maximum, variance, standard deviation,
    p90, p95, p99, and a two-sided 95 % confidence interval for the
    mean (Student t-distribution, appropriate for n = 100 samples).

Public API
----------
    compute_stats(df, metrics)       → DataFrame (one row per env × metric)
    compute_stats_for_benchmark(key) → DataFrame  (loads processed CSV automatically)
    save_stats(stats_df, key)        → writes results/<key>_statistics.csv
    format_latex_table(stats_df)     → LaTeX tabular string (ready to paste)
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config
from scripts.utils import processed_csv_path

# ---------------------------------------------------------------------------
# Core computation
# ---------------------------------------------------------------------------

def compute_stats(
    df: pd.DataFrame,
    metrics: list[str] = config.METRICS,
) -> pd.DataFrame:
    """
    Compute descriptive statistics for every (environment, metric) pair.

    Parameters
    ----------
    df      : DataFrame that **must** contain an ``env`` column and one
              numeric column per metric listed in *metrics*.  Values are
              assumed to be in **seconds**; the output converts to milliseconds.
    metrics : List of column names to analyse.

    Returns
    -------
    DataFrame with columns:
        env, metric, n, mean, median, min, max, variance, std,
        p90, p95, p99, ci_low, ci_high, ci_width
    All timing values are in **milliseconds**.
    """
    rows = []

    for env_key in df["env"].unique():
        env_df = df[df["env"] == env_key]

        for metric in metrics:
            if metric not in env_df.columns:
                continue

            values_s  = env_df[metric].dropna().to_numpy(dtype=float)
            values_ms = values_s * 1_000.0       # seconds → milliseconds
            n = len(values_ms)

            if n < 2:
                continue

            mean    = float(np.mean(values_ms))
            median  = float(np.median(values_ms))
            minimum = float(np.min(values_ms))
            maximum = float(np.max(values_ms))
            var     = float(np.var(values_ms, ddof=1))   # sample variance
            std     = float(np.std(values_ms, ddof=1))   # sample std

            p90 = float(np.percentile(values_ms, 90))
            p95 = float(np.percentile(values_ms, 95))
            p99 = float(np.percentile(values_ms, 99))

            # 95 % confidence interval for the mean (t-distribution).
            # scipy returns (low, high) for the given confidence level.
            ci_low, ci_high = scipy_stats.t.interval(
                config.CONFIDENCE_LEVEL,
                df    = n - 1,
                loc   = mean,
                scale = scipy_stats.sem(values_ms),
            )
            ci_width = ci_high - ci_low

            rows.append({
                "env":      env_key,
                "metric":   metric,
                "n":        n,
                "mean":     mean,
                "median":   median,
                "min":      minimum,
                "max":      maximum,
                "variance": var,
                "std":      std,
                "p90":      p90,
                "p95":      p95,
                "p99":      p99,
                "ci_low":   ci_low,
                "ci_high":  ci_high,
                "ci_width": ci_width,
            })

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------

def compute_stats_for_benchmark(benchmark_key: str) -> pd.DataFrame:
    """
    Load the processed CSV for *benchmark_key* and return the statistics
    DataFrame.  Raises ``FileNotFoundError`` if the processed CSV does not
    exist (run the benchmark + merge first).
    """
    path = processed_csv_path(benchmark_key)
    if not path.exists():
        raise FileNotFoundError(
            f"Processed data not found: {path}\n"
            f"Run: python run.py benchmark --target {benchmark_key}"
        )
    df = pd.read_csv(path)
    return compute_stats(df)


def save_stats(stats_df: pd.DataFrame, benchmark_key: str) -> Path:
    """Write the statistics DataFrame to ``results/<key>_statistics.csv``."""
    path = config.RESULTS_DIR / f"{benchmark_key}_statistics.csv"
    stats_df.to_csv(path, index=False, float_format="%.4f")
    print(f"Statistics saved → {path.relative_to(config.BASE_DIR)}")
    return path


# ---------------------------------------------------------------------------
# LaTeX table generation
# ---------------------------------------------------------------------------

def format_latex_table(
    stats_df: pd.DataFrame,
    benchmark_key: str,
    caption: str = "",
    label: str = "",
) -> str:
    """
    Render a publication-ready LaTeX ``tabular`` environment from a
    statistics DataFrame.

    The table uses the ``booktabs`` package conventions (``\\toprule``,
    ``\\midrule``, ``\\bottomrule``).  Include ``\\usepackage{booktabs}``
    in your LaTeX preamble.

    Parameters
    ----------
    stats_df      : Output of ``compute_stats()`` or ``compute_stats_for_benchmark()``.
    benchmark_key : Used to build the default caption / label when not supplied.
    caption       : LaTeX table caption string.
    label         : LaTeX ``\\label{tab:...}`` identifier.

    Returns
    -------
    str : Full LaTeX ``table`` environment as a string.
    """
    if not caption:
        bk = benchmark_key.replace("_", " ").title()
        caption = (
            f"Descriptive statistics for the {bk} benchmark "
            f"({config.N_REQUESTS} requests per environment). "
            "All timing values in milliseconds (ms). "
            f"CI = {int(config.CONFIDENCE_LEVEL*100)}\\% confidence interval for the mean."
        )
    if not label:
        label = f"tab:stats_{benchmark_key}"

    # Pivot: rows = (metric × env), columns = stat columns
    display_cols = ["mean", "median", "min", "max", "std", "p90", "p95", "p99", "ci_width"]
    col_headers  = [
        r"Mean", r"Median", r"Min", r"Max", r"Std Dev",
        r"P90", r"P95", r"P99", r"CI Width",
    ]
    fmt = "{:.2f}"

    lines = [
        r"\begin{table}[htbp]",
        r"  \centering",
        r"  \caption{" + caption + "}",
        r"  \label{" + label + "}",
        r"  \small",
        r"  \begin{tabular}{llr" + "r" * len(display_cols) + "}",
        r"    \toprule",
        r"    \textbf{Environment} & \textbf{Metric} & \textbf{N} & "
        + " & ".join(r"\textbf{" + h + "}" for h in col_headers)
        + r" \\",
        r"    \midrule",
    ]

    env_order  = list(config.ENVIRONMENTS.keys())
    metric_order = [m for m in config.METRICS if m in stats_df["metric"].values]

    for env_idx, env_key in enumerate(env_order):
        env_rows = stats_df[stats_df["env"] == env_key]
        env_label = config.ENV_LABELS.get(env_key, env_key)

        if env_rows.empty:
            continue

        first_env_row = True
        for metric in metric_order:
            row = env_rows[env_rows["metric"] == metric]
            if row.empty:
                continue

            r = row.iloc[0]
            env_cell    = env_label if first_env_row else ""
            metric_cell = config.METRIC_LABELS.get(metric, metric)
            first_env_row = False

            values = " & ".join(fmt.format(r[c]) for c in display_cols)
            lines.append(
                f"    {env_cell} & {metric_cell} & {int(r['n'])} & {values} \\\\"
            )

        # Separator between environments (except after the last one)
        if env_idx < len(env_order) - 1:
            lines.append(r"    \midrule")

    lines += [
        r"    \bottomrule",
        r"  \end{tabular}",
        r"\end{table}",
    ]

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Pretty-print helper (for terminal inspection)
# ---------------------------------------------------------------------------

def print_summary(stats_df: pd.DataFrame) -> None:
    """Print a human-readable summary to stdout."""
    pd.set_option("display.float_format", "{:.2f}".format)
    pd.set_option("display.max_columns", None)
    pd.set_option("display.width", 120)

    for env_key in stats_df["env"].unique():
        env_label = config.ENV_LABELS.get(env_key, env_key)
        print(f"\n{'─'*60}")
        print(f"  {env_label}")
        print(f"{'─'*60}")
        subset = stats_df[stats_df["env"] == env_key].copy()
        subset["metric"] = subset["metric"].map(
            lambda m: config.METRIC_LABELS.get(m, m)
        )
        subset = subset.set_index("metric")[
            ["n", "mean", "median", "min", "max", "std", "p90", "p95", "p99"]
        ]
        print(subset.to_string())
