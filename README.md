# EduSpark: A Big Data Framework for Student Performance Analytics

EduSpark is a DS403.3 Big Data Programming coursework project for **Use Case 1: Student Performance Analytics System**. The repository contains a Windows-friendly local PySpark pipeline that:

1. starts from a small tracked base dataset,
2. generates a larger synthetic raw dataset,
3. preprocesses it into cleaned Parquet tables, and
4. produces analytics outputs and notebook-ready visuals for reporting and viva discussion.

## Project Overview

The project models a student performance analytics workflow for academic decision-making. It uses PySpark DataFrames to clean, aggregate, and analyze student grades and attendance data at a scale that is much larger than the original reference dataset.

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
|   `-- cleaned/                   # generated cleaned parquet files (gitignored)
|-- docs/
|   |-- dataset_plan.md
|   |-- generation_rules.md
|   |-- project_plan.md
|   |-- results_evaluation.md
|   |-- submission_readiness_check.md
|   `-- team_roles.md
|-- notebooks/
|   `-- eduspark_results_analysis.ipynb
|-- outputs/
|   `-- analytics/                 # generated CSV/parquet analytics outputs (gitignored)
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

`data/base/*.csv -> data/raw_expanded/*.csv -> data/cleaned/* -> outputs/analytics/* -> notebook visuals`

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
  --courses 100 `
  --seed 42
```

### 2. Preprocess the raw dataset into cleaned parquet files

```powershell
.\.venv\Scripts\python.exe scripts\preprocess.py `
  --input-dir data\raw_expanded `
  --output-dir data\cleaned `
  --hadoop-home C:\hadoop
```

### 3. Run the analytics pipeline

```powershell
.\.venv\Scripts\python.exe scripts\analytics.py `
  --input-dir data\cleaned `
  --output-dir outputs\analytics `
  --hadoop-home C:\hadoop
```

The analytics script defaults to the coursework thresholds listed earlier. Those defaults should be kept for the final submission.

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
- total courses: `100`
- total grade summary records: `239,602`
- total attendance summary records: `239,685`
- high-performing students: `2,467`
- low-performing students: `4`
- at-risk students: `1,381`

The semester-level averages are stable across all eight periods from 2022 Semester 1 to 2025 Semester 2, ranging from `80.15` to `80.26`.

The highest subject averages in the current outputs include:

- `COURSE98` - Computer Science Course 98: `80.70`
- `COURSE89` - Computer Science Course 89: `80.67`
- `COURSE56` - Mathematics Course 56: `80.62`
- `COURSE72` - Mathematics Course 72: `80.60`
- `COURSE62` - Computer Science Course 62: `80.54`

## Reproducibility Notes

- The generated raw data, cleaned parquet files, and analytics outputs are intentionally gitignored because they can be recreated from the scripts.
- The default seed in `generate_data.py` is `42`, which helps keep the synthetic data generation reproducible.
- The notebook expects the output folder structure produced by `scripts/analytics.py`.
- Supporting notes for lecturers and viva review are available in [docs/results_evaluation.md](docs/results_evaluation.md) and [docs/submission_readiness_check.md](docs/submission_readiness_check.md).

## Limitations

- The project uses a simulated dataset expanded from a smaller base dataset.
- Output distributions depend on the data generation rules and seed.
- Low-performing students are relatively rare in the current generated dataset.
- The local workflow assumes Windows-compatible Java and Hadoop utility setup.
- Spark outputs are written as folders containing part files, which is normal for Spark.

## Submission Notes

For the cleanest submission package:

- include the source files, docs, and notebook
- regenerate outputs if the lecturer expects a fresh run demonstration
- keep the default analytics thresholds unchanged
- use the notebook only after the analytics outputs exist
- review [docs/submission_readiness_check.md](docs/submission_readiness_check.md) before final packaging
