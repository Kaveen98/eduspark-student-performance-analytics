# EduSpark Team Roles

## Project Title
**EduSpark: A Big Data Framework for Student Performance Analytics**

## Module
**DS403.3 – Big Data Programming**

## Use Case
**Use Case 1 – Student Performance Analytics System**

## Team Contribution Plan

| Member Name | Role | Main Files / Areas | Main Responsibilities |
|---|---|---|---|
| Member 1 | Data Generation Lead | `scripts/generate_data.py`, `docs/dataset_plan.md`, `docs/generation_rules.md` | Expand the original 4-table dataset into a larger raw dataset, inject realistic data issues, document dataset structure and generation logic |
| Member 2 | Preprocessing Lead | `scripts/preprocess.py`, `data/cleaned/`, preprocessing documentation | Build the Spark cleaning pipeline, handle missing values/duplicates/invalid dates and scores, derive `year` and `semester`, generate cleaned summary tables |
| Member 3 | Analytics Lead | `scripts/analytics.py`, `outputs/analytics/` | Implement Spark analytics, calculate average marks by subject and semester, identify high-performing and low-performing students, detect at-risk students, maintain final threshold logic |
| Member 4 | Architecture / Setup / Repository Lead | `README.md`, `.gitignore`, `requirements.txt`, setup docs, architecture diagram, submission docs | Document the environment setup, maintain Windows/PySpark/Java/Hadoop instructions, explain project architecture, keep the repository organized and submission-ready |
| Member 5 | Results / Evaluation / Presentation Lead | `notebooks/eduspark_results_analysis.ipynb`, `docs/results_evaluation.md`, presentation materials | Create report-ready tables and charts, interpret final results, prepare evaluation notes, support report writing, prepare presentation slides and viva explanation flow |

## Detailed Role Breakdown

### Member 1 – Data Generation Lead
**Files / Areas**
- `scripts/generate_data.py`
- `docs/dataset_plan.md`
- `docs/generation_rules.md`

**Responsibilities**
- Understand the original 4-table base dataset
- Generate the expanded raw dataset
- Control dataset scale, years, semesters, and quality issues
- Document how the base dataset was transformed into a large raw dataset

**Suggested commit areas**
- data generation logic
- synthetic record expansion
- raw data issue injection
- dataset documentation

**Example commit messages**
- `Add expanded raw dataset generation pipeline`
- `Refine synthetic student performance data generation`
- `Document dataset plan and generation rules`

---

### Member 2 – Preprocessing Lead
**Files / Areas**
- `scripts/preprocess.py`
- `data/cleaned/`
- preprocessing explanation in docs/report

**Responsibilities**
- Standardize column names and text fields
- Handle missing values, duplicates, invalid dates, and invalid scores
- Derive `year` and `semester`
- Build cleaned tables and summary tables
- Explain preprocessing decisions clearly in the report

**Suggested commit areas**
- cleaning logic
- date parsing
- missing-value handling
- summary-table generation
- cleaned data documentation

**Example commit messages**
- `Add Spark preprocessing pipeline for EduSpark`
- `Handle invalid dates and missing values in preprocessing`
- `Generate cleaned summary parquet outputs`

---

### Member 3 – Analytics Lead
**Files / Areas**
- `scripts/analytics.py`
- `outputs/analytics/`

**Responsibilities**
- Calculate average marks by subject
- Calculate average marks by semester
- Identify high-performing students
- Identify low-performing students
- Detect at-risk students
- Maintain the final thresholds:
  - high-performing threshold = 85
  - low-performing threshold = 60
  - fail threshold = 40
  - attendance-risk threshold = 65
- Explain Spark DataFrame operations and design patterns used

**Suggested commit areas**
- analytics calculations
- classification logic
- threshold tuning
- output export logic
- design pattern explanation

**Example commit messages**
- `Add subject and semester analytics outputs`
- `Implement student classification and academic risk detection`
- `Set final EduSpark analytics thresholds`

---

### Member 4 – Architecture / Setup / Repository Lead
**Files / Areas**
- `README.md`
- `.gitignore`
- `requirements.txt`
- `docs/submission_readiness_check.md`
- `docs/current_project_status.md`
- architecture diagram
- Windows setup notes

**Responsibilities**
- Document project overview and run instructions
- Document Windows setup:
  - Python virtual environment
  - Java 21
  - `HADOOP_HOME`
  - `winutils.exe`
- Explain repository structure
- Prepare architecture diagram
- Check final submission readiness

**Suggested commit areas**
- README
- setup instructions
- architecture notes
- environment documentation
- submission-readiness docs

**Example commit messages**
- `Add project README with Windows setup instructions`
- `Document project structure and execution order`
- `Add submission readiness and current project status notes`

---

### Member 5 – Results / Evaluation / Presentation Lead
**Files / Areas**
- `notebooks/eduspark_results_analysis.ipynb`
- `docs/results_evaluation.md`
- report visuals
- presentation slides

**Responsibilities**
- Build final charts and tables from analytics outputs
- Interpret subject, semester, classification, and risk results
- Prepare notebook visuals for the report
- Draft evaluation, discussion, and limitations content
- Support final presentation and viva preparation

**Suggested commit areas**
- notebook tables/charts
- evaluation notes
- presentation visuals
- results interpretation

**Example commit messages**
- `Add results analysis notebook for EduSpark`
- `Refine charts for subject semester and risk analysis`
- `Add results and evaluation notes for report`

---

## Shared Responsibilities for All Members
- All members contribute to the final report
- All members must have meaningful Git commits
- All members participate in the presentation and viva
- All members should understand the complete pipeline, not only their own part
- All members should be able to explain:
  - dataset generation
  - preprocessing
  - analytics logic
  - final outputs
  - individual contribution

## Final Contribution Evidence
Each member should ideally have:
- 3–6 meaningful commits in their main area
- at least 1 documentation/review-related commit
- clear commit messages that describe real work done

## Recommended Branch Ownership
- Member 1 → `feat/data-generation`
- Member 2 → `feat/preprocessing`
- Member 3 → `feat/spark-analytics`
- Member 4 → `feat/readme-architecture`
- Member 5 → `feat/results-notebook`

## Final Report Contribution Table Format
| Student Name | Role | Contribution |
|---|---|---|
| Member 1 | Data Generation Lead | Expanded the base dataset and documented dataset generation workflow |
| Member 2 | Preprocessing Lead | Built the Spark cleaning pipeline and generated cleaned summary tables |
| Member 3 | Analytics Lead | Implemented Spark analytics, thresholds, and student classification logic |
| Member 4 | Architecture / Setup Lead | Prepared setup guide, architecture explanation, and repository/submission documentation |
| Member 5 | Results / Presentation Lead | Created notebook visuals, evaluation notes, and presentation materials |
