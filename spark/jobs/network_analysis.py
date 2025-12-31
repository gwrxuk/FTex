"""
Network Analysis Spark Job

Graph-based analysis for detecting suspicious networks,
money laundering patterns, and hidden relationships.
"""

from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col, count, sum as spark_sum, avg, collect_list,
    explode, array, struct, lit, when, max as spark_max,
    min as spark_min, stddev, dense_rank, row_number
)
from pyspark.sql.types import (
    StructType, StructField, StringType, DoubleType,
    ArrayType, IntegerType, TimestampType
)
from pyspark.sql.window import Window
from graphframes import GraphFrame
import argparse


def create_spark_session():
    """Create Spark session with GraphFrames support."""
    return (SparkSession.builder
            .appName("FTex Network Analysis")
            .config("spark.jars.packages", "graphframes:graphframes:0.8.2-spark3.2-s_2.12")
            .config("spark.sql.adaptive.enabled", "true")
            .getOrCreate())


def build_transaction_graph(spark, transactions_df, entities_df):
    """
    Build a graph from transactions and entities.
    
    Vertices: Entities
    Edges: Transactions between entities
    """
    # Prepare vertices
    vertices = (
        entities_df
        .select(
            col("id"),
            col("name").alias("name"),
            col("entity_type").alias("type"),
            col("risk_score").alias("risk"),
            col("is_sanctioned").alias("sanctioned"),
            col("is_pep").alias("pep")
        )
    )
    
    # Prepare edges
    edges = (
        transactions_df
        .select(
            col("sender_entity_id").alias("src"),
            col("receiver_entity_id").alias("dst"),
            col("id").alias("transaction_id"),
            col("amount"),
            col("currency"),
            col("transaction_date"),
            col("risk_score").alias("tx_risk")
        )
        .filter(col("src").isNotNull() & col("dst").isNotNull())
    )
    
    return GraphFrame(vertices, edges)


def detect_circular_flows(graph, max_path_length=5, min_amount=10000):
    """
    Detect circular transaction flows (potential layering).
    
    Looks for cycles where money flows back to the source.
    """
    # Find motifs representing cycles
    # Pattern: A sends to B sends to C sends back to A
    cycles = graph.find("(a)-[e1]->(b); (b)-[e2]->(c); (c)-[e3]->(a)")
    
    suspicious_cycles = (
        cycles
        .filter(col("e1.amount") >= min_amount)
        .filter(col("e2.amount") >= min_amount)
        .filter(col("e3.amount") >= min_amount)
        .withColumn(
            "total_flow",
            col("e1.amount") + col("e2.amount") + col("e3.amount")
        )
        .withColumn(
            "avg_flow",
            (col("e1.amount") + col("e2.amount") + col("e3.amount")) / 3
        )
        .select(
            col("a.id").alias("entity_a"),
            col("b.id").alias("entity_b"),
            col("c.id").alias("entity_c"),
            col("total_flow"),
            col("avg_flow"),
            array(
                col("e1.transaction_id"),
                col("e2.transaction_id"),
                col("e3.transaction_id")
            ).alias("transaction_ids")
        )
    )
    
    return suspicious_cycles


def calculate_pagerank(graph, reset_probability=0.15, max_iterations=20):
    """
    Calculate PageRank to identify central entities in the network.
    """
    pr_results = graph.pageRank(
        resetProbability=reset_probability,
        maxIter=max_iterations
    )
    
    return pr_results.vertices.select(
        col("id"),
        col("name"),
        col("type"),
        col("pagerank").alias("centrality_score")
    ).orderBy(col("pagerank").desc())


