import argparse
import os
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


VALID_ENROLLMENT_GRADES = ["A", "B", "C", "D", "F"]


def configure_windows_hadoop(hadoop_home: str | None = None) -> dict[str, str]:
    if os.name != "nt":
        return {}

    candidate = hadoop_home or os.environ.get("HADOOP_HOME")
    default_home = Path(r"C:\hadoop")

    if not candidate and default_home.exists():
        candidate = str(default_home)

    if not candidate:
        print("Warning: HADOOP_HOME is not set. If Spark fails on Windows, set HADOOP_HOME or use --hadoop-home.")
        return {}

    hadoop_path = Path(candidate)
    if not hadoop_path.exists():
        print(f"Warning: Hadoop home not found at {hadoop_path}. Continuing without winutils configuration.")
        return {}

    os.environ["HADOOP_HOME"] = str(hadoop_path)
    os.environ["hadoop.home.dir"] = str(hadoop_path)

    bin_path = hadoop_path / "bin"
    configs = {}

    if bin_path.exists():
        os.environ["PATH"] = f"{bin_path};" + os.environ.get("PATH", "")
        configs["spark.driver.extraLibraryPath"] = str(bin_path)
        configs["spark.executor.extraLibraryPath"] = str(bin_path)

    return configs


def build_spark(app_name: str, hadoop_home: str | None = None) -> SparkSession:
    builder = (
        SparkSession.builder
        .master("local[*]")
        .appName(app_name)
        .config("spark.sql.ansi.enabled", "false")
    )

    for key, value in configure_windows_hadoop(hadoop_home).items():
        builder = builder.config(key, value)

    spark = builder.getOrCreate()
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def safe_parse_date(column_name: str):
    # Normalize slash dates to dash dates and accept optional time portions.
    normalized = F.regexp_replace(F.trim(F.col(column_name)), "/", "-")
    date_portion = F.regexp_extract(normalized, r"(\d{4}-\d{2}-\d{2})", 1)
    return F.to_date(date_portion, "yyyy-MM-dd")


def derive_term_name_from_date(column_name: str):
    month_col = F.month(F.col(column_name))
    return (
        F.when(month_col <= 4, F.lit("Spring"))
         .when(month_col <= 6, F.lit("Summer"))
         .otherwise(F.lit("Fall"))
    )


def term_name_to_semester(term_col):
    return (
        F.when(term_col.isin("Spring", "Summer"), F.lit(1))
         .when(term_col == "Fall", F.lit(2))
         .otherwise(F.lit(None))
    )


def standardize_students(df):
    df = (
        df.select(
            F.col("StudentID").alias("student_id"),
            F.col("FirstName").alias("first_name"),
            F.col("LastName").alias("last_name"),
            F.col("Gender").alias("gender"),
            F.col("DateOfBirth").alias("date_of_birth"),
            F.col("Major").alias("major"),
            F.col("GPA").alias("gpa"),
        )
        .withColumn("student_id", F.col("student_id").cast("long"))
        .dropna(subset=["student_id"])
        .dropDuplicates(["student_id"])
        .withColumn("first_name", F.initcap(F.trim(F.col("first_name"))))
        .withColumn("last_name", F.initcap(F.trim(F.col("last_name"))))
        .withColumn("gender_raw", F.lower(F.trim(F.col("gender"))))
        .withColumn(
            "gender",
            F.when(F.col("gender_raw") == "male", F.lit("Male"))
             .when(F.col("gender_raw") == "female", F.lit("Female"))
             .otherwise(F.lit(None))
        )
        .drop("gender_raw")
        .withColumn("major", F.initcap(F.trim(F.col("major"))))
        .withColumn("date_of_birth", F.to_date(F.col("date_of_birth"), "yyyy-MM-dd"))
        .withColumn("gpa", F.col("gpa").cast("double"))
        .withColumn(
            "gpa",
            F.when((F.col("gpa") >= 0.0) & (F.col("gpa") <= 4.0), F.col("gpa"))
             .otherwise(F.lit(None))
        )
    )

    avg_gpa = df.select(F.avg("gpa").alias("avg_gpa")).first()["avg_gpa"]
    if avg_gpa is None:
        avg_gpa = 2.75

    df = df.fillna({"gpa": float(avg_gpa)})
    return df


def standardize_courses(df):
    df = (
        df.select(
            F.col("CourseID").alias("course_id"),
            F.col("CourseName").alias("course_name"),
            F.col("Department").alias("department"),
            F.col("Credits").alias("credits"),
            F.col("Instructor").alias("instructor"),
        )
        .withColumn("course_id", F.upper(F.trim(F.col("course_id"))))
        .dropna(subset=["course_id"])
        .dropDuplicates(["course_id"])
        .withColumn("course_name", F.initcap(F.trim(F.col("course_name"))))
        .withColumn("department", F.initcap(F.trim(F.col("department"))))
        .withColumn("instructor", F.initcap(F.trim(F.col("instructor"))))
        .withColumn("credits", F.col("credits").cast("int"))
        .withColumn(
            "credits",
            F.when((F.col("credits") > 0) & (F.col("credits") <= 6), F.col("credits"))
             .otherwise(F.lit(None))
        )
    )

    df = df.fillna({"credits": 3, "instructor": "Unknown"})
    return df


