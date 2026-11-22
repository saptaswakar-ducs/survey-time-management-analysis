"""Unit tests for the hand-written statistical helpers, checked against known values / independent formulas."""
import numpy as np
import pandas as pd
from scipy import stats as sps
from tmsurvey import stats as S


def test_holm_and_bh_known_values():
    assert np.allclose(S.holm([0.01, 0.04, 0.03]), [0.03, 0.06, 0.06])
    assert np.allclose(S.benjamini_hochberg([0.01, 0.04, 0.03]), [0.03, 0.04, 0.04])


def test_wilson_ci_known_value():
    lo, hi = S.wilson_ci(5, 10)
    assert abs(lo - 0.2366) < 1e-3 and abs(hi - 0.7634) < 1e-3


def test_fmt_p():
    assert S.fmt_p(0.0004) == "< .001"
    assert S.fmt_p(0.034) == "= .034"


def test_kruskal_matches_scipy_and_epsilon_squared():
    rng = np.random.default_rng(1)
    df = pd.DataFrame({"y": rng.normal(size=60), "g": np.repeat(list("abc"), 20)})
    res = S.kruskal_effect(df, "y", "g")
    H, p = sps.kruskal(*[df.y[df.g == k] for k in "abc"])
    assert np.isclose(res["statistic"], H) and np.isclose(res["p"], p)
    assert np.isclose(res["effect_size"], max(0, (H - 2) / (60 - 3)))


def test_spearman_boot_rho_matches_scipy():
    rng = np.random.default_rng(2)
    x = rng.normal(size=40); y = x + rng.normal(size=40)
    out = S.spearman_boot(x, y, n_boot=200, seed=0)
    assert np.isclose(out["rho"], sps.spearmanr(x, y)[0])
    assert out["ci_low"] < out["rho"] < out["ci_high"]


def test_cochran_q_zero_when_prevalences_equal_and_undefined_when_degenerate():
    X = np.array([[1, 0], [0, 1], [1, 0], [0, 1]])          # both items ticked by 2 of 4 respondents
    assert np.isclose(S.cochran_q(X)["Q"], 0.0)
    col = np.array([1, 0, 1, 1])
    assert np.isnan(S.cochran_q(np.column_stack([col, col, col]))["Q"])   # no within-respondent variation


def test_cluster_ols_equals_hc1_when_every_row_is_its_own_cluster():
    rng = np.random.default_rng(3)
    n = 50
    x = rng.normal(size=n); y = 1 + 2 * x + rng.normal(size=n)
    X = pd.DataFrame({"Intercept": 1.0, "x": x})
    fit = S.cluster_ols(y, X, np.arange(n))
    Xv = X.values
    beta = np.linalg.solve(Xv.T @ Xv, Xv.T @ y)
    e = y - Xv @ beta
    bread = np.linalg.inv(Xv.T @ Xv)
    # cluster CR1 with G = n: factor G/(G-1) * (n-1)/(n-k); HC0 meat = X' diag(e^2) X
    V = (n / (n - 1)) * ((n - 1) / (n - 2)) * bread @ (Xv.T * e ** 2) @ Xv @ bread
    assert np.allclose(fit["beta"], beta) and np.allclose(fit["V"], V)


def test_perm_chi2_detects_perfect_association():
    a = pd.Series(list("xxxxyyyy") * 3)
    out = S.perm_chi2(a, a.copy(), n_perm=500, seed=0)
    assert out["p_perm"] < 0.01 and out["cramers_v_bc"] > 0.9
