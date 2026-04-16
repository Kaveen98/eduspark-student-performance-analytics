# EduSpark Dataset Plan

## Base Dataset
The original base dataset consists of 4 CSV files:
- students.csv
- courses.csv
- grades.csv
- attendance.csv

These files will be used as the reference/sample dataset.

## Expanded Raw Dataset
A larger simulated version of the 4-table dataset will be generated and stored in:
- data/raw_expanded/

This expanded dataset will be the main raw project dataset used for preprocessing and analytics.

## Target Scale
Planned target size:
- students: 10,000 rows
- courses: 100 rows
- grades: 80,000+ rows
- attendance: 150,000+ rows

## Time Coverage
The expanded dataset will cover multiple academic periods:
- Year 2022
- Year 2023
- Year 2024
- Year 2025

Semesters:
- Semester 1
- Semester 2

## Required Analytics Support
The final cleaned dataset must support:
- average marks by subject
- average marks by semester
- high-performing students
- low-performing students
- students at academic risk

## Planned Data Issues to Inject into Raw Expanded Data
Realistic issues will be intentionally introduced into the expanded raw dataset:
- missing score values in a small percentage of grades
- missing attendance status in a small percentage of attendance records
- duplicate rows in grades and attendance
- inconsistent text formatting (e.g. Present/present/PRESENT)
- some invalid or out-of-range score values
- some inconsistent or missing non-key descriptive fields

Important:
- StudentID and CourseID should remain mostly valid
- key relationships should not be heavily damaged

## Cleaning and Preprocessing Goals
The preprocessing stage will:
- standardize column names
- remove duplicates
- parse dates
- derive Year and Semester
- validate score ranges
- normalize attendance values
- calculate attendance percentage per student/course/semester
- create summarized student performance tables

## Final Workflow
Base dataset -> Expanded raw dataset -> Cleaned dataset -> Spark analytics outputs

