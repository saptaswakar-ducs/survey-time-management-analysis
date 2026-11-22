"""Regression test: forest-plot labels must sit next to the coefficient they describe."""
import matplotlib
matplotlib.use("Agg")
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.collections import PathCollection
from tmsurvey import plots, config as C


def _tab(vals):
    idx = ["a", "b", "c"]
    return pd.DataFrame({"coef": vals, "ci_low": [v - .1 for v in vals], "ci_high": [v + .1 for v in vals], "p": [.5, .5, .5]}, index=idx)


def test_forest_labels_align_with_points(tmp_path, monkeypatch):
    monkeypatch.setattr(C, "FIG_DIR", tmp_path)
    fits = {"m1": (_tab([0.3, 0.1, -0.2]), .1, 10, 3), "m2": (_tab([-0.5, 0.4, 0.0]), .1, 10, 3)}
    fig = plots.fig_forest(fits, save_as="t")
    for ax, (_, (tab, *_)) in zip(fig.axes, fits.items()):
        labels = [t.get_text() for t in fig.axes[0].get_yticklabels()]   # y-axis is shared: labels live on panel 1
        pts = [c for c in ax.collections if isinstance(c, PathCollection)][0].get_offsets()   # scatter points (x = coef, y = row)
        for x, y in pts:
            assert abs(tab.loc[labels[int(round(y))], "coef"] - x) < 1e-9
    plt.close(fig)
