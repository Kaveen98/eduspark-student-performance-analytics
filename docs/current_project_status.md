# Current Project Status

Scope of this status note:
- Lightweight repository audit only.
- No code changes.
- No full Spark rerun.
- Based on repository structure, `README.md`, `requirements.txt`, `.gitignore`, `docs/`, `scripts/`, and the notebook file.

## 1. Current Repo Structure

Important top-level folders and files:
- `data/base/`: tracked source CSV files used as the project starting point.
- `data/raw_expanded/`: generated expanded raw CSV files expected from `scripts/generate_data.py`.
- `data/cleaned/`: generated cleaned Parquet outputs expected from `scripts/preprocess.py`.
- `data/raw/` and `data/processed/`: present in the repo structure, but not referenced by the current README run order or the current pipeline scripts. These are potentially leftover or placeholder folders and may confuse reviewers.
- `scripts/`: core pipeline implementation.
- `notebooks/`: final results notebook.
- `outputs/analytics/`: expected final analytics outputs from `scripts/analytics.py`.
- `outputs/verification/`: present in the structure, but not described in the README and not referenced by the current scripts. Its role is unclear from this audit.
- `docs/`: planning, evaluation, submission, and team notes.
- `report/` and `diagrams/`: folders exist, but no tracked files were visible during this audit. They currently read as placeholders.
- `README.md`: main project guide.
- `requirements.txt`: Python dependency list.
- `.gitignore`: ignore rules for environments and generated artifacts.

## 2. Purpose Of Each Major File

Core files:
- `README.md`: explains project purpose, Windows setup, pipeline order, notebook role, thresholds, and submission notes.
- `requirements.txt`: lists direct Python dependencies only: `matplotlib`, `numpy`, `pandas`, and `pyspark`.
- `.gitignore`: excludes virtual environments, notebook checkpoints, caches, generated data folders, analytics outputs, checksum files, and archive files.

Scripts:
- `scripts/generate_data.py`: expands the base CSV dataset into a larger synthetic raw dataset and injects controlled data-quality issues for later cleaning.
- `scripts/preprocess.py`: runs the Spark cleaning stage, standardizes fields, derives `year` and `semester`, creates summaries, and writes cleaned Parquet tables.
- `scripts/analytics.py`: runs the Spark analytics stage, applies the final thresholds, produces required analytics outputs, and writes both CSV and Parquet result sets.

Docs:
- `docs/dataset_plan.md`: describes the planned dataset scale, time coverage, and intended cleaning goals.
- `docs/generation_rules.md`: describes how synthetic records and raw-data issues should be generated.
- `docs/project_plan.md`: short coursework-level overview of the intended workflow and deliverables.
- `docs/results_evaluation.md`: narrative summary of the intended final analytics findings and project interpretation.
- `docs/submission_readiness_check.md`: checklist-style submission note and readiness claim.
- `docs/team_roles.md`: placeholder for team/member responsibilities; still needs real names if this is a group submission.

Notebook:
- `notebooks/eduspark_results_analysis.ipynb`: presentation/report notebook that loads analytics outputs, displays summary tables, and builds charts for subject performance, semester trends, student classification, and academic risk.

## 3. Current Pipeline Status

The intended pipeline is complete in structure and consistent across the scripts and README:
1. `scripts/generate_data.py`
2. `scripts/preprocess.py`
3. `scripts/analytics.py`
4. `notebooks/eduspark_results_analysis.ipynb`

Current status by stage:
- Data generation stage: implemented and parameterized. Default target size is `10,000` students, `100` courses, and seed `42`.
- Preprocessing stage: implemented. Includes Windows Hadoop helper logic, CSV input loading, standardization, summary-table creation, and Parquet writing.
- Analytics stage: implemented. Uses the final default thresholds below and writes required output folders plus extra ranking and summary outputs.
- Notebook stage: implemented. It checks that analytics outputs exist before running and reads Spark CSV output folders with pandas.

