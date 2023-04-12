import com.mongodb.spark._

val rawDF = spark.read.format("mongo").load()

val data = df.select("_airbyte_data.created_at",
                    "_airbyte_data.author_id",
                    "_airbyte_data.text",
                    "_airbyte_data.public_metrics",
                    "_airbyte_data.entities",
                    "_airbyte_data.context_annotations")

MongoSpark.save(data)