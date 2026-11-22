"""Matplotlib figures for the survey analysis. Every function returns a Figure and (optionally) saves a PNG."""
from __future__ import annotations

import numpy as np
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

from . import config as C
from . import stats as S

# Okabe-Ito colour-blind-safe palette
BLUE, ORANGE, GREEN, RED, PURPLE, SKY, YELLOW, GREY = "#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#7F7F7F"
CHRONO_COL = {"Morning person": ORANGE, "No clear preference": GREY, "Evening / night person": BLUE}


def set_style():
    plt.rcParams.update({
        "figure.dpi": 110, "savefig.dpi": 200, "font.size": 10, "axes.titlesize": 11, "axes.titleweight": "bold",
        "axes.labelsize": 10, "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True,
        "grid.alpha": .25, "grid.linewidth": .6, "axes.axisbelow": True, "legend.frameon": False,
        "figure.facecolor": "white", "axes.facecolor": "white",
    })


def save(fig, name: str):
    C.FIG_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(C.FIG_DIR / f"{name}.png", bbox_inches="tight", facecolor="white")
    return fig


def _clock(x, _=None):
    h = x % 24
    return f"{int(h):02d}:{int(round((h % 1) * 60)):02d}"


def _stars(p):
    return "***" if p < .001 else "**" if p < .01 else "*" if p < .05 else ""


def _kw_title(k):
    p = k.get("p_holm", k["p"])
    lab = "p(Holm)" if "p_holm" in k else "p"
    return f"H = {k['statistic']:.1f}, {lab} {S.fmt_p(p)}, ε² = {k['effect_size']:.2f}"


def _panel(ax, letter):
    ax.text(-0.02, 1.08, letter, transform=ax.transAxes, fontsize=12, fontweight="bold", va="bottom")


