# Data dictionary

Three cleaned files in `data/processed/`. `Mini_Survey_cleaned.xlsx` contains the same two tables as the CSVs
(sheets `respondents`, `tasks_long`; a test asserts they are identical) plus a `cleaning_report` sheet.
**No re-cleaning is done in this project.** Variable meanings marked † were inferred from names/values and should be checked against the original questionnaire.

## `respondents_clean.csv` (39 rows, one per respondent)
| Variable | Type | Description |
|---|---|---|
| `row_id` | int | Respondent key (joins to `tasks_long_clean.csv`). Not consecutive (ids start at 2). |
| `age_group` | cat | 18-20, 21-23, 24-26, 27 or above |
| `level` | cat | Undergraduate Year 1-2 / Year 3+ / Master's / PhD-Research scholar |
| `living` | cat | With family / Hostel / Rented flat-PG |
| `plan_style` | cat | I do not plan, Mental plan only, Written to-do list, Calendar/planner app, Time-blocking |
| `chronotype` | cat | Morning person / No clear preference / Evening-night person (self-reported) |
| `follow_plan` | 1-5 | How closely the respondent follows their own plan † (higher = more) |
| `reschedule_freq` | 1-5 | How often plans are rescheduled † (higher = more often); observed 2-5 |
| `overall_productivity` | 1-5 | Overall self-rated productivity † |
| `focus_hours` | num | Focused hours per day †; **only 13/39 answered** (not used for inference) |
| `wake_h` | hours | Usual wake time, decimal hours (7.5 = 07:30) |
| `bed_h_night` | hours | Usual bed time on a 24 h+ scale (24.5 = 00:30, 26 = 02:00) |
| `sleep_hours` | num | Usual sleep duration (hours) |
| `peak_time` | cat | Self-reported peak time of day (Morning 8-12 ... Late night 12-4, No difference) |
| `schedule_first` | cat | Which kind of task is scheduled first |
| `most_postponed` | cat | Task category postponed most often |
| `wish_better` | cat | Task category the respondent most wants to manage better |
| `app_interest` | cat | Would use a planning app? Definitely not ... Definitely (coded 1-5 as `app_score` in code) |
| `sleep_outlier`, `straightlined` | bool | Quality flags from the cleaning step (2 respondents each; no overlap). `flagged` = either. |
| `reason_*` (8 columns) | 0/1 | Multiple-response: reasons plans fail (unexpected tasks, procrastination, low energy, phone/social media, poor time estimation, requests from others, health, other) |
| `decide_*` (7 columns) | 0/1 | Multiple-response: what decides when a task is done (deadline/urgency, energy, mood, others' availability, habit/routine, whenever free, other) |
| `n_tasks_done` | int | Number of task types the respondent reported on (= rows in `tasks_long`) |

## `tasks_long_clean.csv` (301 rows, one per respondent x task)
| Variable | Type | Description |
|---|---|---|
| `row_id` | int | Respondent key |
| `task` | cat | assign, chores, class, commute, exercise, leisure, meals, sleep, study, work |
| `block_early_morning` ... `block_late_night` | 0/1 | Day blocks in which the task is done (six blocks; **not mutually exclusive**) |
| `duration_min` | int | Task duration in minutes † |
| `times_per_week` | num | Frequency per week †; **51% missing**, structurally (not used for inference) |
| `flexibility`, `deadline` | 0-2 | Ordinal codes (label meanings not documented in the files †) |
| `importance`, `energy`, `productivity`, `satisfaction`, `completed`, `postponed`, `interruptions` | 1-5 | Ratings of the task |
| `level`, `chronotype`, `plan_style`, `follow_plan`, `sleep_hours` | | Respondent attributes repeated from the respondent file (a test checks they agree) |

## `cleaning_report` sheet
Counts from the upstream cleaning: 40 raw rows, 1 exact duplicate dropped, 1,013 "don't do this" cells, 70 stray cells removed, 3 mixed Q13 answers fixed, 3 cells imputed, 2 straight-liners flagged.

## Derived variables created in code (`src/tmsurvey/data.py`)
`app_score` (1-5), `flagged`, `task_label`, `morning_sched` (early-morning or morning block), `night_sched` (night or late-night block), `n_blocks`, `log_duration`.
