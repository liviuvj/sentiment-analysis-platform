from transformers import pipeline
from pymongo import MongoClient
from datetime import datetime
from connectors import ClickHouseConnector

# Connecto to MongoDB
mongo_client = MongoClient("mongodb://mongoroot:mongopassword@mongo-db:27017/raw_tweets?authSource=admin")

# Select database and collections
db = mongo_client["raw_twitter"]
collection_tweets = db["clean_tweets"].find()
collection_users = db["clean_users"].find()
collection_mentions = db["clean_mentions"].find()
collection_annotations = db["clean_annotations"].find()
collection_context_annotations = db["clean_context_annotations"].find()
collection_urls = db["clean_urls"].find()
collection_hashtags = db["clean_hashtags"].find()

# Remove MongoDB ID
def clean(collection):
    for object in collection:
        # Convert field to daterime
        dt = datetime.strptime(object["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        object["created_at"] = dt

        # Remove MongoDB id
        object.pop("_id")

        yield object

# Get tweet texts
tweets_english = [doc for doc in collection_tweets if doc["language"] == "en"]

# Create analysis pipelines
sentiment_classifier = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
emotion_classifier = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-emotion")
topic_classifier = pipeline("sentiment-analysis", model="cardiffnlp/tweet-topic-21-multi")
ner_classifier = pipeline("sentiment-analysis", model="tner/twitter-roberta-base-dec2021-tweetner7-all")

# Create iterator for the data
def data_iterator(data):
    for d in data:
        yield d["text"]

# Sentiment classification
for id, sentiment in enumerate(sentiment_classifier(data_iterator(tweets_english))):
    tweets_english[id]["sentiment"] = sentiment["label"]

# Emotion classification
for id, emotion in enumerate(emotion_classifier(data_iterator(tweets_english))):
    tweets_english[id]["emotion"] = emotion["label"]

# Topic classification
for id, topic in enumerate(topic_classifier(data_iterator(tweets_english))):
    tweets_english[id]["topic"] = topic["label"]

# Entity classification
for id, entity in enumerate(ner_classifier(data_iterator(tweets_english))):
    tweets_english[id]["entity"] = entity["label"]

# Define OLAP DB params
db_name = 'twitter'
table_name = 'tweets'
tweets_params = {
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
}

# Create ClickHouse client
ck_client = ClickHouseConnector(host="clickhouse", port=9000, user="ck_user", password="ck_password")

# Create database
ck_client.create_database(db_name)
ck_client.use_database(db_name)

# Create table
ck_client.create_table(table_name, tweets_params, "tweet_id", "tweet_id")

# Insert data
ck_client.insert_into_table(table_name, list(tweets_params.keys()), clean(tweets_english))
