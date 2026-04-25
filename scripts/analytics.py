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

   