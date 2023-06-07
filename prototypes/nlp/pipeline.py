from transformers import pipeline
from pymongo import MongoClient
from clickhouse_driver import Client as ClickClient
from datetime import datetime

# Connecto to MongoDB
mongo_client = MongoClient("mongodb://mongoroot:mongopassword@mongo-db:27017/raw_tweets?authSource=admin")
click_client = ClickClient(host='clickhouse', port=9000, user='ck_user', password='ck_password')

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
def remove_mongo_id(collection):
    for object in collection:
        dt = datetime.strptime(object["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ")
        object["created_at"] = dt
        # object.pop("_id")
        yield object

# Get data
tweets = collection_tweets.find()

# Get tweet texts
tweets_english = [doc for doc in tweets if doc["language"] == "en"]

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
columns = ['tweet_id', 'user_id', 'created_at', 'language', 'text', 'retweet_count', 'reply_count', 'like_count', 'quote_count', 'sentiment', 'emotion', 'topic', 'entity']
data_types = ['String', 'String', 'Datetime', 'FixedString(2)', 'String', 'Int32', 'Int32', 'Int32', 'Int32', 'String', 'String', 'String', 'String']

# Export data to OLAP DB
click_client.execute("CREATE DATABASE IF NOT EXISTS " + db_name)
click_client.execute("USE " + db_name)

click_client.execute('CREATE TABLE IF NOT EXISTS ' + table_name + \
                     ' (' + str(", ".join([f"{col} {data_type}" for col, data_type in zip(columns, data_types)])) + ')' + \
                     ' ENGINE = MergeTree() PRIMARY KEY ' + columns[0] + ' ORDER BY ' + columns[0])

click_client.execute("SHOW TABLES")
# click_client.execute("DROP TABLE IF EXISTS " + table_name)

click_client.execute("INSERT INTO " + table_name + "(" + ", ".join(columns) + ")" + "VALUES",
                     tweets_english[:5])
