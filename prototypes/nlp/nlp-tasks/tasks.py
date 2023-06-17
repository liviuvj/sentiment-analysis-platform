from transformers import pipeline

# from pymongo import MongoClient
# from connectors import ClickHouseConnector

# Connecto to MongoDB
# mongo_client = MongoClient("mongodb://mongoroot:mongopassword@mongo-db:27017/raw_tweets?authSource=admin")

# Select database and collections
# db = mongo_client["raw_twitter"]
# collection_tweets = db["clean_tweets"].find()
# collection_users = db["clean_users"].find()
# collection_mentions = db["clean_mentions"].find()
# collection_annotations = db["clean_annotations"].find()
# collection_context_annotations = db["clean_context_annotations"].find()
# collection_urls = db["clean_urls"].find()
# collection_hashtags = db["clean_hashtags"].find()

from utils import get_logger

log = get_logger("tasks")


class TaskPipeline:
    def __init__(
        self,
        sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest",
        emotion_model: str = "cardiffnlp/twitter-roberta-base-emotion",
        topic_model: str = "cardiffnlp/tweet-topic-21-multi",
        ner_model: str = "tner/twitter-roberta-base-dec2021-tweetner7-all",
    ) -> None:
        self.sentiment_classifier = pipeline(
            "sentiment-analysis", model=sentiment_model
        )
        self.emotion_classifier = pipeline("sentiment-analysis", model=emotion_model)
        self.topic_classifier = pipeline("sentiment-analysis", model=topic_model)
        self.ner_classifier = pipeline("sentiment-analysis", model=ner_model)

    # Create iterator for the data
    #
    # TODO: not all sources might come with this format,
    # consider moving out this function
    def data_iterator(self, data):
        for d in data:
            yield d["text"]

    def task_sentiment_classification(self, data):
        # Sentiment classification

        log.info("Running sentiment classification...")

        for id, sentiment in enumerate(
            self.sentiment_classifier(self.data_iterator(data))
        ):
            data[id]["sentiment"] = sentiment["label"]

    def task_emotion_classification(self, data):
        # Emotion classification

        log.info("Running emotion classification...")

        for id, emotion in enumerate(self.emotion_classifier(self.data_iterator(data))):
            data[id]["emotion"] = emotion["label"]

    def task_topic_classification(self, data):
        # Topic classification

        log.info("Running topic classification...")

        for id, topic in enumerate(self.topic_classifier(self.data_iterator(data))):
            data[id]["topic"] = topic["label"]

    def task_entity_classification(self, data):
        # Entity classification

        log.info("Running entity classification...")

        for id, entity in enumerate(self.ner_classifier(self.data_iterator(data))):
            data[id]["entity"] = entity["label"]

    def run_all_tasks(self, data):
        self.task_sentiment_classification(data)
        self.task_emotion_classification(data)
        self.task_topic_classification(data)
        self.task_entity_classification(data)


class TaskTwitterInput:
    def __init__(self) -> None:
        # Connection credentials
        self.database_host = "mongo-db"
        self.database_port = 27017
        self.database_username = "mongoroot"
        self.database_password = "mongopassword"

        # Database and collection names
        self.database_name = "raw_twitter"
        self.tweets = "clean_tweets"
        self.users = "clean_users"
        self.mentions = "clean_mentions"
        self.annotations = "clean_annotations"
        self.context_annotations = "clean_context_annotations"
        self.urls = "clean_urls"
        self.hashtags = "clean_hashtags"


class TaskTwitterOutput:
    def __init__(self) -> None:
        # Connection credentials
        self.database_host = "clickhouse"
        self.database_port = 9000
        self.database_username = "ck_user"
        self.database_password = "ck_password"

        # Database name
        self.database_name = "twitter"

        # Table definitions

        self.tweets = {
            "name": "tweets",
            "columns": {
                "tweet_id": "String",
                "user_id": "String",
                "created_at": "Datetime",
                "language": "FixedString(2)",
                "text": "String",
                "retweet_count": "Int32",
                "reply_count": "Int32",
                "like_count": "Int32",
                "quote_count": "Int32",
                "sentiment": "String",
                "emotion": "String",
                "topic": "String",
                "entity": "String",
            },
        }

        self.users = {
            "name": "users",
            "columns": {
                "user_id": "String",
                "name": "String",
                "username": "String",
                "description": "String",
                "followers_count": "Int32",
                "following_count": "Int32",
                "tweet_count": "Int32",
                "listed_count": "Int32",
            },
        }

        self.mentions = {
            "name": "mentions",
            "columns": {
                "tweet_id": "String",
                "user_id": "String",
                "username": "String",
            },
        }

        self.annotations = {
            "name": "annotations",
            "columns": {"tweet_id": "String", "type": "String", "annotation": "String"},
        }

        self.context_annotations = {
            "name": "context_annotations",
            "columns": {"tweet_id": "String", "domain": "String", "entity": "String"},
        }

        self.urls = {"name": "urls", "columns": {"tweet_id": "String", "display_url": "String"}}

        self.hashtags = {
            "name": "hashtags",
            "columns": {"tweet_id": "String", "tag": "String"},
        }



# Get tweet texts
# tweets_english = [doc for doc in collection_tweets if doc["language"] == "en"]

# Define OLAP DB params
# db_name = "twitter"
# table_name = "tweets"
# tweets_params = {
#     "tweet_id": "String",
#     "user_id": "String",
#     "created_at": "Datetime",
#     "language": "FixedString(2)",
#     "text": "String",
#     "retweet_count": "Int32",
#     "reply_count": "Int32",
#     "like_count": "Int32",
#     "quote_count": "Int32",
#     "sentiment": "String",
#     "emotion": "String",
#     "topic": "String",
#     "entity": "String",
# }

# # Create ClickHouse client
# ck_client = ClickHouseConnector(
#     host="clickhouse", port=9000, user="ck_user", password="ck_password"
# )

# # Create database
# ck_client.create_database(db_name)
# ck_client.use_database(db_name)

# # Create table
# ck_client.create_table(table_name, tweets_params, "tweet_id", "tweet_id")

# # Insert data
# ck_client.insert_into_table(
#     table_name, list(tweets_params.keys()), clean(tweets_english)
# )
