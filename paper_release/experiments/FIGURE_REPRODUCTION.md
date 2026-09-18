# Paper single-column figures

The 01, 03, 05 and 06 plot scripts use `paper_style.py`: 3.335-inch
PDF width and Times New Roman. The original panel arrangements and aspect
ratios are retained (output heights within about 5% of the original PDFs).
Labels/legends use 7.5 PDF points, enlarged from the original printed figures;
the dense horizontal RL-loop figure uses 6.5-point ticks and an inset legend.
This compact layout takes priority over full 10-point body-size text.

Use `\includegraphics[width=\linewidth]{...}` inside a normal paper column.
Changing the inclusion width changes the effective font size. Log-axis
exponents are naturally smaller than the surrounding tick labels.

Run each existing `code/plot_*.py` script with Python, Matplotlib and pandas
(pandas is needed only for GPU traces). Figures are written to the experiment's
`figures/` directory (05 uses `results/`) and also copied into
`paper_release/figures/exp_figure/`. The manuscript directory is not overwritten.
Change `FONT_SIZE` in `paper_style.py` for the shared default. The compact
RL-loop figure has local tick/legend overrides to preserve its horizontal layout.

## Preserved sources and missing-data fallback

- 01: `data/ratio_summary_recovered.json` contains min, max, mean and median
  recovered from the original PDF bars/markers. Displayed one-decimal labels
  agree with the original. These are approximate geometric reconstructions,
  not reconstructed tenant-level measurements. If `data/results.json` exists,
  the original per-tenant computation is used instead.
- 03: `data/gpu_utilization_recovered.csv` contains 11,657 vertices from all four
  original vector curves. The JSON sidecar records source hash and provenance.
  These curves already include the original smoothing and PDF simplification;
  the fallback does not smooth again or compute raw-log statistics. If both
  original GPU CSV files exist, the original raw-data loading/smoothing is used.
- 05: loop-period bars/IQRs still use the existing measured summary CSV.
  `results/convergence_recovered.json` recovers the seven displayed convergence
  points per group from the preserved `rl_loop_discovery_two_panel.original.pdf`.
  If `data/requests.jsonl` exists, convergence is computed from requests instead.
  The two panels remain side by side in a compact canvas. Labels/legends use
  7.5 PDF points and ticks use 6.5 points, enlarged from the original printed
  figure while avoiding the vertical space needed for full 10-point text.
- 06: uses the existing millisecond breakdown values without modification.

`recover_plot_data.py` regenerates the recovered datasets from the preserved
source PDFs; this one-time recovery requires PyMuPDF. The original PDFs in
experiment roots are intentionally left untouched. Do not replace them with
the newly typeset output: the recovery calibration refers to their original
axis coordinates. Generated figures are transparent with minimal outer padding.
