"""Statistical helpers built only on NumPy / SciPy / pandas (so the repo has no heavy dependencies).

Contents
--------
* descriptive : describe_numeric, freq_table, wilson_ci
* group tests : kruskal_effect, pairwise_mwu_holm, mann_whitney
* association : spearman_boot, cramers_v_bc, perm_chi2, cochran_q
* regression  : cluster_ols (OLS with respondent-clustered CR1 standard errors), wald_cluster
* multiplicity: holm, benjamini_hochberg
"""
from __future__ import annotations

import itertools
import numpy as np
import pandas as pd
from scipy import stats


# ----------------------------------------------------------------------------- descriptive
def wilson_ci(k: int, n: int, z: float = 1.959964):
    """Wilson score interval for a binomial proportion."""
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    d = 1 + z ** 2 / n
    c = p + z ** 2 / (2 * n)
    h = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2))
    return ((c - h) / d, (c + h) / d)


def describe_numeric(df: pd.DataFrame, cols) -> pd.DataFrame:
    rows = []
    for c in cols:
        x = df[c].dropna().astype(float)
        rows.append({
            "variable": c, "n": len(x), "missing": int(df[c].isna().sum()),
            "mean": x.mean(), "sd": x.std(ddof=1), "median": x.median(),
            "q1": x.quantile(.25), "q3": x.quantile(.75), "min": x.min(), "max": x.max(),
            "skew": stats.skew(x, bias=False) if len(x) > 2 else np.nan,
        })
    return pd.DataFrame(rows).set_index("variable")


def freq_table(s: pd.Series) -> pd.DataFrame:
    """Counts, percentages and Wilson 95% CIs for a categorical series (keeps category order)."""
    vc = s.value_counts(sort=False)
    n = int(vc.sum())
    out = pd.DataFrame({"n": vc, "pct": 100 * vc / n})
    ci = [wilson_ci(int(k), n) for k in vc]
    out["ci_low"] = [100 * a for a, _ in ci]
    out["ci_high"] = [100 * b for _, b in ci]
    return out


def fmt_p(p: float) -> str:
    """APA-style p-value string: '< .001' or '= .034'."""
    if p is None or np.isnan(p):
        return "n/a"
    return "< .001" if p < .001 else f"= {p:.3f}".replace("0.", ".", 1)


# ----------------------------------------------------------------------------- multiplicity
def holm(p) -> np.ndarray:
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)
    adj = np.empty(m)
    running = 0.0
    for rank, idx in enumerate(order):
        running = max(running, (m - rank) * p[idx])
        adj[idx] = min(1.0, running)
    return adj


def benjamini_hochberg(p) -> np.ndarray:
    p = np.asarray(p, float)
    m = len(p)
    order = np.argsort(p)[::-1]
    adj = np.empty(m)
    prev = 1.0
    for i, idx in enumerate(order):
        rank = m - i
        prev = min(prev, p[idx] * m / rank)
        adj[idx] = prev
    return adj


# ----------------------------------------------------------------------------- group tests
def kruskal_effect(df: pd.DataFrame, value: str, group: str) -> dict:
    """Kruskal-Wallis H test with epsilon-squared effect size."""
    d = df[[value, group]].dropna()
    groups = [g[value].values for _, g in d.groupby(group, observed=True) if len(g) > 0]
    k, n = len(groups), len(d)
    H, p = stats.kruskal(*groups)
    eps2 = max(0.0, (H - k + 1) / (n - k))
    return {"test": "Kruskal-Wallis", "outcome": value, "factor": group, "n": n, "k_groups": k,
            "statistic": H, "df": k - 1, "p": p, "effect_size": eps2, "effect_name": "epsilon^2"}


def mann_whitney(a, b) -> dict:
    a, b = np.asarray(a, float), np.asarray(b, float)
    U, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    rbc = 2 * U / (len(a) * len(b)) - 1                      # rank-biserial correlation
    return {"U": U, "p": p, "rank_biserial": rbc, "n1": len(a), "n2": len(b)}


