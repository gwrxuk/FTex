"""
Entity Resolution Spark Job

This job performs entity resolution across multiple data sources
using fuzzy matching and graph-based clustering techniques.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, lower, trim, regexp_replace, soundex, 
    levenshtein, when, lit, array, explode, struct,
    collect_list, count, avg, max as spark_max
)
from pyspark.sql.types import (
    StructType, StructField, StringType, FloatType, 
    ArrayType, BooleanType, TimestampType
)
from pyspark.ml.feature import HashingTF, MinHashLSH
import argparse


def create_spark_session(app_name="FTex Entity Resolution"):
    """Create and configure Spark session."""
    return (SparkSession.builder
            .appName(app_name)
            .config("spark.sql.adaptive.enabled", "true")
            .config("spark.sql.adaptive.coalescePartitions.enabled", "true")
            .config("spark.serializer", "org.apache.spark.serializer.KryoSerializer")
            .getOrCreate())


def normalize_name(df, name_col):
    """Normalize names for better matching."""
    return df.withColumn(
        f"{name_col}_normalized",
        lower(trim(regexp_replace(col(name_col), r"[^a-zA-Z0-9\s]", "")))
    )


def calculate_name_similarity(df, col1, col2, threshold=0.8):
    """Calculate similarity score between two name columns."""
    return df.withColumn(
        "name_similarity",
        when(col(col1) == col(col2), 1.0)
        .otherwise(
            1 - (levenshtein(col(col1), col(col2)) / 
                 when(col(col1).isNotNull() & col(col2).isNotNull(),
                      when(len(col(col1)) > len(col(col2)), len(col(col1)))
                      .otherwise(len(col(col2))))
                 .otherwise(1))
        )
    ).filter(col("name_similarity") >= threshold)


def resolve_entities(spark, input_path, output_path, threshold=0.8):
    """
    Main entity resolution pipeline.
    
    Steps:
    1. Load and normalize entity data
    2. Apply blocking keys for efficient comparison
    3. Calculate similarity scores
    4. Cluster similar entities
    5. Generate resolved entity IDs
    """
    
    # Define schema for input data
    schema = StructType([
        StructField("id", StringType(), False),
        StructField("name", StringType(), True),
        StructField("entity_type", StringType(), True),
        StructField("source_system", StringType(), True),
        StructField("attributes", StringType(), True),
        StructField("created_at", TimestampType(), True)
    ])
    
    # Load data
    print(f"Loading entity data from {input_path}")
    entities_df = spark.read.schema(schema).parquet(input_path)
    
    # Normalize names
    entities_df = normalize_name(entities_df, "name")
    
    # Add blocking keys for efficient matching
    entities_df = entities_df.withColumn(
        "soundex_key",
        soundex(col("name_normalized"))
    ).withColumn(
        "first_char",
        col("name_normalized").substr(0, 1)
    )
    
    # Self-join within blocks for candidate pairs
    print("Generating candidate pairs within blocks...")
    
    candidates = (
        entities_df.alias("a")
        .join(
            entities_df.alias("b"),
            (col("a.soundex_key") == col("b.soundex_key")) &
            (col("a.first_char") == col("b.first_char")) &
            (col("a.id") < col("b.id"))
        )
        .select(
            col("a.id").alias("id_a"),
            col("a.name_normalized").alias("name_a"),
            col("b.id").alias("id_b"),
            col("b.name_normalized").alias("name_b")
        )
    )
    
    # Calculate similarity
    print(f"Calculating similarity scores (threshold: {threshold})...")
    similar_pairs = calculate_name_similarity(
        candidates, "name_a", "name_b", threshold
    )
    
    # Create clusters using connected components approach
    print("Clustering similar entities...")
    
    # Build edges for graph
    edges = similar_pairs.select(
        col("id_a").alias("src"),
        col("id_b").alias("dst"),
        col("name_similarity").alias("weight")
    )
    
    # Simple Union-Find clustering via aggregation
    # Group by source and collect all matches
    clusters = (
        edges
        .groupBy("src")
        .agg(
            collect_list("dst").alias("matched_ids"),
            avg("weight").alias("avg_similarity")
        )
        .withColumn("cluster_id", col("src"))
    )
    
    # Generate resolved entities
    print("Generating resolved entity records...")
    
    resolved = (
        clusters
        .join(entities_df, clusters.src == entities_df.id)
        .select(
            col("cluster_id").alias("resolved_entity_id"),
            col("id").alias("source_id"),
            col("name"),
            col("entity_type"),
            col("source_system"),
            col("avg_similarity").alias("confidence_score")
        )
    )
    
    # Calculate resolution statistics
    stats = resolved.agg(
        count("*").alias("total_records"),
        count("resolved_entity_id").alias("resolved_entities"),
        avg("confidence_score").alias("avg_confidence")
    ).collect()[0]
    
    print(f"Resolution Statistics:")
    print(f"  Total Records: {stats['total_records']}")
    print(f"  Resolved Entities: {stats['resolved_entities']}")
    print(f"  Average Confidence: {stats['avg_confidence']:.3f}")
    
    # Write results
    print(f"Writing resolved entities to {output_path}")
    resolved.write.mode("overwrite").parquet(output_path)
    
    return resolved


def main():
    parser = argparse.ArgumentParser(description="FTex Entity Resolution Job")
    parser.add_argument("--input", required=True, help="Input path for entity data")
    parser.add_argument("--output", required=True, help="Output path for resolved entities")
    parser.add_argument("--threshold", type=float, default=0.8, help="Similarity threshold")
    
    args = parser.parse_args()
    
    spark = create_spark_session()
    
    try:
        resolve_entities(spark, args.input, args.output, args.threshold)
        print("Entity resolution completed successfully!")
    except Exception as e:
        print(f"Error during entity resolution: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

