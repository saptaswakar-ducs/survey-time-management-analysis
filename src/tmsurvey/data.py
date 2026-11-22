"""Loading and light preparation of the three cleaned survey files (no re-cleaning is done here)."""
import numpy as np
import pandas as pd
from . import config as C


def _ordered(s: pd.Series, order) -> pd.Series:
    return pd.Categorical(s, categories=order, ordered=True)


def load_respondents(path=None) -> pd.DataFrame:
    """One row per respondent (n = 39)."""
    r = pd.read_csv(path or C.DATA_DIR / "respondents_clean.csv")
    r["level"] = _ordered(r["level"], C.LEVEL_ORDER)
    r["age_group"] = _ordered(r["age_group"], C.AGE_ORDER)
    r["living"] = _ordered(r["living"], C.LIVING_ORDER)
    r["chronotype"] = _ordered(r["chronotype"], C.CHRONO_ORDER)
    r["plan_style"] = _ordered(r["plan_style"], C.PLAN_ORDER)
    r["peak_time"] = _ordered(r["peak_time"], C.PEAK_ORDER)
    r["app_interest"] = _ordered(r["app_interest"], C.APP_ORDER)
    r["app_score"] = r["app_interest"].astype(str).map(C.APP_SCORE)
    r["flagged"] = r["sleep_outlier"] | r["straightlined"]
    return r


def load_tasks(path=None) -> pd.DataFrame:
    """One row per respondent x task (n = 301 rows, 39 respondents)."""
    t = pd.read_csv(path or C.DATA_DIR / "tasks_long_clean.csv")
    t["level"] = _ordered(t["level"], C.LEVEL_ORDER)
    t["chronotype"] = _ordered(t["chronotype"], C.CHRONO_ORDER)
    t["plan_style"] = _ordered(t["plan_style"], C.PLAN_ORDER)
    t["task_label"] = t["task"].map(C.TASK_LABELS)
    t["morning_sched"] = ((t["block_early_morning"] + t["block_morning"]) > 0).astype(int)
    t["night_sched"] = ((t["block_night"] + t["block_late_night"]) > 0).astype(int)
    t["n_blocks"] = t[C.BLOCKS].sum(axis=1)
    t["log_duration"] = np.log(t["duration_min"])
    return t


def load_cleaning_report(path=None) -> pd.DataFrame:
    p = path or C.DATA_DIR / "Mini_Survey_cleaned.xlsx"
    rep = pd.read_excel(p, sheet_name="cleaning_report")
    rep.columns = ["item", "value"]
    return rep
