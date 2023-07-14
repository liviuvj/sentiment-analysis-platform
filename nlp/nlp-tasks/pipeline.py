import sys

from tasks import (
    TaskPipeline, TaskTwitterInput, TaskTwitterOutput,
    TaskDatasetInput, TaskDatasetOutput
    )
from connectors import MongoDBConnector, ClickHouseConnector
from utils import convert_date, get_logger

log = get_logger("main")


def run_pipeline_twitter(
    input_task, output_task, input_client, output_client, nlp_pipeline
):
    """
    Twitter NLP pipeline.

    Args:
        input_task (class): The task with the input database connection parameters.
        output_task (class): The task with the output database connection parameters.
        input_client (class): The input database client.
        output_client (class): The output database client.
        nlp_pipeline (class): The NLP pipeline task to execute on the data.
    """

    log.info("Starting Twitter Pipeline...")

    # Fetch Twitter database
    input_db = input_client[input_task.database_name]

    # MongoDB query to remove the unusable _ID field
    query_filter = {"_id": 0}

    # Fetch input collections
    collection_tweets = input_db[input_task.tweets].find({}, query_filter)
    collection_users = input_db[input_task.users].find({}, query_filter)
    collection_mentions = input_db[input_task.mentions].find({}, query_filter)
    collection_annotations = input_db[input_task.annotations].find({}, query_filter)
    collection_context_annotations = input_db[input_task.context_annotations].find(
        {}, query_filter
    )
    collection_urls = input_db[input_task.urls].find({}, query_filter)
    collection_hashtags = input_db[input_task.hashtags].find({}, query_filter)

    # Get tweet texts
    tweets_english = [doc for doc in collection_tweets if doc["language"] == "en"]

    # Execute all NLP tasks on the data
    nlp_pipeline.run_all_tasks(tweets_english)

    # Create output database
    output_client.create_database(output_task.database_name)
    output_client.use_database(output_task.database_name)

    # Create tables
    log.info("Creating output tables...")
    output_client.create_table(
        output_task.tweets["name"], output_task.tweets["columns"]
    )
    output_client.create_table(output_task.users["name"], output_task.users["columns"])
    output_client.create_table(
        output_task.mentions["name"], output_task.mentions["columns"]
    )
    output_client.create_table(
        output_task.annotations["name"], output_task.annotations["columns"]
    )
    output_client.create_table(
        output_task.context_annotations["name"],
        output_task.context_annotations["columns"],
    )
    output_client.create_table(output_task.urls["name"], output_task.urls["columns"])
    output_client.create_table(
        output_task.hashtags["name"], output_task.hashtags["columns"]
    )

    # Insert data into tables
    output_client.insert_into_table(
        output_task.tweets["name"],
        list(output_task.tweets["columns"].keys()),
        convert_date(tweets_english, "created_at"),
    )

    users = [user for user in collection_users]
    output_client.insert_into_table(
        output_task.users["name"],
        list(output_task.users["columns"].keys()),
        users,
    )

    mentions = [mention for mention in collection_mentions]
    output_client.insert_into_table(
        output_task.mentions["name"],
        list(output_task.mentions["columns"].keys()),
        mentions,
    )

    annotations = [annotation for annotation in collection_annotations]
    output_client.insert_into_table(
        output_task.annotations["name"],
        list(output_task.annotations["columns"].keys()),
        annotations,
    )

    context_annotations = [context for context in collection_context_annotations]
    output_client.insert_into_table(
        output_task.context_annotations["name"],
        list(output_task.context_annotations["columns"].keys()),
        context_annotations,
    )

    urls = [url for url in collection_urls]
    output_client.insert_into_table(
        output_task.urls["name"],
        list(output_task.urls["columns"].keys()),
        urls,
    )

    hashtags = [hashtag for hashtag in collection_hashtags]
    output_client.insert_into_table(
        output_task.hashtags["name"],
        list(output_task.hashtags["columns"].keys()),
        hashtags,
    )