# ------------------------------------------------------------------------------ 1. sample
def fig_sample(r: pd.DataFrame, save_as="fig01_sample_composition"):
    items = [("level", "Academic level"), ("age_group", "Age group"), ("living", "Living arrangement"),
             ("chronotype", "Chronotype"), ("plan_style", "Planning style"), ("app_interest", "Interest in a planning app")]
    fig, axes = plt.subplots(2, 3, figsize=(13, 6.4))
    for ax, (col, title), colr in zip(axes.ravel(), items, [BLUE, BLUE, BLUE, ORANGE, GREEN, PURPLE]):
        vc = r[col].value_counts(sort=False)
        ax.barh(range(len(vc)), vc.values, color=colr, alpha=.9)
        ax.set_yticks(range(len(vc)))
        ax.set_yticklabels(vc.index.astype(str))
        ax.invert_yaxis()
        ax.set_title(title, loc="left")
        ax.set_xlim(0, vc.max() * 1.25)
        ax.grid(axis="y", visible=False)
        for i, v in enumerate(vc.values):
            ax.text(v + .15, i, f"{v} ({100 * v / len(r):.0f}%)", va="center", fontsize=9)
    fig.suptitle(f"Sample composition (n = {len(r)} respondents)", x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return save(fig, save_as)


# ------------------------------------------------------------------------------ 2. distributions
def fig_distributions(r: pd.DataFrame, save_as="fig02_numeric_distributions"):
    fig, axes = plt.subplots(2, 4, figsize=(14, 6.6))
    ordinal = [("follow_plan", "Follows own plan (1-5)"), ("reschedule_freq", "Reschedule frequency (1-5)"),
               ("overall_productivity", "Overall productivity (1-5)")]
    for ax, (c, t) in zip(axes.ravel()[:3], ordinal):
        vc = r[c].value_counts().reindex(range(1, 6), fill_value=0)
        ax.bar(vc.index, vc.values, color=BLUE, alpha=.9)
        ax.axvline(r[c].mean(), color=RED, ls="--", lw=1.2, label=f"mean {r[c].mean():.2f}")
        ax.set_title(t, loc="left"); ax.set_xlabel("Rating"); ax.set_ylabel("Respondents"); ax.legend()
    cont = [("sleep_hours", "Sleep duration (h)", None), ("wake_h", "Wake-up time", _clock),
            ("bed_h_night", "Bed time (24 h+, so 24.5 = 00:30)", _clock), ("n_tasks_done", "Tasks reported per respondent", None)]
    for ax, (c, t, fmt) in zip(axes.ravel()[3:7], cont):
        x = r[c].dropna()
        ax.hist(x, bins=np.arange(x.min() - .25, x.max() + .75, .5) if c != "n_tasks_done" else np.arange(2.5, 11.5, 1),
                color=GREEN, alpha=.9, edgecolor="white")
        ax.axvline(x.median(), color=RED, ls="--", lw=1.2, label=f"median {x.median():.1f}")
        ax.set_title(t, loc="left"); ax.set_ylabel("Respondents"); ax.legend()
        if fmt: ax.xaxis.set_major_formatter(FuncFormatter(fmt))
    ax = axes.ravel()[7]
    fh = r["focus_hours"].dropna()
    ax.hist(fh, bins=np.arange(.5, 10.5, 1), color=PURPLE, alpha=.9, edgecolor="white")
    ax.set_title("Focus hours per day", loc="left"); ax.set_xlabel("Hours"); ax.set_ylabel("Respondents")
    ax.text(.97, .93, f"only {len(fh)} of {len(r)} answered", transform=ax.transAxes, ha="right", va="top", fontsize=9, color=GREY)
    fig.suptitle("Distributions of respondent-level numeric variables", x=0.01, ha="left", fontsize=13, fontweight="bold")
    fig.tight_layout()
    return save(fig, save_as)


# ------------------------------------------------------------------------------ 3. reasons / decisions
def fig_reasons_decisions(r: pd.DataFrame, save_as="fig03_postponement_reasons_and_decision_criteria", q_reasons=None, q_decide=None):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    for ax, mapping, title, col, q in [(axes[0], C.REASONS, "Reasons tasks do not go as planned", RED, q_reasons),
                                       (axes[1], C.DECIDE, "What decides when a task is done", BLUE, q_decide)]:
        rows = []
        for c, lab in mapping.items():
            k, n = int(r[c].sum()), len(r)
            lo, hi = S.wilson_ci(k, n)
            rows.append((lab, 100 * k / n, 100 * lo, 100 * hi))
        d = pd.DataFrame(rows, columns=["lab", "pct", "lo", "hi"]).sort_values("pct")
        ax.barh(d.lab, d.pct, color=col, alpha=.85, xerr=[d.pct - d.lo, d.hi - d.pct], error_kw=dict(ecolor="#333", lw=1, capsize=3))
        ax.set_xlabel("% of respondents (multiple answers allowed; bars = 95% Wilson CI)")
        ax.set_title(title, loc="left"); ax.set_xlim(0, 75); ax.grid(axis="y", visible=False)
        for y, p in enumerate(d.pct): ax.text(p + 1, y + .28, f"{p:.0f}%", fontsize=9, va="center")
        if q: ax.text(.98, .04, f"Cochran's Q = {q['Q']:.1f}, df = {q['df']}, p {S.fmt_p(q['p'])}", transform=ax.transAxes, ha="right", fontsize=9, color="#333")
    fig.tight_layout()
    return save(fig, save_as)


# ------------------------------------------------------------------------------ 4. peak time
def fig_peak_by_chronotype(r: pd.DataFrame, test=None, save_as="fig04_peak_time_by_chronotype"):
    tab = pd.crosstab(r["chronotype"], r["peak_time"]).reindex(columns=C.PEAK_ORDER, fill_value=0)
    cols = [ORANGE, YELLOW, SKY, BLUE, "#1b2a49", "#BBBBBB"]
    fig, ax = plt.subplots(figsize=(10, 3.9))
    left = np.zeros(len(tab))
    for (pk, col) in zip(tab.columns, cols):
        ax.barh(tab.index.astype(str), tab[pk], left=left, color=col, label=pk, edgecolor="white")
        for i, (v, l) in enumerate(zip(tab[pk], left)):
            if v > 0: ax.text(l + v / 2, i, int(v), ha="center", va="center", fontsize=9, color="white" if col in (BLUE, "#1b2a49") else "black")
        left += tab[pk].values
    ax.invert_yaxis(); ax.set_xlabel("Respondents"); ax.grid(axis="y", visible=False)
    ax.legend(title="Self-reported peak time", bbox_to_anchor=(1.01, 1), loc="upper left")
    t = "Peak time of day by chronotype"
    if test: t += f"  (permutation chi-square p {S.fmt_p(test['p_perm'])}, Cramer's V = {test['cramers_v_bc']:.2f})"
    ax.set_title(t, loc="left")
    fig.tight_layout()
    return save(fig, save_as)


# ------------------------------------------------------------------------------ 5. postponement
def fig_schedule_postpone(r: pd.DataFrame, save_as="fig05_scheduling_and_postponement"):
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), gridspec_kw={"width_ratios": [1, 1.25]})
    vc = r["schedule_first"].value_counts().sort_values()
    axes[0].barh(vc.index, vc.values, color=GREEN, alpha=.9)
    for i, v in enumerate(vc.values): axes[0].text(v + .2, i, f"{v} ({100 * v / len(r):.0f}%)", va="center", fontsize=9)
    axes[0].set_title("Which task gets scheduled first?", loc="left"); axes[0].set_xlim(0, vc.max() * 1.3); axes[0].grid(axis="y", visible=False)
    cats = sorted(set(r["most_postponed"]) | set(r["wish_better"]), key=lambda c: -(r["most_postponed"] == c).sum())
    a = r["most_postponed"].value_counts().reindex(cats, fill_value=0)
    b = r["wish_better"].value_counts().reindex(cats, fill_value=0)
    y = np.arange(len(cats)); h = .38
    axes[1].barh(y - h / 2, a.values, h, color=RED, label="Most often postponed")
    axes[1].barh(y + h / 2, b.values, h, color=BLUE, label="Wish to manage better")
    axes[1].set_yticks(y); axes[1].set_yticklabels(cats); axes[1].invert_yaxis(); axes[1].grid(axis="y", visible=False)
    axes[1].set_xlabel("Respondents"); axes[1].legend(loc="lower right"); axes[1].set_title("Postponed vs. wish to improve", loc="left")
    fig.tight_layout()
    return save(fig, save_as)