def pairwise_mwu_holm(df: pd.DataFrame, value: str, group: str) -> pd.DataFrame:
    d = df[[value, group]].dropna()
    levels = [l for l in d[group].cat.categories if (d[group] == l).any()] if hasattr(d[group], "cat") \
        else sorted(d[group].unique())
    rows = []
    for a, b in itertools.combinations(levels, 2):
        res = mann_whitney(d.loc[d[group] == a, value], d.loc[d[group] == b, value])
        rows.append({"group_a": a, "group_b": b, **res})
    out = pd.DataFrame(rows)
    out["p_holm"] = holm(out["p"].values)
    return out


# ----------------------------------------------------------------------------- association
def spearman_boot(x, y, n_boot: int = 2000, seed: int = 0, clusters=None) -> dict:
    """Spearman rho, asymptotic p, and a percentile bootstrap CI.
    If `clusters` is given the bootstrap resamples whole clusters (respondents) rather than rows."""
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    ok = ~(np.isnan(x) | np.isnan(y))
    x, y = x[ok], y[ok]
    rho, p = stats.spearmanr(x, y)
    rng = np.random.default_rng(seed)
    boots = []
    if clusters is None:
        n = len(x)
        for _ in range(n_boot):
            i = rng.integers(0, n, n)
            if np.ptp(x[i]) == 0 or np.ptp(y[i]) == 0:
                continue
            boots.append(stats.spearmanr(x[i], y[i])[0])
    else:
        cl = np.asarray(clusters)[ok]
        ids = np.unique(cl)
        idx_by = {c: np.where(cl == c)[0] for c in ids}
        for _ in range(n_boot):
            pick = rng.choice(ids, len(ids))
            i = np.concatenate([idx_by[c] for c in pick])
            if np.ptp(x[i]) == 0 or np.ptp(y[i]) == 0:
                continue
            boots.append(stats.spearmanr(x[i], y[i])[0])
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return {"rho": rho, "p": p, "ci_low": lo, "ci_high": hi, "n": len(x)}


def cramers_v_bc(table) -> float:
    """Bias-corrected Cramer's V (Bergsma 2013)."""
    t = np.asarray(table, float)
    n = t.sum()
    chi2 = stats.chi2_contingency(t, correction=False)[0]
    r, k = t.shape
    phi2 = chi2 / n
    phi2c = max(0, phi2 - (k - 1) * (r - 1) / (n - 1))
    rc = r - (r - 1) ** 2 / (n - 1)
    kc = k - (k - 1) ** 2 / (n - 1)
    d = min(kc - 1, rc - 1)
    return float(np.sqrt(phi2c / d)) if d > 0 else np.nan


def perm_chi2(a, b, n_perm: int = 10000, seed: int = 0) -> dict:
    """Chi-square test of independence with a Monte-Carlo permutation p-value (valid for sparse tables)."""
    a = pd.Series(a).reset_index(drop=True)
    b = pd.Series(b).reset_index(drop=True)
    tab = pd.crosstab(a, b)
    chi2_obs, p_asym, dof, expected = stats.chi2_contingency(tab, correction=False)
    rng = np.random.default_rng(seed)
    av, bv = pd.factorize(a)[0], pd.factorize(b)[0]
    na, nb = av.max() + 1, bv.max() + 1
    exp = expected
    count = 0
    for _ in range(n_perm):
        bp = rng.permutation(bv)
        t = np.zeros((na, nb))
        np.add.at(t, (av, bp), 1)
        chi2 = ((t - exp) ** 2 / exp).sum()
        count += chi2 >= chi2_obs - 1e-12
    return {"chi2": chi2_obs, "dof": dof, "p_asymptotic": p_asym,
            "p_perm": (count + 1) / (n_perm + 1), "cramers_v_bc": cramers_v_bc(tab),
            "n": int(tab.values.sum()), "min_expected": float(expected.min()),
            "pct_cells_expected_lt5": float((expected < 5).mean() * 100)}