def run_pipeline_dataset(
    input_task, output_task, input_client, output_client, nlp_pipeline, data_source, search_query
):
    """_summary_

    Args:
        input_task (class): The task with the input database connection parameters.
        output_task (class): The task with the output database connection parameters.
        input_client (class): The input database client.
        output_client (class): The output database client.
        nlp_pipeline (class): The NLP pipeline task to execute on the data.
        data_source (str): The name of the data source.
        search_query (str): The name of the search query.
    """

    log.info("Starting Dataset Pipeline...")

    # Fetch Dataset database
    input_db = input_client[input_task.database_name]

    # MongoDB filter to remove the unusable _ID field
    query_filter = {"_id": 0}

    # Fetch filtered tweet collection
    collection_tweets = input_db[input_task.tweets].find(
        {"source": data_source, "search_query": search_query},
        query_filter)

    # Get tweets and filters for tweet_ids and user_ids
    tweets = [tweet for tweet in collection_tweets]
    tweet_ids = [tweet["tweet_id"] for tweet in tweets]
    tweet_filter = {"tweet_id": {"$in": tweet_ids}}
    user_ids = [tweet["user_id"] for tweet in tweets]
    user_filter = {"user_id": {"$in": user_ids}}

    # Fetch filtered users collection
    collection_users = input_db[input_task.users].find(user_filter, query_filter)
    users = list({user["user_id"]:user for user in collection_users}.values())

    # Fetch filtered mentions collection
    collection_mentions = input_db[input_task.mentions].find(tweet_filter, query_filter)
    mentions = list({mention["tweet_id"]:mention for mention in collection_mentions}.values())

    # Fetch filtered urls collection
    collection_urls = input_db[input_task.urls].find(tweet_filter, query_filter)
    urls = list({url["tweet_id"]:url for url in collection_urls}.values())

    # Fetch filtered hashtags collection
    collection_hashtags = input_db[input_task.hashtags].find(tweet_filter, query_filter)
    hashtags = list({tag["tweet_id"]:tag for tag in collection_hashtags}.values())

    # Execute all NLP tasks on the data
    nlp_pipeline.run_all_tasks(tweets)

    # Create output database
    output_client.create_database(output_task.database_name)
    output_client.use_database(output_task.database_name)

    # Create tables
    log.info("Creating output tables...")
    output_client.create_table(
        output_task.tweets["name"], output_task.tweets["columns"]
    )
    output_client.create_table(output_task.users["name"], output_task.users["columns"])
    output_client.create_table(
        output_task.mentions["name"], output_task.mentions["columns"]
    )
    output_client.create_table(output_task.urls["name"], output_task.urls["columns"])
    output_client.create_table(
        output_task.hashtags["name"], output_task.hashtags["columns"]
    )

    # Insert data into tables
    output_client.insert_into_table(
        output_task.tweets["name"],
        list(output_task.tweets["columns"].keys()),
        convert_date(tweets, "created_at"),
    )

    output_client.insert_into_table(
        output_task.users["name"],
        list(output_task.users["columns"].keys()),
        users,
    )

    output_client.insert_into_table(
        output_task.mentions["name"],
        list(output_task.mentions["columns"].keys()),
        mentions,
    )

    output_client.insert_into_table(
        output_task.urls["name"],
        list(output_task.urls["columns"].keys()),
        urls,
    )

    output_client.insert_into_table(
        output_task.hashtags["name"],
        list(output_task.hashtags["columns"].keys()),
        hashtags,
    )


def main():
    # Parse arguments
    task_name = sys.argv[1]
    in_db_username = sys.argv[2]
    in_db_password = sys.argv[3]
    in_db_host = sys.argv[4]
    in_db_port = sys.argv[5]
    out_db_username = sys.argv[6]
    out_db_password = sys.argv[7]
    out_db_host = sys.argv[8]
    out_db_port = sys.argv[9]
    if len(sys.argv) > 10:
        data_source = sys.argv[10]
    if len(sys.argv) > 11:
        search_query = sys.argv[11]

    # Create input and output tasks
    input_task, output_task = None, None

    if task_name == "twitter":
        input_task = TaskTwitterInput(in_db_username, in_db_password, in_db_host, in_db_port)
        output_task = TaskTwitterOutput(out_db_username, out_db_password, out_db_host, out_db_port)
    elif task_name == "dataset":
        input_task = TaskDatasetInput(in_db_username, in_db_password, in_db_host, in_db_port)
        output_task = TaskDatasetOutput(out_db_username, out_db_password, out_db_host, out_db_port)

    # Create Task Pipeline
    nlp_pipeline = TaskPipeline()

    # Connect to the input database: MongoDB
    input_client = MongoDBConnector(
        input_task.database_host,
        input_task.database_port,
        input_task.database_username,
        input_task.database_password,
    ).get_connection()

    # Connect to the output database: ClickHouse
    output_client = ClickHouseConnector(
        output_task.database_host,
        output_task.database_port,
        output_task.database_username,
        output_task.database_password,
    )

    # Run pipeline
    if task_name == "twitter":
        run_pipeline_twitter(input_task, output_task,
                             input_client,output_client,
                             nlp_pipeline)
    elif task_name == "dataset":
        run_pipeline_dataset(input_task, output_task,
                             input_client, output_client,
                             nlp_pipeline, data_source, search_query)

if __name__ == "__main__":
    main()