# ------------------------------------------------------------------------------ 6. task profile
def fig_task_profile(t: pd.DataFrame, save_as="fig06_task_profile_heatmap"):
    m = t.groupby("task_label")[C.RATINGS].mean()
    m = m.loc[m["energy"].sort_values(ascending=False).index]
    norm = (m - m.min()) / (m.max() - m.min())
    fig, ax = plt.subplots(figsize=(9.5, 5.6))
    im = ax.imshow(norm.values, cmap="YlGnBu", aspect="auto")
    ax.set_xticks(range(m.shape[1])); ax.set_xticklabels([c.capitalize() for c in m.columns], rotation=35, ha="right")
    ax.set_yticks(range(m.shape[0])); ax.set_yticklabels(m.index); ax.grid(False)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            ax.text(j, i, f"{m.values[i, j]:.2f}", ha="center", va="center", fontsize=9, color="white" if norm.values[i, j] > .6 else "black")
    cb = fig.colorbar(im, ax=ax, fraction=.035, pad=.02); cb.set_label("Relative level within column (min-max)")
    ax.set_title("Mean rating (1-5) by task type; colour is scaled within each column", loc="left")
    fig.tight_layout()
    return save(fig, save_as)


def fig_time_blocks(t: pd.DataFrame, save_as="fig07_time_block_usage"):
    share = 100 * t.groupby("task_label")[C.BLOCKS].mean()
    share.columns = C.BLOCK_LABELS
    order = (share[["Early morning", "Morning"]].sum(axis=1) - share[["Night", "Late night"]].sum(axis=1)).sort_values(ascending=False).index
    share = share.loc[order]
    overall = 100 * t[C.BLOCKS].mean()
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 5.2), gridspec_kw={"width_ratios": [1.6, 1]})
    im = ax.imshow(share.values, cmap="OrRd", aspect="auto", vmin=0, vmax=100)
    ax.set_xticks(range(6)); ax.set_xticklabels(share.columns, rotation=30, ha="right")
    ax.set_yticks(range(len(share))); ax.set_yticklabels(share.index); ax.grid(False)
    for i in range(share.shape[0]):
        for j in range(6):
            ax.text(j, i, f"{share.values[i, j]:.0f}", ha="center", va="center", fontsize=9, color="white" if share.values[i, j] > 60 else "black")
    fig.colorbar(im, ax=ax, fraction=.04, pad=.02).set_label("% of reports placing the task in the block")
    ax.set_title("When is each task done? (blocks are not exclusive)", loc="left")
    ax2.barh(C.BLOCK_LABELS, overall.values, color=[ORANGE, ORANGE, YELLOW, SKY, BLUE, "#1b2a49"])
    ax2.invert_yaxis(); ax2.set_xlabel("% of all task reports"); ax2.grid(axis="y", visible=False)
    for i, v in enumerate(overall.values): ax2.text(v + .7, i, f"{v:.0f}%", va="center", fontsize=9)
    ax2.set_title("Overall use of each block", loc="left"); ax2.set_xlim(0, 55)
    fig.tight_layout()
    return save(fig, save_as)


