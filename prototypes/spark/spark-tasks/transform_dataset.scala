// Imports
import org.apache.spark.sql.functions.{explode, split}
import com.mongodb.spark._

// Get config arg
val dataSource = sc.getConf.get("spark.DATA_SOURCE")
val searchQuery = sc.getConf.get("spark.SEARCH_QUERY")

// Extract raw data
val rawDF = spark.read.option("encoding", "ISO-8859-1").format("mongo").load()
val rawDataDF = rawDF.select($"_airbyte_data.*")

// Create tweets Dataframe
val tweetsDF = rawDataDF.select(
    $"status_id".alias("tweet_id"),
    lit(dataSource).alias("source"),
    lit(searchQuery).alias("search_query"),
    $"user_id".alias("user_id"),
    $"created_at".alias("created_at"),
    $"lang".alias("language"),
    $"text".alias("text"),
    $"retweet_count".alias("retweet_count"),
    $"favorite_count".alias("like_count")
)

// Create user Dataframe
val usersDF = rawDataDF.select(
    $"user_id".alias("user_id"),
    $"name".alias("name"),
    $"screen_name".alias("username"),
    $"description".alias("description"),
    $"followers_count".alias("followers_count"),
    $"friends_count".alias("following_count"),
    $"statuses_count".alias("tweet_count"),
    $"listed_count".alias("listed_count")
)

// Create mentions DataFrame
val mentionsDF = rawDataDF.
    filter($"mentions_user_id".isNotNull).
    select(
        $"status_id".alias("tweet_id"),
        $"mentions_user_id".alias("user_id"),
        $"mentions_screen_name".alias("username")
    )

// Create annotations DataFrame
val urlsDF = rawDataDF.
    filter($"urls_url".isNotNull).
    select(
        $"status_id".alias("tweet_id"),
        $"urls_url".alias("display_url")
    )

// Create hashtags DataFrame
val hashtagsDF = rawDataDF.
    filter($"hashtags".isNotNull).
    select(
        $"status_id".alias("tweet_id"),
        explode(split($"hashtags", " ")).alias("tag")
    )

// Clean DataFrames by dropping null values and duplicates
val cleanTweetsDF = tweetsDF.dropDuplicates
val cleanMentionsDF = mentionsDF.na.drop.dropDuplicates
val cleanUrlsDF = urlsDF.dropDuplicates
val cleanHashtagsDF = hashtagsDF.dropDuplicates

// This data schema needs to be deduplicated based on both the "user_id" field and the "tweet_count" field.
// The higher the "tweet_count", the more recent and correct the data is.
val cleanUsersDF = usersDF.
    groupBy("user_id").
    agg(max("tweet_count").as("tweet_count")).
    join(usersDF, Seq("user_id", "tweet_count")).
    dropDuplicates("user_id").
    select(
        "user_id", "name", "username", "description",
        "followers_count", "following_count",
        "tweet_count", "listed_count").
    na.fill("", Array("description"))

// Save clean data back to MongoDB
cleanTweetsDF.write.format("mongo").mode("append").option("collection", "clean_tweets").save()
cleanUsersDF.write.format("mongo").mode("append").option("collection", "clean_users").save()
cleanMentionsDF.write.format("mongo").mode("append").option("collection", "clean_mentions").save()
cleanUrlsDF.write.format("mongo").mode("append").option("collection", "clean_urls").save()
cleanHashtagsDF.write.format("mongo").mode("append").option("collection", "clean_hashtags").save()
