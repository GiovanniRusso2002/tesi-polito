"""
Central configuration for the Outsight Cloud evaluation framework.

All paths, environment definitions, endpoint declarations and visual
constants are defined here. No other module hard-codes these values.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Project root (directory that contains this file)
# ---------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Directory layout
# ---------------------------------------------------------------------------
DATA_RAW_DIR       = BASE_DIR / "data" / "raw"
DATA_PROCESSED_DIR = BASE_DIR / "data" / "processed"
FIGURES_DIR        = BASE_DIR / "figures"
RESULTS_DIR        = BASE_DIR / "results"

for _d in (DATA_RAW_DIR, DATA_PROCESSED_DIR, FIGURES_DIR, RESULTS_DIR):
    _d.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Benchmark execution parameters
# ---------------------------------------------------------------------------
N_REQUESTS = 100          # number of independent requests per environment
REQUEST_TIMEOUT = 30      # curl --max-time (seconds)
RETRY_ON_ERROR = True     # retry a failed curl measurement once before skipping

# ---------------------------------------------------------------------------
# Target environments
# ---------------------------------------------------------------------------
ENVIRONMENTS: dict[str, str] = {
    "legacy": "https://legacy.cloud.outsight.ai",
    "aws":    "https://cloud.outsight.ai",
}

ENV_LABELS: dict[str, str] = {
    "legacy": "Legacy (DigitalOcean)",
    "aws":    "AWS (ECS Fargate)",
}

# Colours used consistently across every figure.
ENV_COLORS: dict[str, str] = {
    "legacy": "#d62728",   # red
    "aws":    "#1f77b4",   # blue
}

# ---------------------------------------------------------------------------
# Measured timing metrics (raw curl output, values in seconds)
# ---------------------------------------------------------------------------
METRICS: list[str] = ["dns", "tcp", "tls", "ttfb", "total"]

METRIC_LABELS: dict[str, str] = {
    "dns":   "DNS Lookup",
    "tcp":   "TCP Connect",
    "tls":   "TLS Handshake",
    "ttfb":  "TTFB",
    "total": "Total Time",
}

# ---------------------------------------------------------------------------
# Endpoint registry
#
# Each entry is a benchmark "target" identified by a short key.
# Fields:
#   path        – URL path, appended to each environment's base URL
#   label       – human-readable name used in figure titles and tables
#   method      – HTTP verb (currently only GET is implemented via curl)
#   auth        – whether the request requires an Authorization header
#   headers     – extra static headers (dict)
#   description – one-sentence description for documentation purposes
# ---------------------------------------------------------------------------
ENDPOINTS: dict[str, dict] = {
    # ------------------------------------------------------------------
    # Public / unauthenticated endpoints
    # ------------------------------------------------------------------
    "home": {
        "path":        "/",
        "label":       "Homepage",
        "method":      "GET",
        "auth":        False,
        "headers":     {},
        "description": "Root HTML page served by the frontend.",
    },

    # ------------------------------------------------------------------
    # Authenticated REST API endpoints
    # ------------------------------------------------------------------
    "api_organizations": {
        "path":        "/api/v1/organizations",
        "label":       "API – Organizations",
        "method":      "GET",
        "auth":        True,
        "headers":     {"Accept": "application/json"},
        "description": "List all organisations visible to the authenticated user.",
    },
    "api_sites": {
        "path":        "/api/v1/sites",
        "label":       "API – Sites",
        "method":      "GET",
        "auth":        True,
        "headers":     {"Accept": "application/json"},
        "description": "List all sites visible to the authenticated user.",
    },
    "api_simulations": {
        "path":        "/api/v1/simulations",
        "label":       "API – Simulations",
        "method":      "GET",
        "auth":        True,
        "headers":     {"Accept": "application/json"},
        "description": "List all simulations visible to the authenticated user.",
    },
    "api_public_simulations": {
        "path":        "/api/v1/public/simulations",
        "label":       "API – Public Simulations",
        "method":      "GET",
        "auth":        False,
        "headers":     {"Accept": "application/json"},
        "description": "List publicly accessible simulations.",
    },

    # ------------------------------------------------------------------
    # Static / download benchmarks
    # ------------------------------------------------------------------
    "static_js": {
        "path":        None,   # full URL supplied externally in benchmark_download.py
        "label":       "Static – JS Bundle",
        "method":      "GET",
        "auth":        False,
        "headers":     {},
        "description": "Primary JavaScript application bundle.",
    },
    "static_css": {
        "path":        None,
        "label":       "Static – CSS Bundle",
        "method":      "GET",
        "auth":        False,
        "headers":     {},
        "description": "Primary CSS stylesheet.",
    },
}

# ---------------------------------------------------------------------------
# Authentication
#
# The bearer token is read from the environment variable OUTSIGHT_TOKEN at
# runtime. Scripts that need auth will raise a clear error if it is absent.
# ---------------------------------------------------------------------------
AUTH_ENV_VAR = "OUTSIGHT_TOKEN"

# ---------------------------------------------------------------------------
# Statistics configuration
# ---------------------------------------------------------------------------
PERCENTILES: list[float] = [0.90, 0.95, 0.99]
CONFIDENCE_LEVEL: float  = 0.95   # for t-distribution confidence intervals

# ---------------------------------------------------------------------------
# Figure output configuration
# ---------------------------------------------------------------------------
FIGURE_DPI    = 300
FIGURE_FORMAT = "pdf"   # "pdf" for LaTeX inclusion; also saves a .png preview

# Matplotlib rcParams overrides applied globally by plots.py
MPL_RC: dict = {
    "font.family":        "serif",
    "font.size":          11,
    "axes.titlesize":     12,
    "axes.labelsize":     11,
    "xtick.labelsize":    10,
    "ytick.labelsize":    10,
    "legend.fontsize":    10,
    "figure.dpi":         150,          # screen preview; export uses FIGURE_DPI
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.grid":          True,
    "grid.alpha":         0.35,
    "grid.linestyle":     "--",
}
