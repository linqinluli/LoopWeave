"""Recover DISPLAYED vector vertices/statistics, never raw experiment samples.

Requires PyMuPDF. The source PDFs are preserved unchanged. Coordinate anchors
below are PDF grid/tick positions verified against the original plot scripts.
Recovered curves must not be smoothed again or used to compute raw-log stats.
"""
import csv
import hashlib
import json
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent


def provenance(path):
    return {"source_pdf": path.name,
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "kind": "Recovered displayed PDF geometry; not raw measurements"}


def vertices(drawing):
    items = drawing["items"]
    assert all(item[0] == "l" for item in items)
    points = [items[0][1]]
    for _, start, end in items:
        assert abs(start.x - points[-1].x) < 0.001
        assert abs(start.y - points[-1].y) < 0.001
        points.append(end)
    return points


def recover_gpu():
    root = ROOT / "03_training_gpu_wastes"
    source = root / "gpu_utilization_over_time.pdf"
    page = pymupdf.open(source)[0]
    curves = [d for d in page.get_drawings() if d["type"] == "s" and len(d["items"]) > 100]
    assert len(curves) == 4
    rows = []
    for i, drawing in enumerate(curves):
        panel = i // 2
        # X-grid 0/50min and Y-grid 0/100%, in PDF page coordinates.
        x0 = 38.114646911621094
        x50 = [95.7325210571289, 105.52345275878906][panel]
        y0 = [97.87629699707031, 211.0662841796875][panel]
        y100 = [22.315536499023438, 135.50555419921875][panel]
        for point in vertices(drawing):
            rows.append(["async" if panel == 0 else "sync", i % 2,
                         (point.x - x0) * 50 / (x50 - x0),
                         (y0 - point.y) * 100 / (y0 - y100)])
    dest = root / "data"
    dest.mkdir(exist_ok=True)
    with (dest / "gpu_utilization_recovered.csv").open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["mode", "index", "elapsed_min", "gpu_util"])
        writer.writerows(rows)
    info = provenance(source)
    info["vertices"] = len(rows)
    info["note"] = "Already smoothed and possibly simplified by the original PDF renderer."
    (dest / "gpu_utilization_recovered.json").write_text(json.dumps(info, indent=2))


def recover_ratios():
    root = ROOT / "01_training_sampling_breakdown"
    source = root / "sampling_training_ratio_range.pdf"
    drawings = pymupdf.open(source)[0].get_drawings()
    origin, tick5 = drawings[2]["rect"].x0, drawings[3]["rect"].x0
    def value(x):
        return (x - origin) * 5 / (tick5 - origin)
    result = provenance(source)
    result["groups"] = {}
    for name, bar, diamond, circle in [("Personal", 7, 16, 18), ("Group", 8, 17, 19)]:
        b, d, c = [drawings[i]["rect"] for i in (bar, diamond, circle)]
        result["groups"][name] = {"min": value(b.x0), "max": value(b.x1),
                                  "mean": value((d.x0 + d.x1) / 2),
                                  "median": value((c.x0 + c.x1) / 2)}
    dest = root / "data"
    dest.mkdir(exist_ok=True)
    (dest / "ratio_summary_recovered.json").write_text(json.dumps(result, indent=2))


def recover_convergence():
    root = ROOT / "05_rl_loop_discovery"
    source = root / "rl_loop_discovery_two_panel.original.pdf"
    drawings = pymupdf.open(source)[0].get_drawings()
    curves = [d for d in drawings if d["type"] == "s" and len(d["items"]) == 6]
    assert len(curves) == 2
    result = provenance(source)
    result["warmups"] = [1, 2, 3, 4, 5, 6, 8]
    result["groups"] = {}
    for name, curve in zip(["Personal", "Group"], curves):
        points = vertices(curve)
        result["groups"][name] = [(154.11599731445312 - p.y) * 2 /
                                  (154.11599731445312 - 128.72183227539062) for p in points]
        xs = [2 + (p.x - 340.0841979980469) * 2 /
              (375.87677001953125 - 340.0841979980469) for p in points]
        assert all(abs(x - w) < 0.001 for x, w in zip(xs, result["warmups"]))
    (root / "results" / "convergence_recovered.json").write_text(json.dumps(result, indent=2))


if __name__ == "__main__":
    recover_gpu()
    recover_ratios()
    recover_convergence()
