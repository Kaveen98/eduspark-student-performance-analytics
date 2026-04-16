import argparse
from pathlib import Path

from pyspark.sql import SparkSession
from pyspark.sql import functions as F


def build_spark(app_name: str) -> SparkSession:
    spark = (
        SparkSession.builder
        .master("local[*]")
        .appName(app_name)
        .config("spark.sql.ansi.enabled", "false")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def safe_parse_date(column_name: str):
    # normalize slash dates to dash dates, then parse safely
    normalized = F.regexp_replace(F.trim(F.col(column_name)), "/", "-")
    return F.to_date(normalized, "yyyy-MM-dd")


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


def standardize_grades(df):
    df = (
        df.select(
            F.col("StudentID").alias("student_id"),
            F.col("CourseID").alias("course_id"),
            F.col("AssignmentType").alias("assignment_type"),
            F.col("Score").alias("score"),
            F.col("Date").alias("event_date"),
        )
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
        .withColumn(
            "semester",
            F.when(F.month("event_date") <= 6, F.lit(1)).otherwise(F.lit(2))
        )
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
        .withColumn(
            "semester",
            F.when(F.month("event_date") <= 6, F.lit(1)).otherwise(F.lit(2))
        )
        .withColumn(
            "attended_flag",
            F.when(F.col("attendance_status") == "Present", F.lit(1)).otherwise(F.lit(0))
        )
    )
    return df

def build_grade_summary(grades_df):
    return (
        grades_df.groupBy("student_id", "course_id", "year", "semester")
        .agg(
            F.round(F.avg("score"), 2).alias("average_score"),
            F.count("*").alias("assessment_count")
        )
    )


def build_attendance_summary(attendance_df):
    return (
        attendance_df.groupBy("student_id", "course_id", "year", "semester")
        .agg(
            F.round(F.avg("attended_flag") * 100, 2).alias("attendance_percentage"),
            F.count("*").alias("class_count")
        )
    )


def build_master_table(students_df, courses_df, grade_summary_df, attendance_summary_df):
    performance_df = (
        grade_summary_df.join(
            attendance_summary_df,
            on=["student_id", "course_id", "year", "semester"],
            how="outer"
        )
    )

    master_df = (
        performance_df
        .join(students_df, on="student_id", how="left")
        .join(courses_df, on="course_id", how="left")
    )

    return master_df


def write_parquet(df, output_path: str):
    (
        df.write
        .mode("overwrite")
        .parquet(output_path)
    )


def main():
    parser = argparse.ArgumentParser(description="Preprocess EduSpark expanded raw dataset using PySpark")
    parser.add_argument("--input-dir", default="data/raw_expanded", help="Folder containing expanded raw CSV files")
    parser.add_argument("--output-dir", default="data/cleaned", help="Folder to save cleaned parquet files")
    args = parser.parse_args()

    spark = build_spark("EduSparkPreprocessing")

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    students_raw = spark.read.option("header", True).csv(str(input_dir / "students.csv"))
    courses_raw = spark.read.option("header", True).csv(str(input_dir / "courses.csv"))
    grades_raw = spark.read.option("header", True).csv(str(input_dir / "grades.csv"))
    attendance_raw = spark.read.option("header", True).csv(str(input_dir / "attendance.csv"))

    print("\nRaw row counts")
    print("students_raw   :", students_raw.count())
    print("courses_raw    :", courses_raw.count())
    print("grades_raw     :", grades_raw.count())
    print("attendance_raw :", attendance_raw.count())

    students_clean = standardize_students(students_raw)
    courses_clean = standardize_courses(courses_raw)
    grades_clean = standardize_grades(grades_raw)
    attendance_clean = standardize_attendance(attendance_raw)

    grade_summary = build_grade_summary(grades_clean)
    attendance_summary = build_attendance_summary(attendance_clean)
    student_performance_master = build_master_table(
        students_clean,
        courses_clean,
        grade_summary,
        attendance_summary,
    )

    print("\nCleaned row counts")
    print("students_clean             :", students_clean.count())
    print("courses_clean              :", courses_clean.count())
    print("grades_clean               :", grades_clean.count())
    print("attendance_clean           :", attendance_clean.count())
    print("grade_summary              :", grade_summary.count())
    print("attendance_summary         :", attendance_summary.count())
    print("student_performance_master :", student_performance_master.count())

    write_parquet(students_clean, str(output_dir / "students"))
    write_parquet(courses_clean, str(output_dir / "courses"))
    write_parquet(grades_clean, str(output_dir / "grades"))
    write_parquet(attendance_clean, str(output_dir / "attendance"))
    write_parquet(grade_summary, str(output_dir / "grade_summary"))
    write_parquet(attendance_summary, str(output_dir / "attendance_summary"))
    write_parquet(student_performance_master, str(output_dir / "student_performance_master"))

    print("\nCleaned parquet files saved to:")
    print(output_dir)

    spark.stop()


if __name__ == "__main__":
    main()