def detect_communities(graph, max_iterations=10):
    """
    Detect communities/clusters using label propagation.
    """
    communities = graph.labelPropagation(maxIter=max_iterations)
    
    community_stats = (
        communities
        .groupBy("label")
        .agg(
            count("*").alias("size"),
            collect_list("id").alias("member_ids"),
            avg("risk").alias("avg_risk"),
            spark_sum(when(col("sanctioned") == 1, 1).otherwise(0)).alias("sanctioned_count"),
            spark_sum(when(col("pep") == 1, 1).otherwise(0)).alias("pep_count")
        )
        .withColumn(
            "community_risk",
            when(col("sanctioned_count") > 0, 0.9)
            .when(col("pep_count") > 0, 0.7)
            .when(col("avg_risk") >= 0.5, 0.6)
            .otherwise(col("avg_risk"))
        )
        .orderBy(col("community_risk").desc())
    )
    
    return communities, community_stats


def detect_rapid_passthrough(graph, time_window_hours=24, min_passthrough_ratio=0.9):
    """
    Detect rapid pass-through entities (potential shell companies/mules).
    
    These entities receive and forward funds quickly without retaining them.
    """
    # Calculate incoming and outgoing flows per entity
    incoming = (
        graph.edges
        .groupBy("dst")
        .agg(
            spark_sum("amount").alias("total_incoming"),
            count("*").alias("incoming_count")
        )
    )
    
    outgoing = (
        graph.edges
        .groupBy("src")
        .agg(
            spark_sum("amount").alias("total_outgoing"),
            count("*").alias("outgoing_count")
        )
    )
    
    passthrough = (
        incoming.alias("i")
        .join(outgoing.alias("o"), col("i.dst") == col("o.src"))
        .select(
            col("i.dst").alias("entity_id"),
            col("total_incoming"),
            col("total_outgoing"),
            col("incoming_count"),
            col("outgoing_count")
        )
        .withColumn(
            "passthrough_ratio",
            col("total_outgoing") / col("total_incoming")
        )
        .filter(col("passthrough_ratio") >= min_passthrough_ratio)
        .filter(col("passthrough_ratio") <= 1.1)  # Allow small buffer
        .filter(col("incoming_count") >= 3)
        .withColumn("risk_indicator", lit("rapid_passthrough"))
    )
    
    return passthrough


def find_bridge_entities(graph):
    """
    Find bridge entities that connect otherwise separate communities.
    
    These may be facilitators of illicit flows between networks.
    """
    # Calculate degrees
    in_degrees = (
        graph.inDegrees
        .withColumnRenamed("inDegree", "in_degree")
    )
    
    out_degrees = (
        graph.outDegrees
        .withColumnRenamed("outDegree", "out_degree")
    )
    
    degrees = (
        in_degrees.alias("i")
        .join(out_degrees.alias("o"), "id")
        .withColumn("total_degree", col("in_degree") + col("out_degree"))
    )
    
    # Find entities with high betweenness (simplified - degree-based proxy)
    window = Window.orderBy(col("total_degree").desc())
    
    bridge_candidates = (
        degrees
        .withColumn("degree_rank", dense_rank().over(window))
        .filter(col("degree_rank") <= 50)  # Top 50 by degree
        .join(graph.vertices, "id")
        .select(
            col("id"),
            col("name"),
            col("type"),
            col("in_degree"),
            col("out_degree"),
            col("total_degree"),
            col("risk").alias("entity_risk")
        )
    )
    
    return bridge_candidates


