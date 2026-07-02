"""
Publication-quality figure generation.

All figures target a Master's thesis:
  - 300 dpi export (PDF + PNG)
  - serif fonts, consistent colour palette
  - minimal spines, light grid
  - axis labels and titles in English

Available plot functions
------------------------
    plot_boxplot           – side-by-side box plots per metric, one panel each
    plot_histogram         – overlaid histograms per metric
    plot_cdf               – empirical CDFs per metric
    plot_bar_comparison    – grouped bar chart of means with CI error bars
    plot_scatter_time      – measurements over time (stability check)
    plot_radar             – radar / spider chart across metrics (optional)
    generate_all_plots     – convenience wrapper that calls every function above
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")    # headless backend — safe for server / CI use
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config

# ---------------------------------------------------------------------------
# Apply global rcParams once at import time
# ---------------------------------------------------------------------------
plt.rcParams.update(config.MPL_RC)

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _env_data(df: pd.DataFrame, env_key: str, metric: str) -> np.ndarray:
    """Extract a clean numpy array for one (env, metric) pair (values in ms)."""
    mask   = df["env"] == env_key
    values = df.loc[mask, metric].dropna().to_numpy(dtype=float)
    return values * 1_000.0   # seconds → milliseconds


def _figure_path(benchmark_key: str, plot_type: str) -> Path:
    """Return the output path for a figure file (no extension)."""
    return config.FIGURES_DIR / f"{benchmark_key}_{plot_type}"


def _save_figure(fig: plt.Figure, base_path: Path) -> None:
    """Save as PDF (for LaTeX) and PNG (for quick preview)."""
    pdf_path = base_path.with_suffix(f".{config.FIGURE_FORMAT}")
    png_path = base_path.with_suffix(".png")
    fig.savefig(pdf_path, dpi=config.FIGURE_DPI, bbox_inches="tight")
    fig.savefig(png_path, dpi=150, bbox_inches="tight")
    print(f"  Saved → {pdf_path.relative_to(config.BASE_DIR)}")
    plt.close(fig)


def _env_patches() -> list[mpatches.Patch]:
    """Legend handles for environment colours."""
    return [
        mpatches.Patch(color=config.ENV_COLORS[k], label=config.ENV_LABELS[k])
        for k in config.ENVIRONMENTS
        if k in config.ENV_COLORS
    ]


# ---------------------------------------------------------------------------
# 1. Box plots
# ---------------------------------------------------------------------------

def plot_boxplot(
    df: pd.DataFrame,
    benchmark_key: str,
    metrics: list[str] = config.METRICS,
    title_prefix: str = "",
) -> None:
    """
    Side-by-side box plots comparing Legacy and AWS for every metric.

    One sub-figure per metric, arranged horizontally.  Outliers are shown
    as individual points (fliers).
    """
    n_metrics = len(metrics)
    fig, axes = plt.subplots(
        1, n_metrics,
        figsize = (3.0 * n_metrics, 4.5),
        sharey  = False,
    )
    if n_metrics == 1:
        axes = [axes]

    env_keys = list(config.ENVIRONMENTS.keys())

    for ax, metric in zip(axes, metrics):
        data   = [_env_data(df, ek, metric) for ek in env_keys]
        colors = [config.ENV_COLORS[ek] for ek in env_keys]

        bp = ax.boxplot(
            data,
            patch_artist = True,
            widths        = 0.45,
            medianprops   = {"color": "black", "linewidth": 1.5},
            flierprops    = {"marker": "o", "markersize": 3, "alpha": 0.5},
            whiskerprops  = {"linewidth": 1.0},
            capprops      = {"linewidth": 1.0},
        )
        for patch, color in zip(bp["boxes"], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.75)

        ax.set_xticks([])
        ax.set_xlabel(config.METRIC_LABELS.get(metric, metric), labelpad=4)
        ax.set_ylabel("Latency (ms)" if ax == axes[0] else "")
        ax.yaxis.set_tick_params(labelleft=True)

    label = config.ENDPOINTS.get(benchmark_key, {}).get("label", benchmark_key)
    suptitle = f"{title_prefix}{label} — Latency Distribution" if title_prefix else \
               f"{label} — Latency Distribution"
    fig.suptitle(suptitle, y=1.01, fontsize=12, fontweight="bold")
    fig.legend(handles=_env_patches(), loc="upper center",
               bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
    fig.tight_layout()
    _save_figure(fig, _figure_path(benchmark_key, "boxplot"))


# ---------------------------------------------------------------------------
# 2. Histograms
# ---------------------------------------------------------------------------

def plot_histogram(
    df: pd.DataFrame,
    benchmark_key: str,
    metrics: list[str] = config.METRICS,
    bins: int = 30,
) -> None:
    """
    Overlaid, semi-transparent histograms for each metric.

    One sub-figure per metric.  Vertical dashed lines mark the mean.
    """
    n_metrics = len(metrics)
    fig, axes = plt.subplots(
        1, n_metrics,
        figsize = (3.2 * n_metrics, 4.0),
    )
    if n_metrics == 1:
        axes = [axes]

    env_keys = list(config.ENVIRONMENTS.keys())

    for ax, metric in zip(axes, metrics):
        for env_key in env_keys:
            values = _env_data(df, env_key, metric)
            color  = config.ENV_COLORS[env_key]
            ax.hist(
                values,
                bins      = bins,
                color     = color,
                alpha     = 0.55,
                edgecolor = "none",
                density   = True,
                label     = config.ENV_LABELS[env_key],
            )
            ax.axvline(
                np.mean(values),
                color     = color,
                linestyle = "--",
                linewidth = 1.2,
                alpha     = 0.9,
            )

        ax.set_xlabel("Latency (ms)")
        ax.set_ylabel("Density" if ax == axes[0] else "")
        ax.set_title(config.METRIC_LABELS.get(metric, metric), fontsize=10)

    label = config.ENDPOINTS.get(benchmark_key, {}).get("label", benchmark_key)
    fig.suptitle(f"{label} — Latency Histograms", y=1.01,
                 fontsize=12, fontweight="bold")
    fig.legend(handles=_env_patches(), loc="upper center",
               bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
    fig.tight_layout()
    _save_figure(fig, _figure_path(benchmark_key, "histogram"))


# ---------------------------------------------------------------------------
# 3. Empirical CDF
# ---------------------------------------------------------------------------

def plot_cdf(
    df: pd.DataFrame,
    benchmark_key: str,
    metrics: list[str] = config.METRICS,
) -> None:
    """
    Empirical Cumulative Distribution Functions (ECDF).

    One sub-figure per metric.  Horizontal dashed lines at p90 / p95 / p99
    help locate the tail quantiles directly on the plot.
    """
    n_metrics = len(metrics)
    fig, axes = plt.subplots(
        1, n_metrics,
        figsize = (3.2 * n_metrics, 4.0),
        sharey  = True,
    )
    if n_metrics == 1:
        axes = [axes]

    env_keys = list(config.ENVIRONMENTS.keys())

    for ax, metric in zip(axes, metrics):
        for env_key in env_keys:
            values = np.sort(_env_data(df, env_key, metric))
            n      = len(values)
            cdf    = np.arange(1, n + 1) / n
            ax.plot(
                values, cdf,
                color     = config.ENV_COLORS[env_key],
                linewidth = 1.6,
                label     = config.ENV_LABELS[env_key],
            )

        for p, ls in [(0.90, ":"), (0.95, "--"), (0.99, "-.")]:
            ax.axhline(p, color="grey", linewidth=0.8, linestyle=ls, alpha=0.6)
            ax.text(
                ax.get_xlim()[1] if ax.get_xlim()[1] != 0 else 1,
                p + 0.005,
                f"p{int(p*100)}",
                fontsize=7, color="grey", va="bottom", ha="right",
            )

        ax.set_xlabel("Latency (ms)")
        ax.set_ylabel("Cumulative probability" if ax == axes[0] else "")
        ax.set_ylim(0, 1.05)
        ax.set_title(config.METRIC_LABELS.get(metric, metric), fontsize=10)

    label = config.ENDPOINTS.get(benchmark_key, {}).get("label", benchmark_key)
    fig.suptitle(f"{label} — Empirical CDF", y=1.01, fontsize=12, fontweight="bold")
    fig.legend(handles=_env_patches(), loc="upper center",
               bbox_to_anchor=(0.5, 1.0), ncol=2, frameon=False)
    fig.tight_layout()
    _save_figure(fig, _figure_path(benchmark_key, "cdf"))


# ---------------------------------------------------------------------------
# 4. Bar chart — mean comparison with CI error bars
# ---------------------------------------------------------------------------

def plot_bar_comparison(
    df: pd.DataFrame,
    stats_df: pd.DataFrame,
    benchmark_key: str,
    metrics: list[str] = config.METRICS,
) -> None:
    """
    Grouped bar chart of mean latencies for each metric, with 95 % CI bars.

    The percent improvement (Legacy → AWS) is annotated above each group
    when the AWS mean is lower than the legacy mean.
    """
    env_keys  = list(config.ENVIRONMENTS.keys())
    n_metrics = len(metrics)
    n_envs    = len(env_keys)
    width     = 0.35
    x         = np.arange(n_metrics)

    fig, ax = plt.subplots(figsize=(max(6, 1.8 * n_metrics), 4.5))

    for i, env_key in enumerate(env_keys):
        env_stats = stats_df[stats_df["env"] == env_key]
        means, ci_halfs = [], []

        for metric in metrics:
            row = env_stats[env_stats["metric"] == metric]
            if row.empty:
                means.append(0.0)
                ci_halfs.append(0.0)
            else:
                r = row.iloc[0]
                means.append(r["mean"])
                ci_halfs.append(r["ci_width"] / 2.0)

        offset = (i - (n_envs - 1) / 2) * width
        bars = ax.bar(
            x + offset,
            means,
            width     = width,
            color     = config.ENV_COLORS[env_key],
            alpha     = 0.85,
            label     = config.ENV_LABELS[env_key],
            yerr      = ci_halfs,
            capsize   = 3,
            error_kw  = {"linewidth": 1.0, "ecolor": "black", "alpha": 0.7},
        )

    # Annotate % improvement for each metric
    for j, metric in enumerate(metrics):
        env_means = {}
        for env_key in env_keys:
            row = stats_df[(stats_df["env"] == env_key) & (stats_df["metric"] == metric)]
            if not row.empty:
                env_means[env_key] = row.iloc[0]["mean"]

        if "legacy" in env_means and "aws" in env_means:
            legacy_m = env_means["legacy"]
            aws_m    = env_means["aws"]
            if legacy_m > 0 and aws_m < legacy_m:
                improvement = (legacy_m - aws_m) / legacy_m * 100
                top_y = max(env_means.values())
                ax.text(
                    j, top_y * 1.08,
                    f"−{improvement:.1f}%",
                    ha="center", va="bottom", fontsize=8,
                    color="#2ca02c", fontweight="bold",
                )

    metric_labels = [config.METRIC_LABELS.get(m, m) for m in metrics]
    ax.set_xticks(x)
    ax.set_xticklabels(metric_labels, rotation=15, ha="right")
    ax.set_ylabel("Mean Latency (ms)")
    label = config.ENDPOINTS.get(benchmark_key, {}).get("label", benchmark_key)
    ax.set_title(f"{label} — Mean Latency Comparison (95 % CI)")
    ax.legend(frameon=False)
    fig.tight_layout()
    _save_figure(fig, _figure_path(benchmark_key, "bar_comparison"))


# ---------------------------------------------------------------------------
# 5. Scatter plot over time (stability / drift check)
# ---------------------------------------------------------------------------

def plot_scatter_time(
    df: pd.DataFrame,
    benchmark_key: str,
    metric: str = "ttfb",
) -> None:
    """
    Scatter plot of latency values in collection order.

    Useful for detecting temporal drift, warm-up effects, or outlier
    bursts across the N_REQUESTS measurements.
    """
    env_keys = list(config.ENVIRONMENTS.keys())
    fig, axes = plt.subplots(
        1, len(env_keys),
        figsize = (5.5 * len(env_keys), 3.8),
        sharey  = True,
    )
    if len(env_keys) == 1:
        axes = [axes]

    for ax, env_key in zip(axes, env_keys):
        sub    = df[df["env"] == env_key].reset_index(drop=True)
        values = sub[metric].to_numpy(dtype=float) * 1_000.0
        runs   = sub["run"].to_numpy() if "run" in sub.columns else np.arange(1, len(values) + 1)

        color = config.ENV_COLORS[env_key]
        ax.scatter(runs, values, color=color, s=18, alpha=0.6, linewidths=0)
        ax.axhline(np.mean(values), color=color, linewidth=1.2,
                   linestyle="--", label=f"Mean = {np.mean(values):.1f} ms")
        ax.set_xlabel("Request index")
        ax.set_ylabel("Latency (ms)" if ax == axes[0] else "")
        ax.set_title(config.ENV_LABELS.get(env_key, env_key))
        ax.legend(fontsize=9, frameon=False)

    metric_label = config.METRIC_LABELS.get(metric, metric)
    bench_label  = config.ENDPOINTS.get(benchmark_key, {}).get("label", benchmark_key)
    fig.suptitle(f"{bench_label} — {metric_label} over time",
                 y=1.01, fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save_figure(fig, _figure_path(benchmark_key, f"scatter_{metric}"))


# ---------------------------------------------------------------------------
# 6. Radar / spider chart
# ---------------------------------------------------------------------------

def plot_radar(
    stats_df: pd.DataFrame,
    benchmark_key: str,
    metrics: list[str] = config.METRICS,
    stat: str = "mean",
) -> None:
    """
    Radar chart comparing environments across multiple metrics simultaneously.

    Values are normalised to [0, 1] so that all metrics share the same scale.
    Closer to the centre = better (lower latency).

    Parameters
    ----------
    stat : Which statistic to plot (default: ``"mean"``).
    """
    env_keys     = list(config.ENVIRONMENTS.keys())
    metric_labels = [config.METRIC_LABELS.get(m, m) for m in metrics]
    n = len(metrics)

    angles = np.linspace(0, 2 * np.pi, n, endpoint=False).tolist()
    angles += angles[:1]   # close the polygon

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw={"polar": True})

    # Collect raw values for normalisation
    all_values: dict[str, list[float]] = {}
    for env_key in env_keys:
        env_stats = stats_df[stats_df["env"] == env_key]
        vals = []
        for metric in metrics:
            row = env_stats[env_stats["metric"] == metric]
            vals.append(row.iloc[0][stat] if not row.empty else 0.0)
        all_values[env_key] = vals

    # Normalise across environments for each metric
    combined = np.array(list(all_values.values()))   # shape (n_envs, n_metrics)
    col_max  = combined.max(axis=0)
    col_max[col_max == 0] = 1.0

    for env_key in env_keys:
        normed = [v / col_max[i] for i, v in enumerate(all_values[env_key])]
        normed += normed[:1]

        ax.plot(angles, normed,
                color=config.ENV_COLORS[env_key], linewidth=1.8,
                label=config.ENV_LABELS[env_key])
        ax.fill(angles, normed,
                color=config.ENV_COLORS[env_key], alpha=0.12)

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(metric_labels, size=9)
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0.25, 0.5, 0.75, 1.0])
    ax.set_yticklabels(["25%", "50%", "75%", "100%"], size=7, color="grey")

    bench_label = config.ENDPOINTS.get(benchmark_key, {}).get("label", benchmark_key)
    stat_label  = stat.capitalize()
    ax.set_title(
        f"{bench_label} — {stat_label} Latency Radar\n"
        "(normalised; closer to centre = lower latency)",
        pad=15, fontsize=10,
    )
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.15), frameon=False, fontsize=9)
    fig.tight_layout()
    _save_figure(fig, _figure_path(benchmark_key, "radar"))


# ---------------------------------------------------------------------------
# 7. Compound figure — TTFB CDF for all benchmarks on one canvas
# ---------------------------------------------------------------------------

def plot_combined_cdf(
    datasets: dict[str, pd.DataFrame],
    output_name: str = "combined_ttfb_cdf",
) -> None:
    """
    Overlay TTFB ECDFs for multiple benchmarks on a single figure (two panels:
    one per environment).

    Parameters
    ----------
    datasets : dict mapping benchmark_key → merged DataFrame.
    """
    env_keys = list(config.ENVIRONMENTS.keys())
    fig, axes = plt.subplots(1, len(env_keys), figsize=(5.5 * len(env_keys), 4.5), sharey=True)
    if len(env_keys) == 1:
        axes = [axes]

    cmap   = plt.cm.tab10
    bkeys  = list(datasets.keys())
    colors = {bk: cmap(i / max(len(bkeys) - 1, 1)) for i, bk in enumerate(bkeys)}

    for ax, env_key in zip(axes, env_keys):
        for bk, df in datasets.items():
            values = np.sort(_env_data(df, env_key, "ttfb"))
            n      = len(values)
            if n == 0:
                continue
            cdf  = np.arange(1, n + 1) / n
            lbl  = config.ENDPOINTS.get(bk, {}).get("label", bk)
            ax.plot(values, cdf, linewidth=1.5, color=colors[bk], label=lbl)

        ax.set_xlabel("TTFB (ms)")
        ax.set_ylabel("Cumulative probability" if ax == axes[0] else "")
        ax.set_ylim(0, 1.05)
        ax.set_title(config.ENV_LABELS.get(env_key, env_key))
        ax.legend(fontsize=8, frameon=False)

    fig.suptitle("TTFB ECDF — All Benchmarks", y=1.01, fontsize=12, fontweight="bold")
    fig.tight_layout()
    _save_figure(fig, config.FIGURES_DIR / output_name)


# ---------------------------------------------------------------------------
# Convenience: generate all standard plots for one benchmark
# ---------------------------------------------------------------------------

def generate_all_plots(
    df: pd.DataFrame,
    stats_df: pd.DataFrame,
    benchmark_key: str,
    metrics: list[str] = config.METRICS,
) -> None:
    """
    Generate the full suite of figures for a single benchmark:
      boxplot, histogram, CDF, bar comparison, scatter (TTFB), radar.
    """
    print(f"\n── Generating figures for [{benchmark_key}] ──")

    plot_boxplot(df, benchmark_key, metrics)
    plot_histogram(df, benchmark_key, metrics)
    plot_cdf(df, benchmark_key, metrics)
    plot_bar_comparison(df, stats_df, benchmark_key, metrics)
    plot_scatter_time(df, benchmark_key, metric="ttfb")
    plot_scatter_time(df, benchmark_key, metric="total")
    plot_radar(stats_df, benchmark_key, metrics)