def fig_duration(t: pd.DataFrame, save_as="fig08_task_duration"):
    order = t.groupby("task_label")["duration_min"].median().sort_values().index
    data = [t.loc[t.task_label == k, "duration_min"].values for k in order]
    fig, ax = plt.subplots(figsize=(9.5, 5))
    bp = ax.boxplot(data, vert=False, patch_artist=True, tick_labels=order, widths=.6, medianprops=dict(color="black"))
    for p in bp["boxes"]: p.set(facecolor=SKY, alpha=.8)
    rng = np.random.default_rng(C.SEED)
    for i, d in enumerate(data, 1):
        ax.scatter(d + rng.uniform(-4, 4, len(d)), i + rng.uniform(-.18, .18, len(d)), s=8, color="#333", alpha=.35, zorder=3)
    ax.set_xlabel("Duration (minutes)"); ax.grid(axis="y", visible=False)
    ax.set_title("Reported duration by task type (box = IQR; dots = individual reports)", loc="left")
    fig.tight_layout()
    return save(fig, save_as)


# ------------------------------------------------------------------------------ 9-10 group comparisons
def _box_jitter(ax, d, value, group, order, colors, seed=C.SEED):
    rng = np.random.default_rng(seed)
    data = [d.loc[d[group] == g, value].dropna().values for g in order]
    bp = ax.boxplot(data, tick_labels=[str(o) for o in order], patch_artist=True, widths=.55,
                    medianprops=dict(color="black", lw=1.6), showfliers=False)
    for p, c in zip(bp["boxes"], colors): p.set(facecolor=c, alpha=.35)
    for i, (x, c) in enumerate(zip(data, colors), 1):
        ax.scatter(i + rng.uniform(-.16, .16, len(x)), x + rng.uniform(-.06, .06, len(x)), s=22, color=c, edgecolor="white", lw=.4, zorder=3)
        ax.scatter(i, np.mean(x), marker="D", s=36, color="white", edgecolor="black", zorder=4)


