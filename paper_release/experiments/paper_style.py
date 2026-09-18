"""Typography at actual paper column width (7in text, 0.33in gutter)."""
from pathlib import Path
import shutil

import matplotlib as mpl
from matplotlib.transforms import Bbox

COLUMN_WIDTH = (7.0 - 0.33) / 2
# Compact original-aspect figures: readable type without enlarging the panels.
FONT_SIZE = 7.5


def apply_style():
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["Times New Roman", "Nimbus Roman", "DejaVu Serif"],
        "font.size": FONT_SIZE,
        "axes.labelsize": FONT_SIZE,
        "axes.titlesize": FONT_SIZE,
        "xtick.labelsize": FONT_SIZE,
        "ytick.labelsize": FONT_SIZE,
        "legend.fontsize": FONT_SIZE,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": None,
        "savefig.transparent": True,
        "axes.linewidth": 0.8,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "path.simplify": False,
    })


def save_figure(fig, out_dir, stem, *, vertical_pad=0.015):
    """Preserve column width so includegraphics[width=\\linewidth] is 1:1."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.canvas.draw()
    box = fig.get_tightbbox(fig.canvas.get_renderer())
    if box.x0 < -0.01 or box.x1 > COLUMN_WIDTH + 0.01:
        raise ValueError(f"{stem}: text exceeds column width: {box}")
    bounds = Bbox.from_extents(0, box.y0 - vertical_pad, COLUMN_WIDTH, box.y1 + vertical_pad)
    for ext in ("pdf", "png"):
        output = out_dir / f"{stem}.{ext}"
        fig.savefig(output, bbox_inches=bounds,
                    pad_inches=0, transparent=True)
        paper_dir = Path(__file__).resolve().parent.parent / "figures" / "exp_figure"
        paper_dir.mkdir(parents=True, exist_ok=True)
        if output.resolve() != (paper_dir / output.name).resolve():
            shutil.copy2(output, paper_dir / output.name)
    print(out_dir / f"{stem}.pdf")
