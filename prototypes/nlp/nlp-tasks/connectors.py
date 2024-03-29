from utils import get_logger
from clickhouse_driver import Client as ClickHouseClient
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError

log = get_logger("connectors")


class MongoDBConnector:
    def __init__(self, host: str, port: int, username: str, password: str) -> None:
        """
        Connector for MongoDB.

        Args:
            host (str): Host of the MongoDB instance
            port (int): Port to connect to the host
            username (str): MongoDB database username
            password (str): MongoDB database password
        """

        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def get_connection(self) -> MongoClient:
        """
        Method for establishing the connection with MongoDB.

        Returns:
            MongoClient: The client MongoDB.
        """

        try:
            connection_query = "mongodb://{user}:{pass}@{host}:{port}".format(
                **{
                    "user": self.username,
                    "pass": self.password,
                    "host": self.host,
                    "port": self.port,
                }
            )

            client = MongoClient(connection_query)
            client.server_info()

            log.info("Established connection to MongoDB")

            return client

        except ServerSelectionTimeoutError as e:
            log.error("Error connecting to MongoDB:", e)

class ClickHouseConnector:
    def __init__(self, host: str, port: str, user: str, password: str) -> None:
        """
        Connector for ClickHouse.

        Args:
            host (str): Host of the ClickHouse instance.
            port (str): Port to connect to the host.
            user (str): ClickHouse database username.
            password (str): ClickHouse database password.
        """

        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.client = self.connect()

    def connect(self) -> ClickHouseClient:
        """
        Method for establishing the connection with ClickHouse.

        Returns:
            clickhouse_driver.client.Client: The client connection.
        """

        client = None

        try:
            client = ClickHouseClient(
                host=self.host, port=self.port, user=self.user, password=self.password
            )
            log.info("Established connection to ClickHouse")
        except Exception as e:
            log.error("Error connecting to ClickHouse:", e)

        return client

    def create_database(self, db_name: str) -> None:
        """
        Creates the database with the specified name if it doesn't exist already.

        Args:
            db_name (str): Name of the database.
        """

        try:
            params = {"db_name": db_name}

            self.client.execute(
                "CREATE DATABASE IF NOT EXISTS {db_name}".format(**params)
            )
            log.info("Created database '%s' if not existed", db_name)
        except Exception as e:
            log.error("Error creating database:", e)

    def use_database(self, db_name: str) -> None:
        """
        Checks out the database with the specified name.

        Args:
            db_name (str): Name of the database.
        """

        try:
            params = {"db_name": db_name}
            query = "USE {db_name}"
            self.client.execute(query.format(**params))

            log.info("Using database '%s'", db_name)
        except Exception as e:
            log.error("Error using database:", e)

    def create_table(
        self, table_name: str, columns: dict, pk: str = None, ordered_by: str = None
    ) -> None:
        """
        Creates a table with the specified parameters.

        Args:
            table_name (str): Name of the table.
            columns (dict): Dictionary with the column names as keys and data types as values.
                Example: `{"id": "Int32", "name": "String"}`.
            pk (str, optional): Primary key of the table, needs to exist in the columns parameter as well.
                If not provided, takes first key of `columns`.
            ordered_by (str, optional): Column(s) for ordering the table, needs to exist in the columns parameter as well.
                If not provided, takes first key of `columns`.
        """

        try:
            if (pk and not pk in columns) or (ordered_by and ordered_by not in columns):
                raise Exception(
                    "PRIMARY KEY or ORDERED BY column not in provided columns for the table"
                )

            if not pk:
                pk = list(columns.keys())[0]

            if not ordered_by:
                ordered_by = list(columns.keys())[0]

            cols = ", ".join([f"{col} {columns[col]}" for col in columns])
            params = {
                "table_name": table_name,
                "cols": cols,
                "pk": pk,
                "ordered_by": ordered_by,
            }

            query = (
                "CREATE TABLE IF NOT EXISTS {table_name} ({cols}) "
                + "ENGINE = MergeTree() "
                + "PRIMARY KEY {pk} "
                + "ORDER BY {ordered_by}"
            )

            self.client.execute(query.format(**params))
            log.info("Created table '%s' if not existed", table_name)

        except Exception as e:
            log.error("Error creating table:", e)

    def insert_into_table(
        self, table_name: str, columns: list, values: list[list]
    ) -> None:
        """
        Inserts values into table.

        Args:
            table_name (str): Name of the table.
            columns (list): List with the name of the columns where data will be inserted.
            values (list[list]): List of rows to be inserted into the table.
        """

        try:
            cols = ", ".join(columns)
            params = {"table_name": table_name, "cols": cols}

            query = "INSERT INTO {table_name} ({cols}) VALUES"
            num_inserted_rows = self.client.execute(query.format(**params), values)

            log.info(
                "Inserted %s rows into table '%s'", *[num_inserted_rows, table_name]
            )

        except Exception as e:
            log.error("Error inserting rows into table:", e)
