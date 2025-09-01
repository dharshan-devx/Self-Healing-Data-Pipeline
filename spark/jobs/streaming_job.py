from pyspark.sql import SparkSession
from pyspark.sql.functions import col, from_json
from pyspark.sql.types import (
    StructType, StructField, StringType, IntegerType,
    DoubleType, LongType
)
import os

# -------------------------------------------------------------------
# Config
# -------------------------------------------------------------------
KAFKA_BROKER = os.getenv("KAFKA_BROKER", "broker:29092")
KAFKA_TOPIC = "events"
DATA_DIR = "/opt/data"

# Schema for incoming Kafka events
schema = StructType([
    StructField("user_id", IntegerType(), True),
    StructField("event_id", StringType(), True),
    StructField("event_type", StringType(), True),
    StructField("timestamp", LongType(), True),
    StructField("product_id", StringType(), True),
    StructField("category", StringType(), True),
    StructField("price", DoubleType(), True),
])

# -------------------------------------------------------------------
# Spark Session
# -------------------------------------------------------------------
spark = (
    SparkSession.builder.appName("KafkaSparkStreamingJob")
    .config("spark.sql.extensions", "io.delta.sql.DeltaSparkSessionExtension")
    .config("spark.sql.catalog.spark_catalog", "org.apache.spark.sql.delta.catalog.DeltaCatalog")
    .getOrCreate()
)

spark.sparkContext.setLogLevel("WARN")

# -------------------------------------------------------------------
# Read Stream from Kafka
# -------------------------------------------------------------------
raw_stream = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", KAFKA_BROKER)
    .option("subscribe", KAFKA_TOPIC)
    .option("startingOffsets", "earliest")
    .load()
)

# Parse value as JSON
parsed_stream = (
    raw_stream.selectExpr("CAST(value AS STRING) as json_value")
    .select(from_json(col("json_value"), schema).alias("data"))
    .select("data.*")
)

# -------------------------------------------------------------------
# Write to Delta Lake (Bronze layer)
# -------------------------------------------------------------------
bronze_path = f"{DATA_DIR}/bronze/events"

bronze_writer = (
    parsed_stream.writeStream
    .format("delta")
    .option("checkpointLocation", f"{DATA_DIR}/checkpoints/bronze")
    .outputMode("append")
    .start(bronze_path)
)

# -------------------------------------------------------------------
# Simple Quality Gate (self-healing quarantine)
# Example: filter out invalid rows
# -------------------------------------------------------------------
valid_data = parsed_stream.filter(
    (col("user_id").isNotNull()) &
    (col("event_id").isNotNull()) &
    (col("product_id").isNotNull()) &
    (col("price") >= 0.0) & (col("price") <= 1000.0)
)

invalid_data = parsed_stream.exceptAll(valid_data)

# Write valid data → Silver
silver_path = f"{DATA_DIR}/silver/events"
(
    valid_data.writeStream
    .format("delta")
    .option("checkpointLocation", f"{DATA_DIR}/checkpoints/silver")
    .outputMode("append")
    .start(silver_path)
)

# Write invalid data → Quarantine
quarantine_path = f"{DATA_DIR}/quarantine/events"
(
    invalid_data.writeStream
    .format("delta")
    .option("checkpointLocation", f"{DATA_DIR}/checkpoints/quarantine")
    .outputMode("append")
    .start(quarantine_path)
)

# -------------------------------------------------------------------
# Await Termination
# -------------------------------------------------------------------
spark.streams.awaitAnyTermination()
