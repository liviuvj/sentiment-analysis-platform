// Imports
import org.apache.spark.sql.functions.explode
import com.mongodb.spark._

// Extract raw data
val rawDF = spark.read.format("mongo").load()
val rawDataDF = rawDF.select($"_airbyte_data.data.id", explode($"_airbyte_data.data") as "tweet_data")
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

// Join clean data
val cleanDF = tweetsDF.join(usersDF, Seq("user_id"))

// Save clean data back to MongoDB
tweetsDF.write.format("mongo").mode("append").option("collection", "clean_tweets").save()
usersDF.write.format("mongo").mode("append").option("collection", "clean_users").save()
