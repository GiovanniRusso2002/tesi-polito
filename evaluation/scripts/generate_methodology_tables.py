"""
Generate LaTeX tables for the Benchmark Methodology section (7.1).

Produces three files in results/:
    methodology_params_table.tex   – benchmark configuration parameters
    methodology_metrics_table.tex  – measured HTTP timing metrics and their
                                     correspondence to curl variables
    methodology_environments_table.tex – As-Is vs To-Be environment comparison
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import config

RESULTS = config.RESULTS_DIR
RESULTS.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# 1. Benchmark configuration parameters
# ---------------------------------------------------------------------------

PARAMS = [
    ("Sample size per environment",  r"$N = 100$ independent requests"),
    ("Request timeout",              r"30\,s (curl \texttt{--max-time})"),
    ("Retry policy",                 r"1 automatic retry on transport error"),
    ("HTTP method",                  r"GET"),
    ("Protocol",                     r"HTTPS (TLS\,1.2 / 1.3)"),
    ("Confidence level",             r"95\,\% (Student $t$-distribution)"),
    ("Percentiles reported",         r"P90, P95, P99"),
    ("Measurement tool",             r"\texttt{curl} built-in timing variables"),
    ("Output format",                r"CSV (one row per request)"),
    ("Client location",              r"Fixed single location (Paris, FR)"),
]


def _params_table() -> str:
    rows = "\n".join(
        f"    {param} & {value} \\\\"
        for param, value in PARAMS
    )
    return rf"""\begin{{table}}[htbp]
  \centering
  \caption{{Benchmark configuration parameters used for all latency measurements.}}
  \label{{tab:bench_params}}
  \small
  \begin{{tabular}}{{lp{{8cm}}}}
    \toprule
    \textbf{{Parameter}} & \textbf{{Value / Description}} \\
    \midrule
{rows}
    \bottomrule
  \end{{tabular}}
\end{{table}}
"""


# ---------------------------------------------------------------------------
# 2. HTTP timing metrics and curl variables
# ---------------------------------------------------------------------------

METRICS_INFO = [
    ("DNS Lookup",     r"\texttt{time\_namelookup}",
     "Elapsed time from request start until DNS name resolution completes."),
    ("TCP Connect",    r"\texttt{time\_connect}",
     "Elapsed time from request start until the TCP three-way handshake completes."),
    ("TLS Handshake",  r"\texttt{time\_appconnect}",
     "Elapsed time from request start until the TLS/SSL handshake and key exchange complete."),
    ("TTFB",           r"\texttt{time\_starttransfer}",
     "Time to First Byte: from request start until the first response byte is received."),
    ("Total Time",     r"\texttt{time\_total}",
     "Total elapsed time of the complete HTTP transaction, including response body transfer."),
]


def _metrics_table() -> str:
    rows = "\n".join(
        f"    {label} & {var} & {desc} \\\\"
        for label, var, desc in METRICS_INFO
    )
    return rf"""\begin{{table}}[htbp]
  \centering
  \caption{{HTTP timing metrics extracted from \texttt{{curl}} and their meaning.
    All values are recorded in seconds by \texttt{{curl}} and converted to
    milliseconds during post-processing.}}
  \label{{tab:bench_metrics}}
  \small
  \begin{{tabular}}{{llp{{7.5cm}}}}
    \toprule
    \textbf{{Metric}} & \textbf{{\texttt{{curl}} variable}} & \textbf{{Description}} \\
    \midrule
{rows}
    \bottomrule
  \end{{tabular}}
\end{{table}}
"""


# ---------------------------------------------------------------------------
# 3. As-Is vs To-Be environment comparison
# ---------------------------------------------------------------------------

ENV_COMPARISON = [
    ("Hosting platform",       "DigitalOcean Droplet",
                               "AWS ECS Fargate"),
    ("Container orchestration","None",
                               "ECS with auto-scaling task definitions"),
    ("CDN / edge caching",     "None",
                               "Amazon CloudFront"),
    ("DNS resolver",           "Standard recursive DNS",
                               "Amazon Route\\,53"),
    ("TLS termination",        "Nginx + Let's Encrypt",
                               "CloudFront + ACM certificate"),
    ("Load balancer",          "Nginx reverse proxy",
                               "AWS Application Load Balancer"),
    ("Deployment region",      "Amsterdam",
                               "Paris"),
    ("Measured base URL",      r"\texttt{legacy.cloud.outsight.ai}",
                               r"\texttt{cloud.outsight.ai}"),
]


def _environments_table() -> str:
    rows = "\n".join(
        f"    {aspect} & {legacy} & {aws} \\\\"
        for aspect, legacy, aws in ENV_COMPARISON
    )
    return rf"""\begin{{table}}[htbp]
  \centering
  \caption{{Infrastructure comparison between the As-Is (Legacy) and To-Be (AWS)
    benchmark targets. Both environments expose the same application over HTTPS.}}
  \label{{tab:bench_environments}}
  \small
  \resizebox{{\textwidth}}{{!}}{{%
  \begin{{tabular}}{{lp{{5cm}}p{{5.5cm}}}}
    \toprule
    \textbf{{Aspect}} & \textbf{{As-Is}} & \textbf{{To-Be}} \\
    \midrule
{rows}
    \bottomrule
  \end{{tabular}}%
  }}
\end{{table}}
"""


# ---------------------------------------------------------------------------
# Write files
# ---------------------------------------------------------------------------

def main() -> None:
    files = {
        "methodology_params_table.tex":       _params_table(),
        "methodology_metrics_table.tex":      _metrics_table(),
        "methodology_environments_table.tex": _environments_table(),
    }

    for filename, content in files.items():
        path = RESULTS / filename
        path.write_text(content, encoding="utf-8")
        print(f"  Written → {path.relative_to(_ROOT)}")

    print("\nAll methodology tables generated successfully.")


if __name__ == "__main__":
    main()
