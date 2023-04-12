# Script to start the Spark Shell and connect to MongoDB
spark-shell --conf "spark.mongodb.input.uri=mongodb://mongoroot:mongopassword@localhost:27017/raw_twitter.airbyte_tmp_dbn_tweets?readPreference=primaryPreferred" \
--conf "spark.mongodb.output.uri=mongodb://mongoroot:mongopassword@localhost:27017/raw_twitter.airbyte_tmp_dbn_tweets" \
--packages org.mongodb.spark:mongo-spark-connector_2.12:3.0.1