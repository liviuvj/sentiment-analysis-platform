from tasks import TaskPipeline, TaskTwitterInput, TaskTwitterOutput
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


def main():
    # Create input and output tasks
    twitter_in = TaskTwitterInput()
    twitter_out = TaskTwitterOutput()

    # Create Task Pipeline
    nlp_pipeline = TaskPipeline()

    # Connect to MongoDB
    mongo_client = MongoDBConnector(
        twitter_in.database_host,
        twitter_in.database_port,
        twitter_in.database_username,
        twitter_in.database_password,
    ).get_connection()

    # Connect to ClickHouse
    ck_client = ClickHouseConnector(
        twitter_out.database_host,
        twitter_out.database_port,
        twitter_out.database_username,
        twitter_out.database_password,
    )

    # Run Twitter pipeline
    run_pipeline_twitter(twitter_in, twitter_out, mongo_client, ck_client, nlp_pipeline)


if __name__ == "__main__":
    main()
