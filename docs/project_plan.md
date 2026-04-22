# EduSpark Project Plan

## Coursework Context

- Module: `DS403.3 Big Data Programming`
- Project title: `EduSpark: A Big Data Framework for Student Performance Analytics`
- Use case: `Student Performance Analytics System`

## Objective

Build a local Spark-based pipeline that can generate, preprocess, and analyze student performance data on Windows while remaining easy to explain during coursework review and viva discussion.

## Planned Workflow

1. Keep a small tracked reference dataset in `data/base/`.
2. Generate a large synthetic raw dataset with `scripts/generate_data.py`.
3. Clean and standardize the raw data with `scripts/preprocess.py`.
4. Produce final analytics outputs with `scripts/analytics.py`.
5. Use `notebooks/eduspark_results_analysis.ipynb` for the final report and presentation visuals.

## Expected Deliverables

- working data generation script
- working Spark preprocessing script
- working Spark analytics script
- notebook-based result presentation
- clear setup and run documentation
- lecturer-friendly summary notes in `docs/`
