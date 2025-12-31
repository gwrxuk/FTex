"""
Transaction Monitoring Spark Job

Real-time and batch transaction monitoring for AML and fraud detection.
Implements various detection rules and ML-based anomaly detection.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, sum as spark_sum, count, avg, stddev,
    window, lag, lead, when, lit, datediff,
    hour, dayofweek, to_timestamp, current_timestamp,
    array, explode, struct, collect_list, first,
    round as spark_round, expr
)
from pyspark.sql.types import (
    StructType, StructField, StringType, FloatType,
    DoubleType, TimestampType, IntegerType, ArrayType
)
from pyspark.sql.window import Window
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
import argparse


def create_spark_session():
    """Create Spark session for transaction monitoring."""
    return (SparkSession.builder
            .appName("FTex Transaction Monitoring")
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.streaming.kafka.maxRatePerPartition", "1000")
            .getOrCreate())


def detect_structuring(df, threshold=9500, window_hours=24, min_transactions=3):
    """
    Detect potential structuring/smurfing activity.
    
    Structuring: Breaking large transactions into smaller ones
    to avoid reporting thresholds (typically $10,000 in US).
    """
    # Window for each sender within time period
    time_window = Window.partitionBy("sender_entity_id").orderBy("transaction_date")
    
    structuring_df = (
        df
        .filter(col("amount") < 10000)  # Below reporting threshold
        .filter(col("amount") >= threshold)  # Above structuring threshold
        .withColumn(
            "prev_tx_time",
            lag("transaction_date").over(time_window)
        )
        .withColumn(
            "hours_since_prev",
            (col("transaction_date").cast("long") - col("prev_tx_time").cast("long")) / 3600
        )
        .filter(col("hours_since_prev") <= window_hours)
        .groupBy("sender_entity_id", window("transaction_date", f"{window_hours} hours"))
        .agg(
            spark_sum("amount").alias("total_amount"),
            count("*").alias("transaction_count"),
            collect_list("id").alias("transaction_ids")
        )
        .filter(col("transaction_count") >= min_transactions)
        .filter(col("total_amount") >= 10000)  # Total exceeds threshold
        .withColumn("alert_type", lit("structuring"))
        .withColumn("severity", lit("high"))
        .withColumn(
            "risk_score",
            when(col("total_amount") >= 50000, 0.9)
            .when(col("total_amount") >= 25000, 0.7)
            .otherwise(0.5)
        )
    )
    
    return structuring_df


def detect_velocity_spikes(df, lookback_days=30, std_threshold=3):
    """
    Detect unusual transaction velocity (frequency) for entities.
    """
    # Calculate rolling statistics for each entity
    entity_window = Window.partitionBy("sender_entity_id").orderBy("transaction_date").rowsBetween(-lookback_days, -1)
    
    velocity_df = (
        df
        .withColumn(
            "daily_count",
            count("*").over(
                Window.partitionBy("sender_entity_id", window("transaction_date", "1 day"))
            )
        )
        .withColumn(
            "avg_daily_count",
            avg("daily_count").over(entity_window)
        )
        .withColumn(
            "std_daily_count",
            stddev("daily_count").over(entity_window)
        )
        .withColumn(
            "z_score",
            (col("daily_count") - col("avg_daily_count")) / col("std_daily_count")
        )
        .filter(col("z_score") >= std_threshold)
        .withColumn("alert_type", lit("velocity_spike"))
        .withColumn("severity", 
            when(col("z_score") >= 5, lit("critical"))
            .when(col("z_score") >= 4, lit("high"))
            .otherwise(lit("medium"))
        )
        .withColumn(
            "risk_score",
            spark_round(col("z_score") / 10, 2)
        )
    )
    
    return velocity_df


def detect_round_amounts(df, tolerance=0.01):
    """
    Flag transactions with suspiciously round amounts.
    """
    round_amounts_df = (
        df
        .withColumn(
            "is_round_1000",
            (col("amount") % 1000 == 0) & (col("amount") >= 1000)
        )
        .withColumn(
            "is_round_500",
            (col("amount") % 500 == 0) & (col("amount") >= 500)
        )
        .withColumn(
            "is_round_100",
            (col("amount") % 100 == 0) & (col("amount") >= 100)
        )
        .filter(col("is_round_1000") | col("is_round_500"))
        .withColumn("alert_type", lit("round_amount"))
        .withColumn("severity", lit("low"))
        .withColumn(
            "risk_score",
            when(col("is_round_1000") & (col("amount") >= 10000), 0.6)
            .when(col("is_round_1000"), 0.4)
            .otherwise(0.2)
        )
    )
    
    return round_amounts_df


def detect_high_risk_jurisdictions(df, high_risk_countries=None):
    """
    Flag transactions involving high-risk jurisdictions.
    """
    if high_risk_countries is None:
        # Default FATF high-risk jurisdictions
        high_risk_countries = ["KP", "IR", "MM", "SY", "YE", "AF"]
    
    jurisdiction_df = (
        df
        .filter(
            col("sender_country").isin(high_risk_countries) |
            col("receiver_country").isin(high_risk_countries)
        )
        .withColumn("alert_type", lit("high_risk_jurisdiction"))
        .withColumn("severity", lit("high"))
        .withColumn("risk_score", lit(0.8))
    )
    
    return jurisdiction_df


def detect_unusual_timing(df):
    """
    Flag transactions occurring at unusual times.
    """
    timing_df = (
        df
        .withColumn("tx_hour", hour("transaction_date"))
        .withColumn("tx_dow", dayofweek("transaction_date"))
        .withColumn(
            "is_off_hours",
            (col("tx_hour") < 6) | (col("tx_hour") > 22)
        )
        .withColumn(
            "is_weekend",
            col("tx_dow").isin([1, 7])  # Sunday=1, Saturday=7
        )
        .filter(col("is_off_hours") | col("is_weekend"))
        .withColumn("alert_type", lit("unusual_timing"))
        .withColumn("severity", lit("low"))
        .withColumn(
            "risk_score",
            when(col("is_off_hours") & col("is_weekend"), 0.4)
            .when(col("is_off_hours"), 0.3)
            .otherwise(0.2)
        )
    )
    
    return timing_df


def calculate_entity_risk_scores(df):
    """
    Calculate aggregated risk scores for entities based on transaction patterns.
    """
    entity_window = Window.partitionBy("sender_entity_id")
    
    entity_risk = (
        df
        .groupBy("sender_entity_id")
        .agg(
            count("*").alias("total_transactions"),
            spark_sum("amount").alias("total_volume"),
            avg("amount").alias("avg_transaction"),
            stddev("amount").alias("std_transaction"),
            spark_sum(when(col("is_flagged") == 1, 1).otherwise(0)).alias("flagged_count"),
            count(when(col("sender_country") != col("receiver_country"), 1)).alias("cross_border_count")
        )
        .withColumn(
            "volume_risk",
            when(col("total_volume") >= 1000000, 0.3)
            .when(col("total_volume") >= 100000, 0.2)
            .otherwise(0.1)
        )
        .withColumn(
            "activity_risk",
            when(col("total_transactions") >= 100, 0.2)
            .when(col("total_transactions") >= 50, 0.1)
            .otherwise(0.05)
        )
        .withColumn(
            "flag_risk",
            when(col("flagged_count") >= 10, 0.4)
            .when(col("flagged_count") >= 5, 0.3)
            .when(col("flagged_count") >= 1, 0.2)
            .otherwise(0)
        )
        .withColumn(
            "cross_border_risk",
            (col("cross_border_count") / col("total_transactions")) * 0.2
        )
        .withColumn(
            "overall_risk_score",
            spark_round(
                col("volume_risk") + col("activity_risk") + 
                col("flag_risk") + col("cross_border_risk"),
                3
            )
        )
    )
    
    return entity_risk


def run_monitoring_pipeline(spark, input_path, output_path, rules=None):
    """
    Run the complete transaction monitoring pipeline.
    """
    if rules is None:
        rules = ["structuring", "velocity", "round_amounts", "jurisdictions", "timing"]
    
    # Load transactions
    print(f"Loading transactions from {input_path}")
    
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("transaction_type", StringType(), True),
        StructField("amount", DoubleType(), True),
        StructField("currency", StringType(), True),
        StructField("sender_entity_id", StringType(), True),
        StructField("receiver_entity_id", StringType(), True),
        StructField("sender_country", StringType(), True),
        StructField("receiver_country", StringType(), True),
        StructField("transaction_date", TimestampType(), True),
        StructField("is_flagged", IntegerType(), True),
        StructField("risk_score", DoubleType(), True)
    ])
    
    transactions_df = spark.read.schema(schema).parquet(input_path)
    
    # Run detection rules
    alerts = []
    
    if "structuring" in rules:
        print("Running structuring detection...")
        alerts.append(detect_structuring(transactions_df))
    
    if "velocity" in rules:
        print("Running velocity spike detection...")
        alerts.append(detect_velocity_spikes(transactions_df))
    
    if "round_amounts" in rules:
        print("Running round amount detection...")
        alerts.append(detect_round_amounts(transactions_df))
    
    if "jurisdictions" in rules:
        print("Running high-risk jurisdiction detection...")
        alerts.append(detect_high_risk_jurisdictions(transactions_df))
    
    if "timing" in rules:
        print("Running unusual timing detection...")
        alerts.append(detect_unusual_timing(transactions_df))
    
    # Combine all alerts
    print("Consolidating alerts...")
    
    # Calculate entity risk scores
    print("Calculating entity risk scores...")
    entity_risks = calculate_entity_risk_scores(transactions_df)
    
    # Write results
    entity_risks.write.mode("overwrite").parquet(f"{output_path}/entity_risks")
    
    # Write alerts (if any)
    for i, alert_df in enumerate(alerts):
        if alert_df.count() > 0:
            alert_df.write.mode("append").parquet(f"{output_path}/alerts")
    
    # Generate summary statistics
    total_alerts = sum(df.count() for df in alerts)
    high_risk_entities = entity_risks.filter(col("overall_risk_score") >= 0.5).count()
    
    print(f"\nMonitoring Summary:")
    print(f"  Total Alerts Generated: {total_alerts}")
    print(f"  High Risk Entities: {high_risk_entities}")
    print(f"  Rules Executed: {len(rules)}")
    
    return alerts, entity_risks


def main():
    parser = argparse.ArgumentParser(description="FTex Transaction Monitoring")
    parser.add_argument("--input", required=True, help="Input path for transaction data")
    parser.add_argument("--output", required=True, help="Output path for alerts and scores")
    parser.add_argument("--rules", nargs="+", default=None, help="Detection rules to run")
    
    args = parser.parse_args()
    
    spark = create_spark_session()
    
    try:
        run_monitoring_pipeline(spark, args.input, args.output, args.rules)
        print("Transaction monitoring completed successfully!")
    except Exception as e:
        print(f"Error during transaction monitoring: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

