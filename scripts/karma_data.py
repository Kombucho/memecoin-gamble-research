"""Paths and loader for the repo. Rebuilds the per-caller structure of Karma's
validation/*.json from data/karma_scored_calls.csv (same rows, same order)."""
import csv, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data")
DL = os.path.join(DATA, "defillama")
CHARTS = os.path.join(ROOT, "charts")
FONTS = os.path.join(ROOT, "fonts")
OUTPUTS = os.path.join(ROOT, "outputs")  # regenerated intermediates (.npy), gitignored
os.makedirs(OUTPUTS, exist_ok=True)

def _f(x):
    return None if x in ("", None) else float(x)

def karma_files():
    """Yield {'wallet','handle','tokens':[...]} groups, as the validation JSON files were read."""
    groups = []
    with open(os.path.join(DATA, "karma_scored_calls.csv"), newline="") as fh:
        for r in csv.DictReader(fh):
            if not groups or groups[-1]["wallet"] != r["wallet"]:
                groups.append({"wallet": r["wallet"], "handle": r["handle"] or None, "tokens": []})
            groups[-1]["tokens"].append({"status": "scored", "mint": r["mint"],
                "copy_return_24h": _f(r["r24"]), "copy_peak_multiple": _f(r["peak"]),
                "label": r["label"] or None, "price_1h": _f(r["price_1h"]),
                "market_price_at_entry": _f(r["market_price_at_entry"])})
    return groups
