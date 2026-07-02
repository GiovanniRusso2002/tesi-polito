"""
Cost analysis for the Outsight Cloud migration (Chapter 7.2).

Reads:
    data/legacy_costs.json
    data/aws_costs_current.json       – steady-state estimate from July 2 run rate
    data/aws_costs_monthly_trend.json – migration period trend (Apr-Jun 2026)

Produces in results/:
    cost_comparison_table.tex   – Legacy vs AWS service-level cost table
    cost_summary_table.tex      – High-level cost summary

Produces in figures/:
    cost_bar_comparison.pdf/png – Side-by-side category comparison bar chart
    cost_aws_breakdown.pdf/png  – AWS cost breakdown by service (horizontal bar)
    cost_migration_trend.pdf/png– Monthly AWS spend during migration
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config

plt.rcParams.update(config.MPL_RC)

RESULTS = config.RESULTS_DIR
FIGURES = config.FIGURES_DIR
DATA    = _ROOT / "data"
USD_EUR = 0.92   # spot rate July 2026

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

with open(DATA / "legacy_costs.json") as f:
    legacy = json.load(f)

with open(DATA / "aws_costs_current.json") as f:
    current = json.load(f)

with open(DATA / "aws_costs_monthly_trend.json") as f:
    trend = json.load(f)


def eur(usd: float) -> float:
    return round(usd * USD_EUR, 1)


# Key monthly figures from the current steady-state estimate
AWS_MONTHLY_EUR  = current["monthly_estimate_eur_excl_tax"]   # ~229.8
AWS_MONTHLY_USD  = current["monthly_estimate_usd_excl_tax"]   # ~249.83
LEGACY_EUR       = 172.0

# Per-service monthly breakdown (daily × 30 + fixed monthly)
DAILY  = current["daily_recurring"]
FIXED  = current["monthly_fixed"]

def monthly_eur(svc_key: str) -> float:
    daily_usd = DAILY.get(svc_key, 0.0) * 30
    return eur(daily_usd)

ECS_EUR   = eur(DAILY["Amazon Elastic Container Service"]   * 30)
ELB_EUR   = eur(DAILY["Amazon Elastic Load Balancing"]      * 30)
RDS_EUR   = eur(DAILY["Amazon Relational Database Service"] * 30)
VPC_EUR   = eur(DAILY["Amazon Virtual Private Cloud"]       * 30)
CFG_EUR   = eur(DAILY["AWS Config"]                         * 30)
CW_EUR    = 0.0   # CloudWatch not in daily (absorbed in config/metrics billing)
SM_EUR    = eur(DAILY["AWS Secrets Manager"]                * 30)
GD_EUR    = eur(DAILY["Amazon GuardDuty"]                   * 30)
EC2_EUR   = eur((DAILY["Amazon Elastic Compute Cloud"] +
                 DAILY["EC2 - Other"])                      * 30)
S3_EUR    = eur(FIXED["Amazon Simple Storage Service (storage)"] +
                DAILY["Amazon Simple Storage Service"] * 30)
R53_EUR   = eur(FIXED["Amazon Route 53 (hosted zones)"])


# ---------------------------------------------------------------------------
# 1. Bar chart: category-level comparison Legacy vs AWS
# ---------------------------------------------------------------------------

LEGACY_CATS = {
    "Storage":       70.0,
    "Compute":      102.0,
    "Database/SaaS": 294.0,
    "Networking":     0.0,
    "Security":       0.0,
    "Governance":     0.0,
}

AWS_CATS = {
    "Storage":       S3_EUR,
    "Compute":       ECS_EUR + EC2_EUR,
    "Database/SaaS": RDS_EUR,
    "Networking":    VPC_EUR + R53_EUR + ELB_EUR,
    "Security":      GD_EUR + SM_EUR,
    "Governance":    CFG_EUR,
}

DISPLAY_CATS = ["Storage", "Compute", "Database/SaaS", "Networking",
                "Security", "Governance"]

legacy_vals = [LEGACY_CATS.get(c, 0.0) for c in DISPLAY_CATS]
aws_vals    = [AWS_CATS.get(c, 0.0)    for c in DISPLAY_CATS]

x     = np.arange(len(DISPLAY_CATS))
width = 0.35

fig, ax = plt.subplots(figsize=(10, 5))
bars_l = ax.bar(x - width/2, legacy_vals, width,
                label="Legacy (DigitalOcean)", color="#d62728", alpha=0.82)
bars_a = ax.bar(x + width/2, aws_vals, width,
                label="AWS (ECS Fargate)", color="#1f77b4", alpha=0.82)

ax.set_xticks(x)
ax.set_xticklabels(DISPLAY_CATS, rotation=15, ha="right")
ax.set_ylabel("Monthly Cost (EUR)")
ax.set_title("Monthly Cost by Category: Legacy vs. AWS")
ax.legend(frameon=False)

for bar in bars_l:
    if bar.get_height() > 0:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"EUR{bar.get_height():.0f}", ha="center", va="bottom", fontsize=8)
for bar in bars_a:
    if bar.get_height() > 0:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1,
                f"EUR{bar.get_height():.0f}", ha="center", va="bottom", fontsize=8)

fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(FIGURES / f"cost_bar_comparison.{ext}",
                dpi=config.FIGURE_DPI if ext == "pdf" else 150,
                bbox_inches="tight")
plt.close(fig)
print("  Saved -> figures/cost_bar_comparison")


# ---------------------------------------------------------------------------
# 2. Horizontal bar: AWS service breakdown (monthly estimate, EUR)
# ---------------------------------------------------------------------------

items = [
    ("ECS Fargate",           ECS_EUR),
    ("Elastic LB (ALB)",      ELB_EUR),
    ("RDS (PostgreSQL)",      RDS_EUR),
    ("VPC / NAT Gateway",     VPC_EUR),
    ("AWS Config",            CFG_EUR),
    ("S3 (storage + usage)",  S3_EUR),
    ("Route 53",              R53_EUR),
    ("Secrets Manager",       SM_EUR),
    ("GuardDuty",             GD_EUR),
    ("EC2 (residual)",        EC2_EUR),
]
items = [(lbl, val) for lbl, val in items if val >= 0.1]
items.sort(key=lambda x: x[1])

labels = [i[0] for i in items]
values = [i[1] for i in items]

fig, ax = plt.subplots(figsize=(8, 5))
colors = plt.cm.Blues(np.linspace(0.4, 0.85, len(labels)))
bars = ax.barh(labels, values, color=colors, edgecolor="white", linewidth=0.4)

for bar, val in zip(bars, values):
    ax.text(val + 0.3, bar.get_y() + bar.get_height()/2,
            f"EUR{val:.1f}", va="center", fontsize=8)

ax.set_xlabel("Monthly Cost (EUR)")
ax.set_title("Estimated Steady-State AWS Cost by Service")
ax.set_xlim(0, max(values) * 1.22)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(FIGURES / f"cost_aws_breakdown.{ext}",
                dpi=config.FIGURE_DPI if ext == "pdf" else 150,
                bbox_inches="tight")
plt.close(fig)
print("  Saved -> figures/cost_aws_breakdown")


# ---------------------------------------------------------------------------
# 3. Migration trend + steady-state reference line
# ---------------------------------------------------------------------------

months_eur  = [eur(m["total_excl_tax_usd"]) for m in trend["months"]]
labels_x    = ["Apr 2026", "May 2026", "Jun 2026"]
steady_eur  = round(AWS_MONTHLY_EUR, 0)

fig, ax = plt.subplots(figsize=(7, 4))
ax.plot(labels_x, months_eur, marker="o", color="#1f77b4", linewidth=2,
        markersize=7, label="AWS spend during migration")
ax.axhline(steady_eur, color="#1f77b4", linestyle="--", linewidth=1.2,
           alpha=0.7, label=f"Estimated steady state (EUR{steady_eur:.0f})")
ax.axhline(LEGACY_EUR, color="#d62728", linestyle="--", linewidth=1.2,
           alpha=0.8, label=f"Legacy baseline (EUR{LEGACY_EUR:.0f})")

for lbl, val in zip(labels_x, months_eur):
    ax.annotate(f"EUR{val:.0f}", (lbl, val),
                textcoords="offset points", xytext=(0, 10),
                ha="center", fontsize=9)

ax.set_ylabel("Monthly Cost (EUR, excl. VAT)")
ax.set_title("AWS Monthly Spend During Migration and Steady-State Estimate")
ax.legend(frameon=False, fontsize=9)
ax.set_ylim(0, max(months_eur) * 1.2)
fig.tight_layout()
for ext in ("pdf", "png"):
    fig.savefig(FIGURES / f"cost_migration_trend.{ext}",
                dpi=config.FIGURE_DPI if ext == "pdf" else 150,
                bbox_inches="tight")
plt.close(fig)
print("  Saved -> figures/cost_migration_trend")


# ---------------------------------------------------------------------------
# 4. LaTeX cost comparison table
# ---------------------------------------------------------------------------

AIRTABLE_EUR = 294.0   # legacy SaaS cost (7 editor licences)

comparison_rows = [
    ("Storage",       "DigitalOcean Spaces",  70,    "Amazon S3",               S3_EUR),
    ("Compute",       "DigitalOcean Droplets", 102,  "ECS Fargate",             ECS_EUR),
    ("Database / SaaS", "Airtable (7 editors)", AIRTABLE_EUR, "Amazon RDS",    RDS_EUR),
    ("Load Balancer", r"\textendash{}",        0,    "Elastic LB (ALB)",        ELB_EUR),
    ("Networking",    r"\textendash{}",        0,    "VPC + Route 53",          VPC_EUR + R53_EUR),
    ("Security",      r"\textendash{}",        0,    "GuardDuty + Secrets Mgr", GD_EUR + SM_EUR),
    ("Governance",    r"\textendash{}",        0,    "AWS Config",              CFG_EUR),
]

total_legacy = sum(r[2] for r in comparison_rows)
total_aws    = sum(r[4] for r in comparison_rows)

lines = [
    r"\begin{table}[htbp]",
    r"  \centering",
    r"  \caption{Monthly cost comparison between the Legacy and AWS platforms.}",
    r"  \label{tab:cost_comparison}",
    r"  \footnotesize",
    r"  \resizebox{\textwidth}{!}{%",
    r"  \begin{tabular}{lp{3cm}rp{3.5cm}r}",
    r"    \toprule",
    r"    \textbf{Category} & \textbf{Legacy} & \textbf{EUR/mo} & \textbf{AWS} & \textbf{EUR/mo} \\",
    r"    \midrule",
]
for cat, leg_svc, leg_cost, aws_svc, aws_cost in comparison_rows:
    leg_str = f"{leg_cost:.0f}" if leg_cost > 0 else r"\textendash{}"
    lines.append(f"    {cat} & {leg_svc} & {leg_str} & {aws_svc} & {aws_cost:.1f} \\\\")

lines += [
    r"    \midrule",
    f"    \\textbf{{Total}} & & \\textbf{{{total_legacy:.0f}}} & & \\textbf{{{total_aws:.1f}}} \\\\",
    r"    \bottomrule",
    r"  \end{tabular}%",
    r"  }",
    r"\end{table}",
]
(RESULTS / "cost_comparison_table.tex").write_text("\n".join(lines))
print("  Saved -> results/cost_comparison_table.tex")


# ---------------------------------------------------------------------------
# 5. High-level summary table
# ---------------------------------------------------------------------------

aws_incl = round(AWS_MONTHLY_EUR / 0.92 * 1.20 * 0.92, 0)  # incl. 20% VAT back to EUR

summary_rows = [
    ("Legacy (infra + Airtable)",
     f"{LEGACY_EUR + AIRTABLE_EUR:.0f}",
     "DigitalOcean Spaces, Droplets + Airtable 7-editor licence"),
    ("AWS (excl.\\ VAT)",
     f"{total_aws:.0f}",
     "ECS, RDS, ALB, VPC, S3, GuardDuty, Config, Secrets Mgr"),
    ("AWS (incl.\\ VAT)",
     f"{aws_incl:.0f}",
     "Including French TVA (20\\%) applied to eu-west-3"),
    ("Monthly saving (Legacy $-$ AWS, excl.\\ VAT)",
     f"{LEGACY_EUR + AIRTABLE_EUR - total_aws:.0f}",
     "Positive = AWS is cheaper"),
]

summary_lines = [
    r"\begin{table}[htbp]",
    r"  \centering",
    r"  \caption{High-level monthly cost summary including Airtable.",
    r"    AWS figures are steady-state estimates from the July\,2026 daily run rate.}",
    r"  \label{tab:cost_summary}",
    r"  \small",
    r"  \resizebox{\textwidth}{!}{%",
    r"  \begin{tabular}{lrp{8cm}}",
    r"    \toprule",
    r"    \textbf{Scenario} & \textbf{EUR/month} & \textbf{Notes} \\",
    r"    \midrule",
]
for scenario, cost, note in summary_rows:
    summary_lines.append(f"    {scenario} & {cost} & {note} \\\\")
summary_lines += [
    r"    \bottomrule",
    r"  \end{tabular}%",
    r"  }",
    r"\end{table}",
]
(RESULTS / "cost_summary_table.tex").write_text("\n".join(summary_lines))
print("  Saved -> results/cost_summary_table.tex")

print(f"\nKey figures:")
print(f"  Legacy infra:          EUR{LEGACY_EUR:.0f}/month")
print(f"  AWS steady state:      EUR{AWS_MONTHLY_EUR:.0f}/month excl. VAT (+{(AWS_MONTHLY_EUR/LEGACY_EUR-1)*100:.0f}%)")
print(f"  AWS steady state:      EUR{aws_incl:.0f}/month incl. VAT")
print(f"  Daily run rate:        USD{current['daily_total_usd']:.2f}/day")
