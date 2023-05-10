from transformers import pipeline
import pymongo

# Connecto to MongoDB
client = pymongo.MongoClient("mongodb://mongoroot:mongopassword@mongo-db:27017/raw_tweets?authSource=admin")

# Select database and collection
db = client["raw_twitter"]
collection = db["clean_tweets"]

# Get data
documents = collection.find()

# Get tweet texts
tweet_texts = [doc for doc in documents if doc["language"] == "en"]

# Create sentiment analysis pipelines
sentiment_classifier = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-sentiment-latest")
emotion_classifier = pipeline("sentiment-analysis", model="cardiffnlp/twitter-roberta-base-emotion")
topic_classifier = pipeline("sentiment-analysis", model="cardiffnlp/tweet-topic-21-multi")

def pipe(x):
    x["sentiment"] = sentiment_classifier(x["text"])[0]["label"]
    x["emotion"] = emotion_classifier(x["text"])[0]["label"]
    x["topic"] = topic_classifier(x["text"])[0]["label"]
    return x

for doc in tweet_texts:
    print(pipe(doc))
    break
