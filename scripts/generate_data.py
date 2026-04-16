from pathlib import Path
import argparse
import calendar

import numpy as np
import pandas as pd


YEARS = [2022, 2023, 2024, 2025]
SEMESTER_MONTHS = {
    1: (1, 6),
    2: (7, 12),
}

FIRST_NAMES_MALE = [
    "Nimal", "Kasun", "Chamara", "Dilan", "Shehan",
    "Kusal", "Naveen", "Ravindu", "Ishara", "Tharindu",
    "Sahan", "Amal", "Lahiru", "Supun", "Ayesh"
]

FIRST_NAMES_FEMALE = [
    "Nethmi", "Hiruni", "Dilini", "Kavindi", "Sashini",
    "Tharushi", "Piumi", "Ishani", "Sanduni", "Nadeesha",
    "Amandi", "Madhavi", "Rashmi", "Sachini", "Dinithi"
]

LAST_NAMES = [
    "Perera", "Silva", "Fernando", "Jayasinghe", "Wijesinghe",
    "Dias", "Gunawardena", "Herath", "Ranatunga", "Senanayake",
    "Abeysekera", "Madushanka", "Rajapaksha", "Ekanayake", "Peiris"
]

ASSIGNMENT_TYPES = ["Quiz", "Assignment", "Midterm", "Final"]


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def random_date_in_semester(year: int, semester: int, rng: np.random.Generator) -> pd.Timestamp:
    start_month, end_month = SEMESTER_MONTHS[semester]
    month = int(rng.integers(start_month, end_month + 1))
    last_day = calendar.monthrange(year, month)[1]
    day = int(rng.integers(1, last_day + 1))
    return pd.Timestamp(year=year, month=month, day=day)


def inject_missing_values(df: pd.DataFrame, column: str, frac: float, rng: np.random.Generator) -> pd.DataFrame:
    if frac <= 0 or len(df) == 0:
        return df
    count = max(1, int(len(df) * frac))
    idx = rng.choice(df.index.to_numpy(), size=count, replace=False)
    df.loc[idx, column] = np.nan
    return df


def inject_duplicates(df: pd.DataFrame, frac: float, rng: np.random.Generator) -> pd.DataFrame:
    if frac <= 0 or len(df) == 0:
        return df
    count = max(1, int(len(df) * frac))
    dup_rows = df.sample(n=count, replace=False, random_state=int(rng.integers(0, 1_000_000)))
    return pd.concat([df, dup_rows], ignore_index=True)


def normalize_existing_student_ids(base_students: pd.DataFrame) -> int:
    return int(base_students["StudentID"].max()) + 1


def next_course_number(base_courses: pd.DataFrame) -> int:
    numbers = (
        base_courses["CourseID"]
        .astype(str)
        .str.extract(r"(\d+)$")[0]
        .dropna()
        .astype(int)
    )
    if len(numbers) == 0:
        return 1
    return int(numbers.max()) + 1


def load_base_data(base_dir: Path):
    students = pd.read_csv(base_dir / "students.csv")
    courses = pd.read_csv(base_dir / "courses.csv")
    grades = pd.read_csv(base_dir / "grades.csv")
    attendance = pd.read_csv(base_dir / "attendance.csv")
    return students, courses, grades, attendance