def standardize_enrollments(df):
    term_raw = F.initcap(F.trim(F.col("term_name_raw")))

    df = (
        df.select(
            F.col("EnrollmentID").alias("enrollment_id"),
            F.col("StudentID").alias("student_id"),
            F.col("CourseID").alias("course_id"),
            F.col("Semester").alias("term_name_raw"),
            F.col("Year").alias("year"),
            F.col("Grade").alias("enrollment_grade"),
            F.col("Source").alias("source"),
        )
        .withColumn("enrollment_id", F.col("enrollment_id").cast("long"))
        .withColumn("student_id", F.col("student_id").cast("long"))
        .withColumn("course_id", F.upper(F.trim(F.col("course_id"))))
        .withColumn("year", F.col("year").cast("int"))
        .withColumn(
            "term_name",
            F.when(term_raw.isin("1", "Semester 1"), F.lit("Spring"))
             .when(term_raw.isin("2", "Semester 2"), F.lit("Fall"))
             .when(term_raw.isin("Spring", "Summer", "Fall"), term_raw)
             .otherwise(F.lit(None))
        )
        .withColumn("semester", term_name_to_semester(F.col("term_name")))
        .withColumn("enrollment_grade", F.upper(F.trim(F.col("enrollment_grade"))))
        .withColumn(
            "enrollment_grade",
            F.when(F.col("enrollment_grade").isin(*VALID_ENROLLMENT_GRADES), F.col("enrollment_grade"))
             .otherwise(F.lit(None))
        )
        .withColumn(
            "source",
            F.when(F.length(F.trim(F.col("source"))) > 0, F.initcap(F.trim(F.col("source"))))
             .otherwise(F.lit("Unknown"))
        )
        .dropna(subset=["enrollment_id", "student_id", "course_id", "term_name", "year"])
        .filter((F.col("year") >= 2000) & (F.col("year") <= 2100))
        .dropDuplicates(["enrollment_id"])
        .dropDuplicates(["student_id", "course_id", "year", "term_name"])
        .select(
            "enrollment_id",
            "student_id",
            "course_id",
            "term_name",
            "semester",
            "year",
            "enrollment_grade",
            "source",
        )
    )
    return df


def standardize_grades(df):
    df = (
        df.select(
            F.col("StudentID").alias("student_id"),
            F.col("CourseID").alias("course_id"),
            F.col("AssignmentType").alias("assignment_type"),
            F.col("Score").alias("score"),
            F.col("Date").alias("event_date"),
        )
        .withColumn("student_id", F.col("student_id").cast("long"))
        .withColumn("course_id", F.upper(F.trim(F.col("course_id"))))
        .dropDuplicates()
        .withColumn("assignment_type", F.initcap(F.lower(F.trim(F.col("assignment_type")))))
        .withColumn("score", F.col("score").cast("double"))
        .withColumn(
            "score",
            F.when((F.col("score") >= 0) & (F.col("score") <= 100), F.col("score"))
             .otherwise(F.lit(None))
        )
        .withColumn("event_date", safe_parse_date("event_date"))
        .dropna(subset=["student_id", "course_id", "score", "event_date"])
        .withColumn("year", F.year("event_date"))
        .withColumn("term_name", derive_term_name_from_date("event_date"))
        .withColumn("semester", term_name_to_semester(F.col("term_name")))
    )
    return df


def standardize_attendance(df):
    df = (
        df.select(
            F.col("StudentID").alias("student_id"),
            F.col("CourseID").alias("course_id"),
            F.col("AttendanceStatus").alias("attendance_status"),
            F.col("Date").alias("event_date"),
        )
        .withColumn("student_id", F.col("student_id").cast("long"))
        .withColumn("course_id", F.upper(F.trim(F.col("course_id"))))
        .dropDuplicates()
        .withColumn("attendance_status_raw", F.lower(F.trim(F.col("attendance_status"))))
        .withColumn(
            "attendance_status",
            F.when(F.col("attendance_status_raw") == "present", F.lit("Present"))
             .when(F.col("attendance_status_raw") == "absent", F.lit("Absent"))
             .otherwise(F.lit(None))
        )
        .drop("attendance_status_raw")
        .withColumn("event_date", safe_parse_date("event_date"))
        .dropna(subset=["student_id", "course_id", "attendance_status", "event_date"])
        .withColumn("year", F.year("event_date"))
        .withColumn("term_name", derive_term_name_from_date("event_date"))
        .withColumn("semester", term_name_to_semester(F.col("term_name")))
        .withColumn(
            "attended_flag",
            F.when(F.col("attendance_status") == "Present", F.lit(1)).otherwise(F.lit(0))
        )
    )
    return df


def build_grade_summary(grades_df):
    return (
        grades_df.groupBy("student_id", "course_id", "year", "semester", "term_name")
        .agg(
            F.round(F.avg("score"), 2).alias("average_score"),
            F.count("*").alias("assessment_count")
        )
    )


