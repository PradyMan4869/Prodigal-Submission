import argparse
from pyspark.sql import SparkSession

def ingest_data(spark, input_path, output_path):
    print(f"Reading data from {input_path}")
    df = spark.read.csv(input_path, header=True, inferSchema=True)
    df_cleaned = df.na.drop()
    print(f"Writing cleaned data to {output_path}")
    df_cleaned.write.mode("overwrite").parquet(output_path)
    print("Data ingestion complete.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_path", required=True)
    parser.add_argument("--output_path", required=True)
    args = parser.parse_args()

    spark = SparkSession.builder.appName("DataIngestion").getOrCreate()
    ingest_data(spark, args.input_path, args.output_path)
    spark.stop()
