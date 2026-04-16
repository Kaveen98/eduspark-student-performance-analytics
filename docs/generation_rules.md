# EduSpark Data Expansion Rules

## Goal
Generate a larger raw student performance dataset from the base 4-table dataset.

The expanded dataset will be stored in:
- data/raw_expanded/students.csv
- data/raw_expanded/courses.csv
- data/raw_expanded/grades.csv
- data/raw_expanded/attendance.csv

## Base Source
Reference files:
- data/base/students.csv
- data/base/courses.csv
- data/base/grades.csv
- data/base/attendance.csv

## Target Size
- students: 10,000 rows
- courses: 100 rows
- grades: 80,000 to 120,000 rows
- attendance: 150,000 to 250,000 rows

## Time Coverage
Years:
- 2022
- 2023
- 2024
- 2025

Semester rules:
- Semester 1 = January to June
- Semester 2 = July to December

## Generation Logic

### Students
- Expand from base student profiles
- Keep core demographic structure realistic
- Create unique StudentID values
- Preserve meaningful distributions for department, gender, GPA range, etc.

### Courses
- Expand course list moderately
- Keep unique CourseID values
- Preserve department and credits structure

### Grades
- Generate multiple grade records per student across multiple courses and semesters
- Keep score values mostly realistic
- Include assignment/exam style categories if present in the base dataset
- Each record should include:
  - StudentID
  - CourseID
  - Date
  - Score
  - AssignmentType

### Attendance
- Generate attendance records by date for student-course combinations
- Attendance should contain many records per student/course across semesters
- Each record should include:
  - StudentID
  - CourseID
  - Date
  - AttendanceStatus

## Data Issues to Inject

### Grades
- around 2% missing Score values
- around 1% duplicate rows
- around 1% invalid/out-of-range Score values
- small amount of inconsistent AssignmentType text formatting

### Attendance
- around 2% missing AttendanceStatus
- around 1% duplicate rows
- inconsistent AttendanceStatus values such as:
  - Present
  - present
  - PRESENT
  - Absent
  - absent

### Students / Courses
- a very small amount of missing or inconsistent non-key text fields
- do not heavily damage StudentID or CourseID

## Important Constraints
- StudentID must remain usable for joins
- CourseID must remain usable for joins
- dates must span multiple years and semesters
- the expanded dataset must support:
  - average marks by subject
  - average marks by semester
  - high-performing students
  - low-performing students
  - at-risk students

## Planned Preprocessing After Generation
- standardize column names
- remove duplicates
- normalize text values
- parse dates
- derive Year and Semester
- fix or remove invalid scores
- calculate attendance percentage
- build summary tables for analytics

