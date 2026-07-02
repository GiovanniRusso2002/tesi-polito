#!/usr/bin/env python3

import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

DATA = BASE_DIR / "data"
RESULTS = BASE_DIR / "results"
RESULTS.mkdir(exist_ok=True)

FILES = [
    ("Legacy", DATA / "legacy_home.csv"),
    ("AWS", DATA / "aws_home.csv"),
]

metrics = [
    "dns",
    "tcp",
    "tls",
    "ttfb",
    "total",
]

rows = []

for name, file in FILES:

    df = pd.read_csv(file)

    for metric in metrics:

        values = df[metric]

        rows.append({

            "Environment": name,
            "Metric": metric.upper(),

            "Mean (ms)": values.mean()*1000,
            "Median (ms)": values.median()*1000,
            "Std (ms)": values.std()*1000,
            "Min (ms)": values.min()*1000,
            "Max (ms)": values.max()*1000,
            "P95 (ms)": values.quantile(0.95)*1000,
            "P99 (ms)": values.quantile(0.99)*1000,
        })

stats = pd.DataFrame(rows)

stats.to_csv(RESULTS / "home_statistics.csv", index=False)

print(stats)