def analyze_flow_patterns(graph, min_flow=10000):
    """
    Analyze transaction flow patterns for suspicious activity.
    """
    # Aggregate flows between entity pairs
    flows = (
        graph.edges
        .groupBy("src", "dst")
        .agg(
            count("*").alias("transaction_count"),
            spark_sum("amount").alias("total_flow"),
            avg("amount").alias("avg_flow"),
            stddev("amount").alias("std_flow"),
            spark_min("transaction_date").alias("first_tx"),
            spark_max("transaction_date").alias("last_tx")
        )
        .filter(col("total_flow") >= min_flow)
    )
    
    # Detect reciprocal flows (money moving back and forth)
    reciprocal = (
        flows.alias("a")
        .join(
            flows.alias("b"),
            (col("a.src") == col("b.dst")) & (col("a.dst") == col("b.src"))
        )
        .select(
            col("a.src").alias("entity_1"),
            col("a.dst").alias("entity_2"),
            col("a.total_flow").alias("flow_1_to_2"),
            col("b.total_flow").alias("flow_2_to_1"),
            col("a.transaction_count").alias("tx_count_1_to_2"),
            col("b.transaction_count").alias("tx_count_2_to_1")
        )
        .withColumn(
            "net_flow",
            col("flow_1_to_2") - col("flow_2_to_1")
        )
        .withColumn(
            "reciprocity_score",
            when(
                col("flow_1_to_2") > col("flow_2_to_1"),
                col("flow_2_to_1") / col("flow_1_to_2")
            ).otherwise(
                col("flow_1_to_2") / col("flow_2_to_1")
            )
        )
        .filter(col("reciprocity_score") >= 0.7)  # High reciprocity
        .withColumn("pattern_type", lit("reciprocal_flow"))
    )
    
    return flows, reciprocal


def run_network_analysis(spark, tx_path, entity_path, output_path):
    """
    Run complete network analysis pipeline.
    """
    print("Loading data...")
    
    transactions_df = spark.read.parquet(tx_path)
    entities_df = spark.read.parquet(entity_path)
    
    print("Building transaction graph...")
    graph = build_transaction_graph(spark, transactions_df, entities_df)
    
    print(f"Graph Statistics:")
    print(f"  Vertices: {graph.vertices.count()}")
    print(f"  Edges: {graph.edges.count()}")
    
    # Run analyses
    print("\nRunning PageRank centrality analysis...")
    pagerank = calculate_pagerank(graph)
    pagerank.write.mode("overwrite").parquet(f"{output_path}/pagerank")
    
    print("Detecting communities...")
    communities, community_stats = detect_communities(graph)
    community_stats.write.mode("overwrite").parquet(f"{output_path}/communities")
    
    print("Detecting circular flows...")
    cycles = detect_circular_flows(graph)
    cycles.write.mode("overwrite").parquet(f"{output_path}/circular_flows")
    
    print("Detecting rapid passthrough entities...")
    passthrough = detect_rapid_passthrough(graph)
    passthrough.write.mode("overwrite").parquet(f"{output_path}/passthrough")
    
    print("Finding bridge entities...")
    bridges = find_bridge_entities(graph)
    bridges.write.mode("overwrite").parquet(f"{output_path}/bridges")
    
    print("Analyzing flow patterns...")
    flows, reciprocal = analyze_flow_patterns(graph)
    reciprocal.write.mode("overwrite").parquet(f"{output_path}/reciprocal_flows")
    
    # Summary
    print("\nNetwork Analysis Summary:")
    print(f"  High Centrality Entities: {pagerank.filter(col('centrality_score') >= 1.0).count()}")
    print(f"  Communities Detected: {community_stats.count()}")
    print(f"  Suspicious Cycles: {cycles.count()}")
    print(f"  Passthrough Entities: {passthrough.count()}")
    print(f"  Bridge Entities: {bridges.count()}")
    print(f"  Reciprocal Flow Pairs: {reciprocal.count()}")


def main():
    parser = argparse.ArgumentParser(description="FTex Network Analysis")
    parser.add_argument("--transactions", required=True, help="Path to transaction data")
    parser.add_argument("--entities", required=True, help="Path to entity data")
    parser.add_argument("--output", required=True, help="Output path for analysis results")
    
    args = parser.parse_args()
    
    spark = create_spark_session()
    
    try:
        run_network_analysis(spark, args.transactions, args.entities, args.output)
        print("Network analysis completed successfully!")
    except Exception as e:
        print(f"Error during network analysis: {e}")
        raise
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

