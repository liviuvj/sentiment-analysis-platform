# Script to start the Spark Shell and connect to MongoDB
spark-shell --conf "spark.mongodb.input.uri=mongodb://mongoroot:mongopassword@mongo-db:27017/raw_twitter.airbyte_tmp_bgr__0133_tweets_advanced?authSource=admin" \
--conf "spark.mongodb.output.uri=mongodb://mongoroot:mongopassword@mongo-db:27017/raw_twitter.airbyte_0133_tweets_advanced?authSource=admin" \
--packages org.mongodb.spark:mongo-spark-connector_2.12:3.0.1
--conf "spark.DATA_SOURCE=fuente" --conf "spark.SEARCH_QUERY=datos"

# Script to start the Spark Shell and connect to MongoDB
spark-shell --conf "spark.mongodb.input.uri=mongodb://mongoroot:mongopassword@mongo-db:27017/raw_dataset.airbyte_raw_jon?authSource=admin" \
--conf "spark.mongodb.output.uri=mongodb://mongoroot:mongopassword@mongo-db:27017/raw_dataset.airbyte_raw_jon?authSource=admin" \
--packages org.mongodb.spark:mongo-spark-connector_2.12:3.0.1
--conf "spark.DATA_SOURCE=fuente" --conf "spark.SEARCH_QUERY=datos"