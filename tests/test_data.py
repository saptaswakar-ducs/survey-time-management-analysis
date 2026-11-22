"""Integrity tests for the cleaned datasets: fail loudly if the data files change unexpectedly."""
import pandas as pd
from tmsurvey import config as C, data


def test_respondent_table():
    r = data.load_respondents()
    assert len(r) == 39
    assert r["row_id"].is_unique
    assert r["chronotype"].notna().all() and r["plan_style"].notna().all()
    assert r["flagged"].sum() == 4          # 2 sleep outliers + 2 straight-liners (see cleaning_report)


def test_task_table():
    r, t = data.load_respondents(), data.load_tasks()
    assert len(t) == 301
    assert set(t["row_id"]) <= set(r["row_id"])
    assert t[C.RATINGS].apply(lambda s: s.between(1, 5)).all().all()
    assert t[C.BLOCKS].isin([0, 1]).all().all()
    per = t.groupby("row_id").size().reindex(r["row_id"]).values
    assert (per == r["n_tasks_done"].values).all()


def test_attributes_consistent_between_files():
    r, t = data.load_respondents(), data.load_tasks()
    m = t.merge(r[["row_id", "chronotype", "plan_style", "follow_plan", "sleep_hours"]], on="row_id", suffixes=("", "_r"))
    for c in ["chronotype", "plan_style", "follow_plan", "sleep_hours"]:
        assert (m[c].astype(str) == m[c + "_r"].astype(str)).all()


def test_excel_matches_csv():
    xl = C.DATA_DIR / "Mini_Survey_cleaned.xlsx"
    assert pd.read_excel(xl, sheet_name="respondents").equals(pd.read_csv(C.DATA_DIR / "respondents_clean.csv"))
    assert pd.read_excel(xl, sheet_name="tasks_long").equals(pd.read_csv(C.DATA_DIR / "tasks_long_clean.csv"))
