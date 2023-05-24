// Imports
import org.apache.spark.sql.functions.explode
import com.mongodb.spark._

// Extract raw data
val rawDF = spark.read.option("encoding", "ISO-8859-1").format("mongo").load()
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

// Create mentions DataFrame
val mentionsDF = rawDataDF.filter(
    $"tweet_data.entities.mentions".isNotNull
    ).select(
        $"tweet_data.id".alias("tweet_id"),
        explode($"tweet_data.entities.mentions").alias("mentions")
    ).select($"tweet_id", $"mentions.*").
    select($"tweet_id", $"id".alias("user_id"), $"username")

// Create annotations DataFrame
val annotationsDF = rawDataDF.select(
    $"tweet_data.id".alias("tweet_id"),
    explode($"tweet_data.entities.annotations").alias("annotations")
    ).select($"tweet_id", $"annotations.*").
    filter($"probability" > 0.9).
    select($"tweet_id", $"type", $"normalized_text".alias("annotation"))

// Create context annotations DataFrame
val contextAnnotationsDF = rawDataDF.select(
        $"tweet_data.id".alias("tweet_id"),
        explode($"tweet_data.context_annotations").alias("context_annotations")
    ).select($"tweet_id", $"context_annotations.*").
    select($"tweet_id", $"domain.name".alias("domain"), $"entity.name".alias("entity"))

// Create annotations DataFrame
val urlsDF = rawDataDF.select(
    $"tweet_data.id".alias("tweet_id"),
    explode($"tweet_data.entities.urls").alias("urls")
    ).select($"tweet_id", $"urls.*").
    select($"tweet_id", $"display_url")

// Create hashtags DataFrame
val hashtagsDF = rawDataDF.select(
    $"tweet_data.id".alias("tweet_id"),
    explode($"tweet_data.entities.hashtags").alias("hashtags")
    ).select($"tweet_id", $"hashtags.*").
    select($"tweet_id", $"tag")

// Clean DataFrames by dropping null values and duplicates
val cleanTweetsDF = tweetsDF.dropDuplicates
val cleanUsersDF = usersDF.dropDuplicates
val cleanMentionsDF = mentionsDF.na.drop.dropDuplicates
val cleanAnnotationsDF = annotationsDF.na.drop.dropDuplicates
val cleanContextAnnotationsDF = contextAnnotationsDF.na.drop.dropDuplicates
val cleanUrlsDF = urlsDF.dropDuplicates
val cleanHashtagsDF = hashtagsDF.dropDuplicates

// Save clean data back to MongoDB
cleanTweetsDF.write.format("mongo").mode("append").option("collection", "clean_tweets").save()
cleanUsersDF.write.format("mongo").mode("append").option("collection", "clean_users").save()
cleanMentionsDF.write.format("mongo").mode("append").option("collection", "clean_mentions").save()
cleanAnnotationsDF.write.format("mongo").mode("append").option("collection", "clean_annotations").save()
cleanContextAnnotationsDF.write.format("mongo").mode("append").option("collection", "clean_context_annotations").save()
cleanUrlsDF.write.format("mongo").mode("append").option("collection", "clean_urls").save()
cleanHashtagsDF.write.format("mongo").mode("append").option("collection", "clean_hashtags").save()