def fig_chronotype(r: pd.DataFrame, kw: dict, save_as="fig09_chronotype_comparisons"):
    order = C.CHRONO_ORDER
    cols = [CHRONO_COL[o] for o in order]
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.8))
    spec = [("overall_productivity", "Overall productivity (1-5)", None), ("sleep_hours", "Sleep duration (h)", None), ("wake_h", "Wake-up time", _clock)]
    for ax, (v, yl, fmt), letter in zip(axes, spec, "abc"):
        _box_jitter(ax, r, v, "chronotype", order, cols)
        ax.set_ylabel(yl); ax.tick_params(axis="x", labelrotation=12)
        k = kw[v]
        ax.set_title(_kw_title(k), loc="left", fontsize=10)
        if fmt: ax.yaxis.set_major_formatter(FuncFormatter(fmt))
        _panel(ax, letter)
    fig.suptitle("Chronotype is tied to wake time, but not detectably to sleep duration or overall productivity   (◇ = mean)", x=0.01, ha="left", fontsize=12, fontweight="bold", y=1.03)
    fig.tight_layout()
    return save(fig, save_as)


def fig_plan_style(r: pd.DataFrame, kw: dict, save_as="fig10_planning_style"):
    order = C.PLAN_ORDER
    cols = [GREY, SKY, GREEN, BLUE, PURPLE]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.9), gridspec_kw={"width_ratios": [1, 1, 1.05]})
    for ax, v, yl, letter in zip(axes[:2], ["follow_plan", "overall_productivity"], ["Follows own plan (1-5)", "Overall productivity (1-5)"], "ab"):
        _box_jitter(ax, r, v, "plan_style", order, cols)
        ax.set_ylabel(yl); ax.set_xticklabels([o.replace(" / ", "/\n").replace(" ", "\n", 1) for o in order], fontsize=8)
        ax.set_title(_kw_title(kw[v]), loc="left", fontsize=10)
        _panel(ax, letter)
    ax = axes[2]
    tab = pd.crosstab(r["plan_style"], r["app_interest"]).reindex(index=order, columns=C.APP_ORDER, fill_value=0)
    pct = 100 * tab.div(tab.sum(axis=1), axis=0)
    palette = [RED, ORANGE, "#DDDDDD", SKY, BLUE]
    left = np.zeros(len(pct))
    for c, col in zip(pct.columns, palette):
        ax.barh(range(len(pct)), pct[c], left=left, color=col, label=c, edgecolor="white"); left += pct[c].values
    ax.set_yticks(range(len(pct))); ax.set_yticklabels([f"{o} (n={n})" for o, n in zip(order, tab.sum(axis=1))], fontsize=8)
    ax.invert_yaxis(); ax.set_xlabel("% within planning style"); ax.grid(axis="y", visible=False)
    ax.legend(title="Would use a planning app?", fontsize=8, title_fontsize=8, bbox_to_anchor=(0.5, -0.2), loc="upper center", ncol=3)
    ax.set_title(_kw_title(kw["app_score"]), loc="left", fontsize=10); _panel(ax, "c")
    fig.tight_layout()
    return save(fig, save_as)


# ------------------------------------------------------------------------------ 11-12 correlations
def _heat(ax, mat, labels, stars=None, cmap="RdBu_r", fs=8.5):
    im = ax.imshow(mat, cmap=cmap, vmin=-1, vmax=1); ax.grid(False)
    ax.set_xticks(range(len(labels))); ax.set_xticklabels(labels, rotation=40, ha="right")
    ax.set_yticks(range(len(labels))); ax.set_yticklabels(labels)
    for i in range(len(labels)):
        for j in range(len(labels)):
            if i == j: continue
            s = stars[i][j] if stars is not None else ""
            ax.text(j, i, f"{mat[i, j]:.2f}{s}", ha="center", va="center", fontsize=fs, color="white" if abs(mat[i, j]) > .55 else "black")
    return im


