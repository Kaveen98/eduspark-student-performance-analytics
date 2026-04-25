import argparse
import os
from pathlib import Path

import pandas as pd
from pyspark.sql import SparkSession
from pyspark.sql import functions as F


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


def read_csv(spark: SparkSession, input_path: Path):
    return (
        spark.read
        .option("header", True)
        .csv(str(input_path))
    )


def cast_columns(df, casts: dict[str, str]):
    for column_name, data_type in casts.items():
        if column_name in df.columns:
            df = df.withColumn(column_name, F.col(column_name).cast(data_type))
    return df


def write_csv(df, output_path: str):
    (
        df.coalesce(1)
        .write
        .mode("overwrite")
        .option("header", True)
        .csv(output_path)
    )


def write_small_csv_with_pandas(rows, output_file: str):
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, index=False)


def main():
    parser = argparse.ArgumentParser(description="Run EduSpark analytics on cleaned CSV data")
    parser.add_argument("--input-dir", default="data/cleaned", help="Path to cleaned CSV directory")
    parser.add_argument("--output-dir", default="outputs/analytics", help="Path to save analytics outputs")
    parser.add_argument(
        "--hadoop-home",
        default=None,
        help="Optional Hadoop home for Windows winutils setup. Defaults to HADOOP_HOME or C:\\hadoop when available.",
    )
    parser.add_argument("--high-threshold", type=float, default=85.0, help="Threshold for high-performing students")
    parser.add_argument("--low-threshold", type=float, default=60.0, help="Threshold for low-performing students")
    parser.add_argument("--attendance-risk-threshold", type=float, default=65.0, help="Attendance threshold for at-risk students")
    parser.add_argument("--fail-threshold", type=float, default=40.0, help="Course average below this is considered failed")
    args = parser.parse_args()

    spark = build_spark("EduSparkAnalytics", args.hadoop_home)

    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    master_df = cast_columns(
        read_csv(spark, input_dir / "student_performance_master_csv"),
        {
            "student_id": "long",
            "enrollment_id": "long",
            "semester": "int",
            "year": "int",
            "average_score": "double",
            "assessment_count": "long",
            "attendance_percentage": "double",
            "class_count": "long",
            "date_of_birth": "date",
            "gpa": "double",
            "credits": "int",
        },
    )
    students_df = cast_columns(
        read_csv(spark, input_dir / "students_csv"),
        {
            "student_id": "long",
            "date_of_birth": "date",
            "gpa": "double",
        },
    )
    courses_df = cast_columns(
        read_csv(spark, input_dir / "courses_csv"),
        {
            "credits": "int",
        },
    )
    enrollments_df = cast_columns(
        read_csv(spark, input_dir / "enrollments_csv"),
        {
            "enrollment_id": "long",
            "student_id": "long",
            "semester": "int",
            "year": "int",
        },
    )
    grade_summary_df = cast_columns(
        read_csv(spark, input_dir / "grade_summary_csv"),
        {
            "student_id": "long",
            "year": "int",
            "semester": "int",
            "average_score": "double",
            "assessment_count": "long",
        },
    )
    attendance_summary_df = cast_columns(
        read_csv(spark, input_dir / "attendance_summary_csv"),
        {
            "student_id": "long",
            "year": "int",
            "semester": "int",
            "attendance_percentage": "double",
            "class_count": "long",
        },
    )

    print("\nLoaded cleaned datasets")
    print("student_performance_master:", master_df.count())
    print("students                 :", students_df.count())
    print("courses                  :", courses_df.count())
    print("enrollments              :", enrollments_df.count())
    print("grade_summary            :", grade_summary_df.count())
    print("attendance_summary       :", attendance_summary_df.count())

    # -----------------------------
    # 1. Average marks by subject
    # -----------------------------
    average_marks_by_subject = (
        master_df
        .filter(F.col("average_score").isNotNull())
        .groupBy("course_id", "course_name", "department")
        .agg(
            F.round(F.avg("average_score"), 2).alias("average_mark"),
            F.countDistinct("student_id").alias("student_count"),
            F.count("*").alias("record_count")
        )
        .orderBy(F.desc("average_mark"))
    )

    # --------------------------------
    # 2. Average marks by semester
    # --------------------------------
    average_marks_by_semester = (
        master_df
        .filter(F.col("average_score").isNotNull())
        .groupBy("year", "semester")
        .agg(
            F.round(F.avg("average_score"), 2).alias("average_mark"),
            F.countDistinct("student_id").alias("student_count"),
            F.count("*").alias("record_count")
        )
        .orderBy("year", "semester")
    )

    # -------------------------------------------------
    # 3. Student performance summary (overall per student)
    # -------------------------------------------------
    student_performance_summary = (
        master_df
        .groupBy("student_id", "first_name", "last_name", "gender", "major")
        .agg(
            F.round(F.avg("average_score"), 2).alias("overall_average_score"),
            F.round(F.avg("attendance_percentage"), 2).alias("overall_attendance_percentage"),
            F.countDistinct("course_id").alias("course_count"),
            F.sum(F.when(F.col("average_score") < args.fail_threshold, 1).otherwise(0)).alias("failed_courses")
        )
        .withColumn("full_name", F.concat_ws(" ", F.col("first_name"), F.col("last_name")))
        .select(
            "student_id",
            "full_name",
            "gender",
            "major",
            "overall_average_score",
            "overall_attendance_percentage",
            "course_count",
            "failed_courses"
        )
    )

   
    # -----------------------------
    # 4. High-performing students
    # -----------------------------
    high_performing_students = (
        student_performance_summary
        .filter(F.col("overall_average_score") >= args.high_threshold)
        .orderBy(F.desc("overall_average_score"), F.desc("overall_attendance_percentage"))
    )

    # -----------------------------
    # 5. Low-performing students
    # -----------------------------
    low_performing_students = (
        student_performance_summary
        .filter(F.col("overall_average_score") < args.low_threshold)
        .orderBy(F.asc("overall_average_score"), F.asc("overall_attendance_percentage"))
    )

    # -----------------------------
    # 6. Students at academic risk
    # -----------------------------
    at_risk_students = (
        student_performance_summary
        .withColumn("risk_low_score", F.col("overall_average_score") < args.low_threshold)
        .withColumn("risk_low_attendance", F.col("overall_attendance_percentage") < args.attendance_risk_threshold)
        .withColumn("risk_failed_courses", F.col("failed_courses") >= 2)
        .withColumn(
            "risk_reasons",
            F.concat_ws(
                "; ",
                F.when(F.col("risk_low_score"), F.lit("Low average score")).otherwise(F.lit(None)),
                F.when(F.col("risk_low_attendance"), F.lit("Low attendance")).otherwise(F.lit(None)),
                F.when(F.col("risk_failed_courses"), F.lit("Multiple failed courses")).otherwise(F.lit(None)),
            )
        )
        .filter(
            F.col("risk_low_score") |
            F.col("risk_low_attendance") |
            F.col("risk_failed_courses")
        )
        .orderBy(
            F.asc("overall_average_score"),
            F.asc("overall_attendance_percentage"),
            F.desc("failed_courses")
        )
    )

    # -----------------------------
    # 7. Optional extra outputs
    # -----------------------------
    subject_pass_fail_summary = (
        master_df
        .filter(F.col("average_score").isNotNull())
        .groupBy("course_id", "course_name", "department")
        .agg(
            F.count("*").alias("total_student_course_records"),
            F.sum(F.when(F.col("average_score") >= args.fail_threshold, 1).otherwise(0)).alias("pass_count"),
            F.sum(F.when(F.col("average_score") < args.fail_threshold, 1).otherwise(0)).alias("fail_count")
        )
        .withColumn(
            "pass_rate_percentage",
            F.round((F.col("pass_count") / F.col("total_student_course_records")) * 100, 2)
        )
        .withColumn(
            "fail_rate_percentage",
            F.round((F.col("fail_count") / F.col("total_student_course_records")) * 100, 2)
        )
        .orderBy(F.desc("fail_rate_percentage"))
    )

    department_performance_summary = (
        master_df
        .filter(F.col("average_score").isNotNull())
        .groupBy("department")
        .agg(
            F.round(F.avg("average_score"), 2).alias("department_average_score"),
            F.round(F.avg("attendance_percentage"), 2).alias("department_average_attendance"),
            F.countDistinct("student_id").alias("student_count")
        )
        .orderBy(F.desc("department_average_score"))
    )

    top_10_students = (
        student_performance_summary
        .filter(F.col("overall_average_score").isNotNull())
        .orderBy(F.desc("overall_average_score"), F.desc("overall_attendance_percentage"))
        .limit(10)
    )

    bottom_10_students = (
        student_performance_summary
        .filter(F.col("overall_average_score").isNotNull())
        .orderBy(F.asc("overall_average_score"), F.asc("overall_attendance_percentage"))
        .limit(10)
    )

    analytics_overview_rows = [
        {"metric": "total_students", "value": students_df.count()},
        {"metric": "total_courses", "value": courses_df.count()},
        {"metric": "total_enrollments", "value": enrollments_df.count()},
        {"metric": "total_grade_summary_records", "value": grade_summary_df.count()},
        {"metric": "total_attendance_summary_records", "value": attendance_summary_df.count()},
        {"metric": "high_performing_students", "value": high_performing_students.count()},
        {"metric": "low_performing_students", "value": low_performing_students.count()},
        {"metric": "at_risk_students", "value": at_risk_students.count()},
    ]

    # -----------------------------
    # Print quick summaries
    # -----------------------------
    print("\nMain analytics output counts")
    print("average_marks_by_subject    :", average_marks_by_subject.count())
    print("average_marks_by_semester   :", average_marks_by_semester.count())
    print("high_performing_students    :", high_performing_students.count())
    print("low_performing_students     :", low_performing_students.count())
    print("at_risk_students            :", at_risk_students.count())
    print("subject_pass_fail_summary   :", subject_pass_fail_summary.count())
    print("department_performance      :", department_performance_summary.count())

    print("\nTop 5 subjects by average mark")
    average_marks_by_subject.show(5, truncate=False)

    print("\nAverage marks by semester")
    average_marks_by_semester.show(10, truncate=False)

    print("\nTop 10 students")
    top_10_students.show(truncate=False)

    print("\nBottom 10 students")
    bottom_10_students.show(truncate=False)

    print("\nAt-risk students sample")
    at_risk_students.show(10, truncate=False)

    # -----------------------------
    # Save outputs as CSV
    # -----------------------------
    write_csv(average_marks_by_subject, str(output_dir / "average_marks_by_subject_csv"))
    write_csv(average_marks_by_semester, str(output_dir / "average_marks_by_semester_csv"))
    write_csv(high_performing_students, str(output_dir / "high_performing_students_csv"))
    write_csv(low_performing_students, str(output_dir / "low_performing_students_csv"))
    write_csv(at_risk_students, str(output_dir / "at_risk_students_csv"))
    write_csv(subject_pass_fail_summary, str(output_dir / "subject_pass_fail_summary_csv"))
    write_csv(department_performance_summary, str(output_dir / "department_performance_summary_csv"))
    write_csv(top_10_students, str(output_dir / "top_10_students_csv"))
    write_csv(bottom_10_students, str(output_dir / "bottom_10_students_csv"))
    write_small_csv_with_pandas(
        analytics_overview_rows,
        str(output_dir / "analytics_overview.csv")
    )

    print(f"\nAnalytics outputs saved to: {output_dir}")

    spark.stop()


if __name__ == "__main__":
    main()
