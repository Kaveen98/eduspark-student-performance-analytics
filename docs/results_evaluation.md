# EduSpark Results and Evaluation

## Final Analytics Configuration

The final analytics thresholds used in the EduSpark system were:

- High-performing student threshold: 85
- Low-performing student threshold: 60
- Fail threshold per course: 40
- Attendance risk threshold: 65

These thresholds were kept fixed for the final coursework outputs.

## Dataset Size After Preprocessing

The local final run used for the current notebook and output review reported:

- Students: 10,000
- Courses: 100
- Cleaned grade records: 696,034
- Cleaned attendance records: 1,853,377
- Grade summary records: 239,602
- Attendance summary records: 239,685
- Master performance records: 239,685

This confirms that the project operated on a large, multi-table dataset covering several academic periods.

## Main Results

### 1. Average Marks by Subject

The system produced subject-level summaries for 100 courses.

The highest subject averages in the checked outputs were:

- COURSE98 - Computer Science Course 98: 80.70
- COURSE89 - Computer Science Course 89: 80.67
- COURSE56 - Mathematics Course 56: 80.62
- COURSE72 - Mathematics Course 72: 80.60
- COURSE62 - Computer Science Course 62: 80.54

This suggests that Computer Science and Mathematics courses sit near the top of the current generated distribution.

### 2. Average Marks by Semester

The system generated results for all eight semester periods from 2022 to 2025.

Semester averages were:

- 2022 Semester 1: 80.15
- 2022 Semester 2: 80.20
- 2023 Semester 1: 80.18
- 2023 Semester 2: 80.20
- 2024 Semester 1: 80.22
- 2024 Semester 2: 80.16
- 2025 Semester 1: 80.24
- 2025 Semester 2: 80.26

The averages remain stable across all semesters, with only small fluctuations.

### 3. Student Classification

The current output counts were:

- High-performing students: 2,467
- Low-performing students: 4
- At-risk students: 1,381

High-performing students are those with an overall average score of at least 85. Low-performing students are those with an overall average score below 60.

A student is flagged as academically at risk when one or more of the following conditions are met:

- overall average score below 60
- overall attendance percentage below 65
- two or more failed courses, where a failed course average is below 40

The checked sample rows show that low attendance is the most common contributor to the at-risk classification.

## Interpretation of Findings

The EduSpark pipeline successfully produced all required outputs for the Student Performance Analytics use case.

The final outputs show that:

- academic performance is broadly consistent across semesters
- subject-level differences are visible but not extreme
- a meaningful group of high-performing students can be identified
- the at-risk output provides a concrete intervention-oriented view of lower attendance and weaker academic performance

## Big Data Processing Patterns Used

The solution demonstrates several core big data processing patterns:

- filtering for student classification groups
- aggregation for subject, semester, and student summaries
- sorting for ranked outputs such as top and bottom students
- joins during preprocessing and master-table construction

## Limitations

- the final dataset is simulated from a smaller tracked base dataset
- the resulting performance distribution depends on the generation assumptions and random seed
- low-performing students are relatively rare in the current generated outputs
- the workflow is local Spark on Windows rather than a distributed cluster deployment

## Conclusion

EduSpark demonstrates a practical Spark-based student performance analytics workflow that supports subject analysis, semester analysis, student classification, and academic risk detection. The current outputs align with the project objectives for Use Case 1 and are suitable for coursework reporting and viva discussion.