def fig_corr_respondent(rho, stars, labels, save_as="fig11_respondent_correlations"):
    fig, ax = plt.subplots(figsize=(8.2, 6.6))
    im = _heat(ax, rho, labels, stars)
    fig.colorbar(im, ax=ax, fraction=.04, pad=.02).set_label("Spearman rho")
    ax.set_title("Respondent-level Spearman correlations (n = 39)\n* p<.05  ** p<.01  *** p<.001 after Holm correction", loc="left")
    fig.tight_layout()
    return save(fig, save_as)


def fig_scatter_productivity(r: pd.DataFrame, res: dict, save_as="fig12_productivity_associations"):
    fig, axes = plt.subplots(1, 2, figsize=(11.5, 4.7))
    rng = np.random.default_rng(C.SEED)
    for ax, x, xl, key, col in [(axes[0], "follow_plan", "Follows own plan (1-5)", "follow_plan", BLUE), (axes[1], "sleep_hours", "Sleep duration (h)", "sleep_hours", GREEN)]:
        jx = r[x] + rng.uniform(-.08, .08, len(r)); jy = r["overall_productivity"] + rng.uniform(-.08, .08, len(r))
        ax.scatter(jx, jy, s=34, color=col, alpha=.75, edgecolor="white")
        b = np.polyfit(r[x], r["overall_productivity"], 1); xs = np.linspace(r[x].min(), r[x].max(), 50)
        ax.plot(xs, np.polyval(b, xs), color=RED, lw=2)
        s = res[key]
        ax.set_title(f"rho = {s['rho']:.2f} [{s['ci_low']:.2f}, {s['ci_high']:.2f}], p {S.fmt_p(s['p'])}", loc="left", fontsize=10)
        ax.set_xlabel(xl); ax.set_ylabel("Overall productivity (1-5)")
    fig.suptitle("Overall productivity vs. plan adherence and sleep (points jittered; line = OLS fit for display)", x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return save(fig, save_as)


# ------------------------------------------------------------------------------ 13 task level
def task_means_cluster(t: pd.DataFrame, y: str):
    """Mean of `y` per task with respondent-clustered 95% CI (from an intercept-free dummy regression)."""
    X = pd.get_dummies(t["task_label"]).astype(float)
    f = S.cluster_ols(t[y], X, t["row_id"])
    return f["table"][["coef", "ci_low", "ci_high"]]


def fig_task_means(t: pd.DataFrame, outcomes=("energy", "productivity", "satisfaction", "interruptions"), save_as="fig13_task_level_means"):
    base = task_means_cluster(t, "energy").sort_values("coef")
    order = list(base.index)
    fig, axes = plt.subplots(1, len(outcomes), figsize=(3.6 * len(outcomes), 5), sharey=True)
    cols = [ORANGE, BLUE, GREEN, RED]
    for ax, y, c in zip(axes, outcomes, cols):
        m = task_means_cluster(t, y).loc[order]
        ax.errorbar(m["coef"], range(len(m)), xerr=[m["coef"] - m["ci_low"], m["ci_high"] - m["coef"]], fmt="o", color=c, ecolor=c, capsize=3, ms=6)
        ax.axvline(t[y].mean(), color="#333", ls=":", lw=1)
        ax.set_title(y.capitalize(), loc="left"); ax.set_xlabel("Mean (1-5), 95% CI"); ax.set_xlim(1, 5)
        ax.set_yticks(range(len(order))); ax.set_yticklabels(order); ax.grid(axis="y", alpha=.15)
    fig.suptitle("Task-level means with respondent-clustered 95% CIs (dotted = grand mean)", x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return save(fig, save_as)


def fig_corr_task(rho, lo, hi, labels, save_as="fig14_task_level_correlations"):
    sig = [["" if i == j else ("*" if (lo[i][j] > 0 or hi[i][j] < 0) else "") for j in range(len(labels))] for i in range(len(labels))]
    fig, ax = plt.subplots(figsize=(7.8, 6.4))
    im = _heat(ax, rho, labels, sig)
    fig.colorbar(im, ax=ax, fraction=.04, pad=.02).set_label("Spearman rho")
    ax.set_title("Task-level Spearman correlations (301 reports, 39 respondents)\n* = respondent-cluster bootstrap 95% CI excludes 0", loc="left")
    fig.tight_layout()
    return save(fig, save_as)


def fig_forest(fits: dict, save_as="fig15_regression_forest"):
    fig, axes = plt.subplots(1, len(fits), figsize=(6.4 * len(fits), 5.2), sharey=True)
    axes = np.atleast_1d(axes)
    order = list(next(iter(fits.values()))[0].sort_values("coef").index)   # ONE common row order for all panels
    for ax, (name, (tab, r2, n, g)) in zip(axes, fits.items()):
        tab = tab.loc[order]
        sig = tab["p"] < .05
        ax.errorbar(tab["coef"], range(len(tab)), xerr=[tab["coef"] - tab["ci_low"], tab["ci_high"] - tab["coef"]], fmt="none",
                    ecolor="#888", capsize=2.5, lw=1.2, zorder=1)
        ax.scatter(tab["coef"], range(len(tab)), c=np.where(sig, RED, BLUE), s=42, zorder=3)
        ax.axvline(0, color="#333", lw=1)
        ax.set_yticks(range(len(tab))); ax.set_yticklabels(tab.index)
        ax.set_xlabel("Change in rating per 1 SD (95% CI, respondent-clustered)")
        ax.set_title(f"{name}\nR² = {r2:.2f}; n = {n}; clusters = {g}   (red = p<.05)", loc="left", fontsize=10)
        ax.grid(axis="y", alpha=.15)
    fig.tight_layout()
    return save(fig, save_as)


def fig_chrono_blocks(t: pd.DataFrame, save_as="fig16_chronotype_by_time_block"):
    """Descriptive heatmap; sleep reports are excluded because ~95% of them sit in early-morning/late-night blocks
    and would swamp the pattern for every chronotype."""
    d = t[t["task"] != "sleep"]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.1))
    for ax, y, cmap in zip(axes, ["energy", "productivity"], ["YlOrRd", "YlGnBu"]):
        cnt = np.array([[int(((d.chronotype == ch) & (d[b] == 1)).sum()) for b in C.BLOCKS] for ch in C.CHRONO_ORDER])
        mat = np.array([[d.loc[(d.chronotype == ch) & (d[b] == 1), y].mean() for b in C.BLOCKS] for ch in C.CHRONO_ORDER])
        mat = np.where(cnt >= 5, mat, np.nan)          # mask cells with < 5 reports (too noisy to read)
        lo, hi = np.nanmin(mat), np.nanmax(mat)
        im = ax.imshow(mat, cmap=cmap, vmin=lo - .1, vmax=hi + .1, aspect="auto"); ax.grid(False)
        ax.set_xticks(range(6)); ax.set_xticklabels(C.BLOCK_LABELS, rotation=25, ha="right")
        ax.set_yticks(range(3)); ax.set_yticklabels(C.CHRONO_ORDER)
        for i, ch in enumerate(C.CHRONO_ORDER):
            for j, b in enumerate(C.BLOCKS):
                n = cnt[i, j]
                if np.isnan(mat[i, j]):
                    ax.text(j, i, f"n={n}\n(<5, hidden)", ha="center", va="center", fontsize=7.5, color="#888")
                    continue
                dark = (mat[i, j] - lo) / (hi - lo + 1e-9) > .65
                ax.text(j, i, f"{mat[i, j]:.2f}\nn={n}", ha="center", va="center", fontsize=8, color="white" if dark else "black")
        fig.colorbar(im, ax=ax, fraction=.04, pad=.02)
        ax.set_title(f"Mean {y} of tasks done in each block (excl. sleep)", loc="left")
    fig.tight_layout()
    return save(fig, save_as)
