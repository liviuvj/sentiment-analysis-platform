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
tweet_texts = [doc["text"] for doc in documents]

# Create sentiment analysis pipeline
classifier = pipeline("sentiment-analysis")

# Run classifier on tweets
results = classifier(["We are very happy to show you the 🤗 Transformers library.", "We hope you don't hate it."])
for result in results:
    print(f"label: {result['label']}, with score: {round(result['score'], 4)}")
