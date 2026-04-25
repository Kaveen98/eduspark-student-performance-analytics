# EduSpark: A Big Data Framework for Student Performance Analytics

EduSpark is a DS403.3 Big Data Programming coursework project for **Use Case 1: Student Performance Analytics System**. The repository contains a Windows-friendly local PySpark pipeline that:

1. starts from a small tracked base dataset,
2. generates a larger synthetic raw dataset,
3. preprocesses it into cleaned CSV folders, and
4. produces analytics outputs and notebook-ready visuals for reporting and viva discussion.

## Project Overview

The project models a student performance analytics workflow for academic decision-making. It uses PySpark DataFrames to clean, aggregate, and analyze student grades and attendance data at a scale that is much larger than the original reference dataset.
The current workflow is 5-file and CSV-only. It treats `enrollments.csv` as the academic backbone table, with `students.csv` and `courses.csv` as master/reference data and `grades.csv` plus `attendance.csv` as event data.

The main analytics outputs are:

- average marks by subject
- average marks by semester
- high-performing students
- low-performing students
- students at academic risk

The submission thresholds used in the final analytics are:

- high-performing threshold: `85`
- low-performing threshold: `60`
- fail threshold: `40`
- attendance-risk threshold: `65`

## Repository Structure

```text
.
|-- data/
|   |-- base/                      # tracked reference CSV files
|   |-- raw_expanded/              # generated raw CSV files (gitignored)
|   `-- cleaned/                   # generated cleaned CSV folders
|-- docs/                         # optional documentation folder when notes are present
|-- notebooks/
|   `-- eduspark_results_analysis.ipynb
|-- outputs/
|   `-- analytics/                 # generated CSV analytics folders and overview file
|-- scripts/
|   |-- generate_data.py
|   |-- preprocess.py
|   `-- analytics.py
|-- .gitignore
|-- README.md
`-- requirements.txt
```

## Technologies Used

- Python 3.14
- PySpark 4.1.1
- Pandas
- NumPy
- Matplotlib
- Java 21
- local Hadoop `winutils.exe` setup for Windows Spark execution
- VS Code / Jupyter notebook workflow for final visuals

## Dataset Workflow

The intended run order is:

1. `scripts/generate_data.py`
2. `scripts/preprocess.py`
3. `scripts/analytics.py`
4. `notebooks/eduspark_results_analysis.ipynb`

The workflow transforms the data as follows:

`data/base/*.csv -> data/raw_expanded/*.csv -> data/cleaned/*_csv -> outputs/analytics/*_csv -> notebook visuals`

The tracked base dataset and generated raw dataset now include all 5 CSV files:

- `students.csv`
- `courses.csv`
- `enrollments.csv`
- `grades.csv`
- `attendance.csv`

## Windows Setup

This project is designed to run locally on Windows with Java and Hadoop utilities available.

### 1. Create and activate the virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Confirm Java 21 is available

```powershell
java -version
```

The local environment used for this audit reported Java `21.0.10`.

### 3. Configure Hadoop / winutils for Windows

Place `winutils.exe` inside a Hadoop bin directory such as `C:\hadoop\bin`.

Two options are supported:

- set `HADOOP_HOME` in the terminal or system environment before running Spark
- pass `--hadoop-home C:\hadoop` to the Spark scripts directly

Optional environment setup example:

```powershell
$env:HADOOP_HOME = "C:\hadoop"
$env:PATH = "$env:HADOOP_HOME\bin;$env:PATH"
```

If `HADOOP_HOME` is not set, both Spark scripts will also try `C:\hadoop` automatically when that folder exists.

## Running the Full Pipeline

Use the commands below from the repository root.

### 1. Generate the expanded raw dataset

```powershell
.\.venv\Scripts\python.exe scripts\generate_data.py `
  --base-dir data\base `
  --output-dir data\raw_expanded `
  --students 10000 `
  --courses 150 `
  --seed 42
```

This step now writes `data/raw_expanded/enrollments.csv` alongside the other raw files. The current final successful run reflected in the repository outputs used `10,000` students and `150` courses.

### 2. Preprocess the raw dataset into cleaned CSV folders

```powershell
.\.venv\Scripts\python.exe scripts\preprocess.py `
  --input-dir data\raw_expanded `
  --output-dir data\cleaned `
  --hadoop-home C:\hadoop
```

This step writes cleaned CSV folders under `data/cleaned/`, including `students_csv`, `courses_csv`, `enrollments_csv`, `grades_csv`, `attendance_csv`, `grade_summary_csv`, `attendance_summary_csv`, and `student_performance_master_csv`.

### 3. Run the analytics pipeline

```powershell
.\.venv\Scripts\python.exe scripts\analytics.py `
  --input-dir data\cleaned `
  --output-dir outputs\analytics `
  --hadoop-home C:\hadoop
```

The analytics script defaults to the coursework thresholds listed earlier. Those defaults should be kept for the final submission.

The final analytics CSV outputs are written under `outputs/analytics/`:

- `average_marks_by_subject_csv/`
- `average_marks_by_semester_csv/`
- `high_performing_students_csv/`
- `low_performing_students_csv/`
- `at_risk_students_csv/`
- `subject_pass_fail_summary_csv/`
- `department_performance_summary_csv/`
- `top_10_students_csv/`
- `bottom_10_students_csv/`
- `analytics_overview.csv`

## Notebook Purpose

`notebooks/eduspark_results_analysis.ipynb` is the presentation/report notebook. It reads the final files inside `outputs/analytics/` and produces:

- summary tables
- top-subject and semester trend charts
- classification counts
- example student profile tables
- academic risk factor visuals

Run the notebook **after** the analytics script has completed.

## Current Final Results

The checked local outputs in `outputs/analytics/` currently report:

- total students: `10,000`
- total courses: `150`
- total enrollments: `240,927`
- total grade summary records: `240,843`
- total attendance summary records: `240,927`
- high-performing students: `2,521`
- low-performing students: `1`
- at-risk students: `6,256`
- subject summaries: `150`
- semester summaries: `8`

The semester-level averages are stable across all eight periods from 2022 Semester 1 to 2025 Semester 2, ranging from `80.30` to `80.39`.

The highest subject averages in the current outputs include:

- `COURSE91` - Open-source Zero-defect Paradigm: `81.01`
- `COURSE2` - Course 2: `81.00`
- `COURSE120` - Inverse Web-enabled Infrastructure: `80.78`
- `COURSE20` - Course 20: `80.74`
- `COURSE124` - Fundamental Empowering Hierarchy: `80.73`

The at-risk population in the current final run is driven almost entirely by attendance. The checked `at_risk_students` output contains `6,255` students flagged for `Low attendance` only, and `1` student flagged for both low score and low attendance.

## Reproducibility Notes

- The generated raw data and cleaned CSV folders can be recreated from the scripts.
- The default seed in `generate_data.py` is `42`, which helps keep the synthetic data generation reproducible.
- The notebook expects the output folder structure produced by `scripts/analytics.py`.

## Limitations

- The project uses a simulated dataset expanded from a smaller base dataset.
- Output distributions depend on the data generation rules and seed.
- Low-performing students are relatively rare in the current generated dataset.
- The local workflow assumes Windows-compatible Java and Hadoop utility setup.
- Spark outputs are written as folders containing part files, which is normal for Spark.

