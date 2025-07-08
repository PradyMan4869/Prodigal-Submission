import argparse
from pyspark.sql import SparkSession
from pyspark.sql.functions import col

def create_features(spark, input_path, output_path):
    print(f"Reading ingested data from {input_path}")
    df = spark.read.parquet(input_path)
    df_featured = df.withColumn("rooms_per_person", col("total_rooms") / col("population"))
    df_featured = df_featured.withColumn("bedrooms_per_room", col("total_bedrooms") / col("total_rooms"))
    print(f"Writing featured data to {output_path}")
    df_featured.write.mode("overwrite").parquet(output_path)
    print("Feature engineering complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", required=True)
    parser.add_argument("--output_path", required=True)
    args = parser.parse_args()

    spark = SparkSession.builder.appName("FeatureEngineering").getOrCreate()
    create_features(spark, args.input_path, args.output_path)
    spark.stop()