Final thresholds remain unchanged in the current code and notebook:
- high-performing threshold = `85`
- low-performing threshold = `60`
- fail threshold = `40`
- attendance-risk threshold = `65`

Status judgment:
- The pipeline is code-complete and coherent for submission.
- This audit did not rerun Spark jobs, so execution success was not revalidated here.

## 4. Inputs And Outputs

Source-of-truth inputs:
- `data/base/students.csv`
- `data/base/courses.csv`
- `data/base/grades.csv`
- `data/base/attendance.csv`

Generated intermediate outputs:
- `data/raw_expanded/students.csv`
- `data/raw_expanded/courses.csv`
- `data/raw_expanded/grades.csv`
- `data/raw_expanded/attendance.csv`
- `data/cleaned/students/`
- `data/cleaned/courses/`
- `data/cleaned/grades/`
- `data/cleaned/attendance/`
- `data/cleaned/grade_summary/`
- `data/cleaned/attendance_summary/`
- `data/cleaned/student_performance_master/`

Final analytics outputs expected from the current scripts:
- `outputs/analytics/average_marks_by_subject_csv/`
- `outputs/analytics/average_marks_by_semester_csv/`
- `outputs/analytics/high_performing_students_csv/`
- `outputs/analytics/low_performing_students_csv/`
- `outputs/analytics/at_risk_students_csv/`
- `outputs/analytics/subject_pass_fail_summary_csv/`
- `outputs/analytics/department_performance_summary_csv/`
- `outputs/analytics/top_10_students_csv/`
- `outputs/analytics/bottom_10_students_csv/`
- `outputs/analytics/analytics_overview.csv`
- matching Parquet versions for all Spark-generated analytics tables

Notebook consumption:
- The notebook reads from `outputs/analytics/` and depends on those files already existing.

## 5. Documentation Status

Current documentation quality:
- `README.md` is the strongest document in the repo. It covers setup, run order, thresholds, notebook purpose, reproducibility, and submission notes.
- `docs/dataset_plan.md` and `docs/generation_rules.md` align well with the generation and preprocessing scripts.
- `docs/project_plan.md` is short but adequate as a coursework overview.
- `docs/results_evaluation.md` is useful for report writing and viva preparation, but it is still a narrative document, not a substitute for rerunning or rechecking outputs.
- `docs/submission_readiness_check.md` is useful as a checklist, but its `Ready` verdict should be treated as a documentation claim unless the final machine is checked.
- `docs/team_roles.md` is not complete for final submission if group member names still need to be inserted.

Overall documentation status:
- Good and mostly submission-oriented.
- One incomplete item remains: team-role ownership details.

## 6. Submission-Readiness Verdict

**Mostly ready**

Reasons:
- Core scripts are present and logically complete.
- The run order is documented clearly.
- Thresholds are consistent across README, notebook, and analytics script.
- The notebook is structured as a final presentation/report artifact.
- Submission-focused supporting docs already exist.

Reasons it is not marked fully ready from this audit alone:
- No Spark rerun was performed in this lightweight check.
- `docs/team_roles.md` still appears to be a placeholder.
- Some folders are present but not clearly explained in the current documentation: `data/raw/`, `data/processed/`, `outputs/verification/`, `report/`, and `diagrams/`.

## 7. Manual Checks Still Needed

- Confirm whether `docs/team_roles.md` needs actual member names and role ownership before submission.
- Confirm the final submission package includes only folders that are meaningful to the lecturer; otherwise explain or omit unclear placeholder folders.
- On the final Windows machine, verify Java, `HADOOP_HOME`, and `winutils.exe` setup before demonstration.
- Open the notebook once against the intended final analytics outputs and confirm all cells run cleanly.
- Decide whether generated analytics outputs will be bundled or regenerated during demonstration, and keep that choice consistent with the README/submission notes.