def cochran_q(X) -> dict:
    """Cochran's Q test: do k binary items (columns) have the same prevalence across n respondents (rows)?"""
    X = np.asarray(X, float)
    n, k = X.shape
    T = X.sum(axis=0)
    L = X.sum(axis=1)
    N = X.sum()
    denom = k * N - (L ** 2).sum()
    if denom == 0:                       # no respondent varies across items: Q is undefined
        return {"Q": np.nan, "df": k - 1, "p": np.nan, "n": n}
    Q = (k - 1) * (k * (T ** 2).sum() - N ** 2) / denom
    return {"Q": Q, "df": k - 1, "p": stats.chi2.sf(Q, k - 1), "n": n}


# ----------------------------------------------------------------------------- regression
def design_matrix(df: pd.DataFrame, numeric=(), categorical=(), standardize=True):
    """Intercept + (z-scored) numeric + treatment-coded dummies. Returns X (DataFrame)."""
    parts = [pd.Series(1.0, index=df.index, name="Intercept")]
    for c in numeric:
        v = df[c].astype(float)
        parts.append(((v - v.mean()) / v.std(ddof=1) if standardize else v).rename(c))
    for c in categorical:
        d = pd.get_dummies(df[c].astype(str), prefix=c, drop_first=False)
        base = df[c].cat.categories[0] if hasattr(df[c], "cat") else sorted(df[c].unique())[0]
        d = d.drop(columns=f"{c}_{base}").astype(float)
        parts.append(d)
    return pd.concat(parts, axis=1)


def cluster_ols(y, X: pd.DataFrame, clusters) -> dict:
    """OLS with cluster-robust (CR1) covariance; t-tests use G-1 degrees of freedom.
    Appropriate here because each respondent contributes several task rows."""
    y = np.asarray(y, float)
    Xv = X.values.astype(float)
    cl = pd.Series(np.asarray(clusters))
    n, k = Xv.shape
    XtX_inv = np.linalg.inv(Xv.T @ Xv)
    beta = XtX_inv @ Xv.T @ y
    resid = y - Xv @ beta
    ids = cl.unique()
    G = len(ids)
    meat = np.zeros((k, k))
    for g in ids:
        m = (cl == g).values
        s = Xv[m].T @ resid[m]
        meat += np.outer(s, s)
    c = (G / (G - 1)) * ((n - 1) / (n - k))
    V = c * XtX_inv @ meat @ XtX_inv
    se = np.sqrt(np.diag(V))
    t = beta / se
    p = 2 * stats.t.sf(np.abs(t), G - 1)
    tcrit = stats.t.ppf(0.975, G - 1)
    ss_res = (resid ** 2).sum()
    ss_tot = ((y - y.mean()) ** 2).sum()
    table = pd.DataFrame({"coef": beta, "se": se, "t": t, "p": p,
                          "ci_low": beta - tcrit * se, "ci_high": beta + tcrit * se}, index=X.columns)
    return {"table": table, "V": V, "beta": beta, "n": n, "G": G, "k": k,
            "r2": 1 - ss_res / ss_tot, "adj_r2": 1 - (ss_res / (n - k)) / (ss_tot / (n - 1)), "names": list(X.columns)}


def wald_cluster(fit: dict, names) -> dict:
    """Joint cluster-robust Wald test that all coefficients in `names` are zero (F(q, G-1))."""
    idx = [fit["names"].index(n) for n in names]
    b = fit["beta"][idx]
    V = fit["V"][np.ix_(idx, idx)]
    q = len(idx)
    W = float(b @ np.linalg.solve(V, b))
    F = W / q
    return {"F": F, "df1": q, "df2": fit["G"] - 1, "p": float(stats.f.sf(F, q, fit["G"] - 1))}