def build_attendance_summary(attendance_df):
    return (
        attendance_df.groupBy("student_id", "course_id", "year", "semester", "term_name")
        .agg(
            F.round(F.avg("attended_flag") * 100, 2).alias("attendance_percentage"),
            F.count("*").alias("class_count")
        )
    )


def align_summary_to_enrollments(summary_df, enrollments_df):
    enrollment_keys = enrollments_df.select(
        "student_id",
        "course_id",
        "year",
        "semester",
        "term_name",
    ).dropDuplicates()
    return summary_df.join(
        enrollment_keys,
        on=["student_id", "course_id", "year", "semester", "term_name"],
        how="inner",
    )


def build_master_table(students_df, courses_df, enrollments_df, grade_summary_df, attendance_summary_df):
    performance_df = (
        enrollments_df
        .join(
            grade_summary_df,
            on=["student_id", "course_id", "year", "semester", "term_name"],
            how="left"
        )
        .join(
            attendance_summary_df,
            on=["student_id", "course_id", "year", "semester", "term_name"],
            how="left"
        )
    )

    master_df = (
        performance_df
        .join(students_df, on="student_id", how="left")
        .join(courses_df, on="course_id", how="left")
    )

    return master_df


def write_csv(df, output_path: str):
    (
        df.write
        .mode("overwrite")
        .option("header", True)
        .csv(output_path)
    )


def main():
    parser = argparse.ArgumentParser(description="Preprocess EduSpark expanded raw dataset using PySpark")
    parser.add_argument("--input-dir", default="data/raw_expanded", help="Folder containing expanded raw CSV files")
    parser.add_argument("--output-dir", default="data/cleaned", help="Folder to save cleaned CSV folders")
    parser.add_argument(
        "--hadoop-home",
        default=None,
        help="Optional Hadoop home for Windows winutils setup. Defaults to HADOOP_HOME or C:\\hadoop when available.",
    )
    args = parser.parse_args()

    spark = build_spark("EduSparkPreprocessing", args.hadoop_home)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    students_raw = spark.read.option("header", True).csv(str(input_dir / "students.csv"))
    courses_raw = spark.read.option("header", True).csv(str(input_dir / "courses.csv"))
    enrollments_raw = spark.read.option("header", True).csv(str(input_dir / "enrollments.csv"))
    grades_raw = spark.read.option("header", True).csv(str(input_dir / "grades.csv"))
    attendance_raw = spark.read.option("header", True).csv(str(input_dir / "attendance.csv"))

    print("\nRaw row counts")
    print("students_raw   :", students_raw.count())
    print("courses_raw    :", courses_raw.count())
    print("enrollments_raw:", enrollments_raw.count())
    print("grades_raw     :", grades_raw.count())
    print("attendance_raw :", attendance_raw.count())

    students_clean = standardize_students(students_raw)
    courses_clean = standardize_courses(courses_raw)
    enrollments_clean = standardize_enrollments(enrollments_raw)
    grades_clean = standardize_grades(grades_raw)
    attendance_clean = standardize_attendance(attendance_raw)

    valid_student_ids = students_clean.select("student_id").dropDuplicates()
    valid_course_ids = courses_clean.select("course_id").dropDuplicates()
    enrollments_clean = (
        enrollments_clean
        .join(valid_student_ids, on="student_id", how="inner")
        .join(valid_course_ids, on="course_id", how="inner")
    )

    grade_summary = align_summary_to_enrollments(build_grade_summary(grades_clean), enrollments_clean)
    attendance_summary = align_summary_to_enrollments(build_attendance_summary(attendance_clean), enrollments_clean)
    student_performance_master = build_master_table(
        students_clean,
        courses_clean,
        enrollments_clean,
        grade_summary,
        attendance_summary,
    )

    print("\nCleaned row counts")
    print("students_clean             :", students_clean.count())
    print("courses_clean              :", courses_clean.count())
    print("enrollments_clean          :", enrollments_clean.count())
    print("grades_clean               :", grades_clean.count())
    print("attendance_clean           :", attendance_clean.count())
    print("grade_summary              :", grade_summary.count())
    print("attendance_summary         :", attendance_summary.count())
    print("student_performance_master :", student_performance_master.count())

    write_csv(students_clean, str(output_dir / "students_csv"))
    write_csv(courses_clean, str(output_dir / "courses_csv"))
    write_csv(enrollments_clean, str(output_dir / "enrollments_csv"))
    write_csv(grades_clean, str(output_dir / "grades_csv"))
    write_csv(attendance_clean, str(output_dir / "attendance_csv"))
    write_csv(grade_summary, str(output_dir / "grade_summary_csv"))
    write_csv(attendance_summary, str(output_dir / "attendance_summary_csv"))
    write_csv(student_performance_master, str(output_dir / "student_performance_master_csv"))

    print("\nCleaned CSV folders saved to:")
    print(output_dir)

    spark.stop()


if __name__ == "__main__":
    main()
