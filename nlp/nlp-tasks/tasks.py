from transformers import pipeline
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
        """
        Main class to run the Natural Language Processing tasks.

        Args:
            sentiment_model (str, optional): Sentiment analysis model.
                Defaults to "cardiffnlp/twitter-roberta-base-sentiment-latest".
            emotion_model (str, optional): Emotion classification model.
                Defaults to "cardiffnlp/twitter-roberta-base-emotion".
            topic_model (str, optional): Topic classification model.
                Defaults to "cardiffnlp/tweet-topic-21-multi".
            ner_model (str, optional): Named Entity Recognition model.
                Defaults to "tner/twitter-roberta-base-dec2021-tweetner7-all".
        """

        self.sentiment_classifier = pipeline(
            "sentiment-analysis", model=sentiment_model
        )
        self.emotion_classifier = pipeline("sentiment-analysis", model=emotion_model)
        self.topic_classifier = pipeline("sentiment-analysis", model=topic_model)
        self.ner_classifier = pipeline("sentiment-analysis", model=ner_model)

    def data_iterator(self, data, log_iterations=1000):
        # Create iterator for the data
        for i, d in enumerate(data, start=1):
            if not i % log_iterations:
                log.info(f"\t> Iterated over {i} instances")
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
    def __init__(
        self, db_username: str, db_password: str, db_host: str, db_port: int
    ) -> None:
        """
        Task that defines parameters for the input source of Twitter data.

        Args:
            db_username (str): Database username.
            db_password (str): Database password.
            db_host (str): Database host.
            db_port (int): Database port.
        """

        # Connection credentials
        self.database_username = db_username
        self.database_password = db_password
        self.database_host = db_host
        self.database_port = db_port

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
    def __init__(
        self, db_username: str, db_password: str, db_host: str, db_port: int
    ) -> None:
        """
        Task that defines parameters for the output destination of Twitter data.

        Args:
            db_username (str): Database username.
            db_password (str): Database password.
            db_host (str): Database host.
            db_port (int): Database port.
        """

        # Connection credentials
        self.database_username = db_username
        self.database_password = db_password
        self.database_host = db_host
        self.database_port = db_port

        # Database name
        self.database_name = "twitter"

        # Table definitions

        self.tweets = {
            "name": "tweets",
            "columns": {
                "tweet_id": "String",
                "source": "String",
                "search_query": "String",
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

        self.urls = {
            "name": "urls",
            "columns": {"tweet_id": "String", "display_url": "String"},
        }

        self.hashtags = {
            "name": "hashtags",
            "columns": {"tweet_id": "String", "tag": "String"},
        }


class TaskDatasetInput:
    def __init__(
        self, db_username: str, db_password: str, db_host: str, db_port: int
    ) -> None:
        """
        Task that defines parameters for the input source of Twitter data.

        Args:
            db_username (str): Database username.
            db_password (str): Database password.
            db_host (str): Database host.
            db_port (int): Database port.
        """

        # Connection credentials
        self.database_username = db_username
        self.database_password = db_password
        self.database_host = db_host
        self.database_port = db_port

        # Database and collection names
        self.database_name = "raw_dataset"
        self.tweets = "clean_tweets"
        self.users = "clean_users"
        self.mentions = "clean_mentions"
        self.urls = "clean_urls"
        self.hashtags = "clean_hashtags"


class TaskDatasetOutput:
    def __init__(
        self, db_username: str, db_password: str, db_host: str, db_port: int
    ) -> None:
        """
        Task that defines parameters for the output destination of Twitter data.

        Args:
            db_username (str): Database username.
            db_password (str): Database password.
            db_host (str): Database host.
            db_port (int): Database port.
        """

        # Connection credentials
        self.database_username = db_username
        self.database_password = db_password
        self.database_host = db_host
        self.database_port = db_port

        # Database name
        self.database_name = "twitter"

        # Table definitions

        self.tweets = {
            "name": "tweets",
            "columns": {
                "tweet_id": "String",
                "search_query": "String",
                "source": "String",
                "user_id": "String",
                "created_at": "Datetime",
                "language": "FixedString(2)",
                "text": "String",
                "retweet_count": "Int32",
                "like_count": "Int32",
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

        self.urls = {
            "name": "urls",
            "columns": {"tweet_id": "String", "display_url": "String"},
        }

        self.hashtags = {
            "name": "hashtags",
            "columns": {"tweet_id": "String", "tag": "String"},
        }
