from transformers import pipeline
import pymongo

# Connecto to MongoDB
client = pymongo.MongoClient("mongodb://mongoroot:mongopassword@mongo-db:27017/raw_tweets?authSource=admin")

# Select database and collections
db = client["raw_twitter"]
collection_tweets = db["clean_tweets"]
collection_users = db["clean_users"]
collection_mentions = db["clean_mentions"]
collection_annotations = db["clean_annotations"]
collection_context_annotations = db["clean_context_annotations"]
collection_urls = db["clean_urls"]
collection_hashtags = db["clean_hashtags"]

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

# Topic classification
for id, entity in enumerate(ner_classifier(data_iterator(tweets_english))):
    tweets_english[id]["entity"] = entity["label"]

# Export data to OLAP DB