def generate_students(base_students: pd.DataFrame, target_students: int, rng: np.random.Generator) -> pd.DataFrame:
    base_students = base_students.copy()

    major_dist = base_students["Major"].dropna().value_counts(normalize=True)
    majors = major_dist.index.tolist()
    major_probs = major_dist.values

    gender_dist = base_students["Gender"].dropna().value_counts(normalize=True)
    genders = gender_dist.index.tolist()
    gender_probs = gender_dist.values

    rows = base_students.to_dict(orient="records")
    next_id = normalize_existing_student_ids(base_students)

    while len(rows) < target_students:
        gender = str(rng.choice(genders, p=gender_probs))
        major = str(rng.choice(majors, p=major_probs))

        if gender.lower() == "male":
            first_name = str(rng.choice(FIRST_NAMES_MALE))
        else:
            first_name = str(rng.choice(FIRST_NAMES_FEMALE))

        last_name = str(rng.choice(LAST_NAMES))

        birth_year = int(rng.integers(2000, 2007))
        birth_month = int(rng.integers(1, 13))
        birth_day = int(rng.integers(1, calendar.monthrange(birth_year, birth_month)[1] + 1))

        gpa = round(float(np.clip(rng.normal(loc=2.9, scale=0.55), 1.5, 4.0)), 2)

        rows.append(
            {
                "StudentID": next_id,
                "FirstName": first_name,
                "LastName": last_name,
                "Gender": gender,
                "DateOfBirth": f"{birth_year:04d}-{birth_month:02d}-{birth_day:02d}",
                "Major": major,
                "GPA": gpa,
            }
        )
        next_id += 1

    students_df = pd.DataFrame(rows)

    # small realistic quality issues in non-key columns
    students_df = inject_missing_values(students_df, "Major", 0.003, rng)

    case_idx = rng.choice(
        students_df.index.to_numpy(),
        size=max(1, int(len(students_df) * 0.005)),
        replace=False,
    )
    students_df.loc[case_idx, "Gender"] = students_df.loc[case_idx, "Gender"].astype(str).str.upper()

    # a few unrealistic GPA values for cleaning later
    bad_gpa_idx = rng.choice(
        students_df.index.to_numpy(),
        size=max(1, int(len(students_df) * 0.003)),
        replace=False,
    )
    students_df.loc[bad_gpa_idx, "GPA"] = rng.choice([4.5, -0.5, 5.0], size=len(bad_gpa_idx))

    return students_df


def generate_courses(base_courses: pd.DataFrame, target_courses: int, rng: np.random.Generator) -> pd.DataFrame:
    base_courses = base_courses.copy()

    dept_dist = base_courses["Department"].dropna().value_counts(normalize=True)
    departments = dept_dist.index.tolist()
    dept_probs = dept_dist.values

    credits_dist = base_courses["Credits"].dropna().value_counts(normalize=True)
    credit_values = credits_dist.index.tolist()
    credit_probs = credits_dist.values

    rows = base_courses.to_dict(orient="records")
    next_num = next_course_number(base_courses)

    while len(rows) < target_courses:
        department = str(rng.choice(departments, p=dept_probs))
        credits = int(rng.choice(credit_values, p=credit_probs))

        rows.append(
            {
                "CourseID": f"COURSE{next_num}",
                "CourseName": f"{department} Course {next_num}",
                "Department": department,
                "Credits": credits,
                "Instructor": f"Instructor {next_num}",
            }
        )
        next_num += 1

    courses_df = pd.DataFrame(rows)

    # small non-key issues
    courses_df = inject_missing_values(courses_df, "Instructor", 0.02, rng)

    dept_case_idx = rng.choice(
        courses_df.index.to_numpy(),
        size=max(1, int(len(courses_df) * 0.01)),
        replace=False,
    )
    courses_df.loc[dept_case_idx, "Department"] = (
        courses_df.loc[dept_case_idx, "Department"].astype(str).str.lower()
    )

    return courses_df


def build_enrollments(
    students_df: pd.DataFrame,
    courses_df: pd.DataFrame,
    rng: np.random.Generator,
    min_courses_per_term: int = 2,
    max_courses_per_term: int = 4,
) -> pd.DataFrame:
    """
    Internal helper table used to generate grades and attendance.
    Not saved as a project source table.
    """
    course_records = courses_df[["CourseID", "Department"]].to_dict(orient="records")

    rows = []
    enrollment_id = 1

    for student in students_df.itertuples(index=False):
        major = getattr(student, "Major", None)

        for year in YEARS:
            for semester in [1, 2]:
                course_count = int(rng.integers(min_courses_per_term, max_courses_per_term + 1))

                preferred_courses = [c for c in course_records if c["Department"] == major]
                selected_course_ids = set()

                while len(selected_course_ids) < course_count:
                    if preferred_courses and rng.random() < 0.65:
                        course = preferred_courses[int(rng.integers(0, len(preferred_courses)))]
                    else:
                        course = course_records[int(rng.integers(0, len(course_records)))]

                    selected_course_ids.add(course["CourseID"])

                for course_id in selected_course_ids:
                    rows.append(
                        {
                            "EnrollmentID": enrollment_id,
                            "StudentID": student.StudentID,
                            "CourseID": course_id,
                            "Year": year,
                            "Semester": semester,
                        }
                    )
                    enrollment_id += 1

    return pd.DataFrame(rows)


