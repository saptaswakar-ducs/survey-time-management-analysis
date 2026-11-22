"""Paths, labels and category orderings shared by the notebook, tests and scripts."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = ROOT / "data" / "processed"
FIG_DIR = ROOT / "figures"
TABLE_DIR = ROOT / "results" / "tables"

SEED = 20260122          # one seed for every random procedure (bootstrap / permutation)
ALPHA = 0.05

# --- category orderings (so tables and plots are in a meaningful order) ---------------
LEVEL_ORDER = ["Undergraduate Year 1-2", "Undergraduate Year 3+", "Master's", "PhD / Research scholar"]
AGE_ORDER = ["18-20", "21-23", "24-26", "27 or above"]
LIVING_ORDER = ["With family", "Hostel", "Rented flat / PG"]
CHRONO_ORDER = ["Morning person", "No clear preference", "Evening / night person"]
PLAN_ORDER = ["I do not plan", "Mental plan only", "Written to-do list", "Calendar / planner app", "Time-blocking"]
PEAK_ORDER = ["Morning (8-12)", "Afternoon (12-4)", "Evening (4-8)", "Night (8-12)", "Late night (12-4)", "No difference"]
APP_ORDER = ["Definitely not", "Probably not", "Not sure", "Probably", "Definitely"]
APP_SCORE = {k: i + 1 for i, k in enumerate(APP_ORDER)}          # 1 (definitely not) .. 5 (definitely)

# --- column groups -----------------------------------------------------------------------
BLOCKS = ["block_early_morning", "block_morning", "block_afternoon",
          "block_evening", "block_night", "block_late_night"]
BLOCK_LABELS = ["Early morning", "Morning", "Afternoon", "Evening", "Night", "Late night"]

REASONS = {
    "reason_phone_social_media": "Phone / social media",
    "reason_procrastination": "Procrastination",
    "reason_requests_from_others": "Requests from others",
    "reason_poor_time_estimation": "Poor time estimation",
    "reason_unexpected_tasks": "Unexpected tasks",
    "reason_low_energy_tiredness": "Low energy / tiredness",
    "reason_health_issues": "Health issues",
    "reason_other": "Other",
}
DECIDE = {
    "decide_deadline_urgency": "Deadline / urgency",
    "decide_whenever_i_am_free": "Whenever I am free",
    "decide_my_energy_level": "My energy level",
    "decide_my_mood": "My mood",
    "decide_habit_routine": "Habit / routine",
    "decide_availability_of_other_people": "Others' availability",
    "decide_other": "Other",
}
TASK_LABELS = {
    "assign": "Assignments", "chores": "Chores", "class": "Classes / labs", "commute": "Commute",
    "exercise": "Exercise", "leisure": "Leisure", "meals": "Meals", "sleep": "Sleep", "study": "Self-study",
    "work": "Work / clubs",
}
RATINGS = ["importance", "energy", "productivity", "satisfaction", "completed", "postponed", "interruptions"]
RESP_NUMERIC = ["follow_plan", "reschedule_freq", "overall_productivity", "focus_hours",
                "wake_h", "bed_h_night", "sleep_hours", "n_tasks_done"]
