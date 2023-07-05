import sys

from tasks import (
    TaskPipeline, TaskTwitterInput, TaskTwitterOutput,
    TaskDatasetInput, TaskDatasetOutput
    )
from connectors import MongoDBConnector, ClickHouseConnector
from utils import convert_date, get_logger

log = get_logger("main")


def run_pipeline_twitter(
    task_input, task_output, input_client, output_client, nlp_pipeline
):
    log.info("Starting Twitter Pipeline...")

    # Fetch Twitter database
    input_db = input_client[task_input.database_name]

    # MongoDB query to remove the unusable _ID field
    query_filter = {"_id": 0}

    # Fetch input collections
    collection_tweets = input_db[task_input.tweets].find({}, query_filter)
    collection_users = input_db[task_input.users].find({}, query_filter)
    collection_mentions = input_db[task_input.mentions].find({}, query_filter)
    collection_annotations = input_db[task_input.annotations].find({}, query_filter)
    collection_context_annotations = input_db[task_input.context_annotations].find(
        {}, query_filter
    )
    collection_urls = input_db[task_input.urls].find({}, query_filter)
    collection_hashtags = input_db[task_input.hashtags].find({}, query_filter)

    # Get tweet texts
    tweets_english = [doc for doc in collection_tweets if doc["language"] == "en"]

    # Execute all NLP tasks on the data
    nlp_pipeline.run_all_tasks(tweets_english)

    # Create output database
    output_client.create_database(task_output.database_name)
    output_client.use_database(task_output.database_name)

    # Create tables
    log.info("Creating output tables...")
    output_client.create_table(
        task_output.tweets["name"], task_output.tweets["columns"]
    )
    output_client.create_table(task_output.users["name"], task_output.users["columns"])
    output_client.create_table(
        task_output.mentions["name"], task_output.mentions["columns"]
    )
    output_client.create_table(
        task_output.annotations["name"], task_output.annotations["columns"]
    )
    output_client.create_table(
        task_output.context_annotations["name"],
        task_output.context_annotations["columns"],
    )
    output_client.create_table(task_output.urls["name"], task_output.urls["columns"])
    output_client.create_table(
        task_output.hashtags["name"], task_output.hashtags["columns"]
    )

    # Insert data into tables
    output_client.insert_into_table(
        task_output.tweets["name"],
        list(task_output.tweets["columns"].keys()),
        convert_date(tweets_english, "created_at"),
    )

    users = [user for user in collection_users]
    output_client.insert_into_table(
        task_output.users["name"],
        list(task_output.users["columns"].keys()),
        users,
    )

    mentions = [mention for mention in collection_mentions]
    output_client.insert_into_table(
        task_output.mentions["name"],
        list(task_output.mentions["columns"].keys()),
        mentions,
    )

    annotations = [annotation for annotation in collection_annotations]
    output_client.insert_into_table(
        task_output.annotations["name"],
        list(task_output.annotations["columns"].keys()),
        annotations,
    )

    context_annotations = [context for context in collection_context_annotations]
    output_client.insert_into_table(
        task_output.context_annotations["name"],
        list(task_output.context_annotations["columns"].keys()),
        context_annotations,
    )

    urls = [url for url in collection_urls]
    output_client.insert_into_table(
        task_output.urls["name"],
        list(task_output.urls["columns"].keys()),
        urls,
    )

    hashtags = [hashtag for hashtag in collection_hashtags]
    output_client.insert_into_table(
        task_output.hashtags["name"],
        list(task_output.hashtags["columns"].keys()),
        hashtags,
    )


def run_pipeline_dataset(
    input_task, output_task, input_client, output_client, nlp_pipeline
):
    log.info("Starting Dataset Pipeline...")

    # Fetch Dataset database
    input_db = input_client[input_task.database_name]

    # MongoDB query to remove the unusable _ID field
    query_filter = {"_id": 0}

    # Fetch input collections
    collection_tweets = input_db[input_task.tweets].find({}, query_filter)
    collection_users = input_db[input_task.users].find({}, query_filter)
    collection_mentions = input_db[input_task.mentions].find({}, query_filter)
    collection_urls = input_db[input_task.urls].find({}, query_filter)
    collection_hashtags = input_db[input_task.hashtags].find({}, query_filter)

    # Get tweet texts
    tweets = [doc for doc in collection_tweets]

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
        run_pipeline_twitter(input_task, output_task, input_client, output_client, nlp_pipeline)
    elif task_name == "dataset":
        run_pipeline_dataset(input_task, output_task, input_client, output_client, nlp_pipeline)

if __name__ == "__main__":
    main()