def generate_grades(
    enrollments_df: pd.DataFrame,
    students_df: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    rows = []
    grade_id = 1

    student_gpa_map = students_df.set_index("StudentID")["GPA"].to_dict()

    for enr in enrollments_df.itertuples(index=False):
        # 2-4 graded events per student-course-term
        record_count = int(rng.integers(2, 5))

        base_gpa = float(student_gpa_map.get(enr.StudentID, 2.8))
        # slightly clamp weird GPAs when generating marks
        base_gpa_for_marks = float(np.clip(base_gpa, 1.5, 4.0))
        base_score_mean = 45 + (base_gpa_for_marks * 12.5)

        assignment_types = rng.choice(ASSIGNMENT_TYPES, size=record_count, replace=False)

        for assignment_type in assignment_types:
            score = int(np.clip(rng.normal(loc=base_score_mean, scale=12), 0, 100))
            date = random_date_in_semester(enr.Year, enr.Semester, rng)

            rows.append(
                {
                    "GradeID": grade_id,
                    "StudentID": enr.StudentID,
                    "CourseID": enr.CourseID,
                    "AssignmentType": str(assignment_type),
                    "Score": score,
                    "Date": date.strftime("%Y-%m-%d"),
                }
            )
            grade_id += 1

    grades_df = pd.DataFrame(rows)

    # inject realistic raw-data issues
    grades_df = inject_missing_values(grades_df, "Score", 0.02, rng)

    invalid_idx = rng.choice(
        grades_df.index.to_numpy(),
        size=max(1, int(len(grades_df) * 0.01)),
        replace=False,
    )
    grades_df.loc[invalid_idx, "Score"] = rng.choice([-10, -5, 105, 120], size=len(invalid_idx))

    casing_idx = rng.choice(
        grades_df.index.to_numpy(),
        size=max(1, int(len(grades_df) * 0.02)),
        replace=False,
    )
    grades_df.loc[casing_idx, "AssignmentType"] = (
        grades_df.loc[casing_idx, "AssignmentType"]
        .astype(str)
        .map(lambda x: rng.choice([x.lower(), x.upper(), x.title()]))
    )

    bad_date_idx = rng.choice(
        grades_df.index.to_numpy(),
        size=max(1, int(len(grades_df) * 0.003)),
        replace=False,
    )
    grades_df.loc[bad_date_idx, "Date"] = rng.choice(
        ["2024/13/01", "not_a_date", "2023-02-30"],
        size=len(bad_date_idx),
    )

    grades_df = inject_duplicates(grades_df, 0.01, rng)

    grades_df = grades_df.reset_index(drop=True)
    grades_df["GradeID"] = np.arange(1, len(grades_df) + 1)

    return grades_df


def generate_attendance(
    enrollments_df: pd.DataFrame,
    students_df: pd.DataFrame,
    rng: np.random.Generator,
) -> pd.DataFrame:
    rows = []
    attendance_id = 1

    student_gpa_map = students_df.set_index("StudentID")["GPA"].to_dict()

    for enr in enrollments_df.itertuples(index=False):
        # 6-10 attendance records per student-course-term
        record_count = int(rng.integers(6, 11))

        base_gpa = float(student_gpa_map.get(enr.StudentID, 2.8))
        base_gpa_for_att = float(np.clip(base_gpa, 1.5, 4.0))
        present_prob = float(np.clip(0.68 + ((base_gpa_for_att - 2.5) * 0.08), 0.55, 0.95))

        for _ in range(record_count):
            date = random_date_in_semester(enr.Year, enr.Semester, rng)
            status = "Present" if rng.random() < present_prob else "Absent"

            rows.append(
                {
                    "AttendanceID": attendance_id,
                    "StudentID": enr.StudentID,
                    "CourseID": enr.CourseID,
                    "Date": date.strftime("%Y-%m-%d"),
                    "AttendanceStatus": status,
                }
            )
            attendance_id += 1

    attendance_df = pd.DataFrame(rows)

    attendance_df = inject_missing_values(attendance_df, "AttendanceStatus", 0.02, rng)

    case_idx = rng.choice(
        attendance_df.index.to_numpy(),
        size=max(1, int(len(attendance_df) * 0.03)),
        replace=False,
    )

    def mutate_status(x):
        if pd.isna(x):
            return x
        variants = {
            "Present": ["Present", "present", "PRESENT"],
            "Absent": ["Absent", "absent", "ABSENT"],
        }
        return rng.choice(variants.get(str(x), [str(x)]))

    attendance_df.loc[case_idx, "AttendanceStatus"] = (
        attendance_df.loc[case_idx, "AttendanceStatus"].map(mutate_status)
    )

    bad_date_idx = rng.choice(
        attendance_df.index.to_numpy(),
        size=max(1, int(len(attendance_df) * 0.003)),
        replace=False,
    )
    attendance_df.loc[bad_date_idx, "Date"] = rng.choice(
        ["2025/15/02", "wrong_date", "2022-02-31"],
        size=len(bad_date_idx),
    )

    attendance_df = inject_duplicates(attendance_df, 0.01, rng)

    attendance_df = attendance_df.reset_index(drop=True)
    attendance_df["AttendanceID"] = np.arange(1, len(attendance_df) + 1)

    return attendance_df


def main():
    parser = argparse.ArgumentParser(description="Generate expanded raw dataset for EduSpark")
    parser.add_argument("--base-dir", default="data/base", help="Folder containing base CSV files")
    parser.add_argument("--output-dir", default="data/raw_expanded", help="Folder to save expanded raw CSV files")
    parser.add_argument("--students", type=int, default=10000, help="Target number of students")
    parser.add_argument("--courses", type=int, default=100, help="Target number of courses")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    rng = np.random.default_rng(args.seed)

    base_dir = Path(args.base_dir)
    output_dir = Path(args.output_dir)
    ensure_dir(output_dir)

    base_students, base_courses, base_grades, base_attendance = load_base_data(base_dir)

    students_df = generate_students(base_students, args.students, rng)
    courses_df = generate_courses(base_courses, args.courses, rng)
    enrollments_df = build_enrollments(students_df, courses_df, rng)
    grades_df = generate_grades(enrollments_df, students_df, rng)
    attendance_df = generate_attendance(enrollments_df, students_df, rng)

    students_df.to_csv(output_dir / "students.csv", index=False)
    courses_df.to_csv(output_dir / "courses.csv", index=False)
    grades_df.to_csv(output_dir / "grades.csv", index=False)
    attendance_df.to_csv(output_dir / "attendance.csv", index=False)

    print("\nEduSpark expanded raw dataset generated successfully.")
    print(f"students.csv   -> {len(students_df):,} rows")
    print(f"courses.csv    -> {len(courses_df):,} rows")
    print(f"grades.csv     -> {len(grades_df):,} rows")
    print(f"attendance.csv -> {len(attendance_df):,} rows")

    print("\nInjected raw-data issues summary:")
    print(f"Missing Grade Score values: {int(grades_df['Score'].isna().sum()):,}")
    print(f"Missing AttendanceStatus values: {int(attendance_df['AttendanceStatus'].isna().sum()):,}")

    grade_dates = pd.to_datetime(grades_df["Date"], errors="coerce")
    attendance_dates = pd.to_datetime(attendance_df["Date"], errors="coerce")

    print("\nValid year coverage:")
    print("Grades years:", sorted(grade_dates.dropna().dt.year.unique().tolist()))
    print("Attendance years:", sorted(attendance_dates.dropna().dt.year.unique().tolist()))


if __name__ == "__main__":
    main()
    