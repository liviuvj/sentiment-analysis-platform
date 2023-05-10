// Imports
import org.apache.spark.sql.functions.explode
import com.mongodb.spark._

// Extract raw data
val rawDF = spark.read.format("mongo").load()
val rawDataDF = rawDF.select($"_airbyte_data.data.id", explode($"_airbyte_data.data") as "tweet_data")
val rawMentionsDF = rawDF.select($"_airbyte_data.data.id", explode($"_airbyte_data.data.entities.mentions") as "mentions")
val rawURLsDF = rawDF.select($"_airbyte_data.data.id", explode($"_airbyte_data.data.entities.urls") as "urls")
val rawHashtagsDF = rawDF.select($"_airbyte_data.data.id", explode($"_airbyte_data.data.entities.hashtags") as "hashtags")
val rawAnnotationsDF = rawDF.select($"_airbyte_data.data.id", explode($"_airbyte_data.data.entities.annotations") as "annotations")
val rawContextAnnotationsDF = rawDF.select($"_airbyte_data.data.id", explode($"_airbyte_data.data.context_annotations") as "context_annotations")
val rawPlacesDF = rawDF.select($"_airbyte_data.data.id", explode($"_airbyte_data.includes.places") as "place_data")
val rawUsersDF = rawDF.select(explode($"_airbyte_data.includes.users") as "user_data")

// Create tweets Dataframe
val tweetsDF = rawDataDF.select(
    $"tweet_data.id".alias("tweet_id"),
    $"tweet_data.author_id".alias("user_id"),
    $"tweet_data.created_at".alias("created_at"),
    $"tweet_data.lang".alias("language"),
    $"tweet_data.text".alias("text"),
    $"tweet_data.public_metrics.retweet_count".alias("retweet_count"),
    $"tweet_data.public_metrics.reply_count".alias("reply_count"),
    $"tweet_data.public_metrics.like_count".alias("like_count"),
    $"tweet_data.public_metrics.quote_count".alias("quote_count")
)

// Create user Dataframe
val usersDF = rawUsersDF.select(
    $"user_data.id".alias("user_id"),
    $"user_data.name".alias("name"),
    $"user_data.username".alias("username"),
    $"user_data.description".alias("description"),
    $"user_data.location".alias("location"),
    $"user_data.public_metrics.followers_count".alias("followers_count"),
    $"user_data.public_metrics.following_count".alias("following_count"),
    $"user_data.public_metrics.tweet_count".alias("tweet_count"),
    $"user_data.public_metrics.listed_count".alias("listed_count")
)

// Create place DataFrame
val placesDF = rawPlacesDF.select(
    $"id".alias("tweet_id"),
    $"place_data.id".alias("country_id"),
    $"place_data.country".alias("country"),
    $"place_data.country_code".alias("country_code"),
    $"place_data.full_name".alias("full_name"),
    $"place_data.geo.bbox".alias("geo"),
    $"place_data.place_type".alias("place_type")
)

// Create mentions DataFrame
val mentionsDF = rawMentionsDF.select(
    $"id".alias("tweet_id"),
    $"mentions.username".alias("username")
)

// Save clean data back to MongoDB
tweetsDF.write.format("mongo").mode("append").option("collection", "clean_tweets").save()
usersDF.write.format("mongo").mode("append").option("collection", "clean_users").save()
placesDF.write.format("mongo").mode("append").option("collection", "clean_places").save()
mentionsDF.write.format("mongo").mode("append").option("collection", "clean_mentions").save()
