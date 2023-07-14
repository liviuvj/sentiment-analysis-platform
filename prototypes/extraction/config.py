from requests.auth import HTTPBasicAuth
import requests
import json
import yaml


def parse_config_file(path: str):
    """
    Method for parsing the YAML configuration file.

    Args:
        path (str): Path to the YAML configuration file.

    Returns:
        dict: Dictionary with the configuration values.
    """
    with open(path) as f:
        return yaml.safe_load(f)


class BaseConfig:
    def __init__(self, airbyte_username: str, airbyte_password: str) -> None:
        """
        Base configuration class.

        Args:
            airbyte_username (str): Airbyte username.
            airbyte_password (str): Airbyte password.
        """
        self.BASE_URL = "http://localhost:8000/api/v1"
        self.BASIC_AUTH = HTTPBasicAuth(airbyte_username, airbyte_password)


class AirbyteConfig(BaseConfig):
    def __init__(self, airbyte_username: str, airbyte_password: str) -> None:
        """
        Airbyte configuration class.

        Args:
            airbyte_username (str): Airbyte username.
            airbyte_password (str): Airbyte password.
        """
        super().__init__(airbyte_username, airbyte_password)

    def create_workspace(self, account_name: str, account_email: str) -> str:
        """
        Creates a workspace for the specified account name and email.

        Args:
            account_name (str): Account name.
            account_email (str): Account email.

        Returns:
            str: ID of the created workspace.
        """
        url = self.BASE_URL + "/workspaces/create"

        payload = json.dumps({"email": account_email, "name": account_name})

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        ).json()

        return response["workspaceId"]

    def list_workspaces(self):
        """
        Lists the available workspaces.
        """
        url = self.BASE_URL + "/workspaces/list"

        response = requests.post(url, auth=self.BASIC_AUTH).json()

        print(response)

    def update_workspace_initial_setup(self, workspace_id: str) -> int:
        """
        Updates the initial setup of the specified workspace.

        Args:
            workspace_id (str): Workspace ID.

        Returns:
            int: Status code of the request.
        """
        url = self.BASE_URL + "/workspaces/update"

        payload = json.dumps(
            {"workspaceId": workspace_id, "initialSetupComplete": "true"}
        )

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        )

        return response.status_code

    def list_latest_source_definitions(self, source_name: str = None) -> dict:
        """
        Lists the latest source definition available.

        Args:
            source_name (str, optional): Name of the source definition. Defaults to None.

        Returns:
            dict: Definition of the specified `source_name`, all available otherwise.
        """
        url = self.BASE_URL + "/source_definitions/list"

        response = requests.post(url, auth=self.BASIC_AUTH).json()["sourceDefinitions"]

        if source_name:
            source_definition = [
                source for source in response if source["name"] == source_name
            ][0]
            response = source_definition

        return response

    def check_connection_to_source(self, source_id: str) -> str:
        """
        Checks connection can be established with the specified source.

        Args:
            source_id (str): Source ID.

        Returns:
            str: Status of the connection.
        """
        url = self.BASE_URL + "/sources/check_connection"

        payload = json.dumps({"sourceId": source_id})

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        ).json()

        return response["status"]

    def list_latest_destination_definitions(self, destination_name: str = None) -> dict:
        """
        Lists the latest destination definition available.

        Args:
            destination_name (str, optional): Name of the destination definition. Defaults to None.

        Returns:
            dict: Definition of the specified `destination_name`, all available otherwise.
        """
        url = self.BASE_URL + "/destination_definitions/list_latest"

        response = requests.post(url, auth=self.BASIC_AUTH).json()[
            "destinationDefinitions"
        ]

        if destination_name:
            destination_definition = [
                destination
                for destination in response
                if destination["name"] == destination_name
            ][0]
            response = destination_definition

        return response

    def check_connection_to_destination(self, destination_id: str) -> str:
        """
        Checks connection can be established with the specified destination.

        Args:
            destination_id (str): Destination ID.

        Returns:
            str: Status of the connection.
        """
        url = self.BASE_URL + "/destinations/check_connection"

        payload = json.dumps({"destinationId": destination_id})

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        ).json()

        return response["status"]

    def trigger_connection_manual_sync(self, connection_id: str) -> str:
        """
        Triggers a manual synchronization for the specified connection.

        Args:
            connection_id (str): Connection ID.

        Returns:
            str: Status of the connection
        """
        url = self.BASE_URL + "/connections/sync"

        payload = json.dumps({"connectionId": connection_id})

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        ).json()

        return response["job"]["status"]


class TwitterConfig(BaseConfig):
    def __init__(self, airbyte_username: str, airbyte_password: str, workspace_id: str):
        """
        Twitter configuration class.

        Args:
            airbyte_username (str): Airbyte username.
            airbyte_password (str): Airbyte password.
            workspace_id (str): Airbyte workspace ID.
        """
        super().__init__(airbyte_username, airbyte_password)
        self.workspace_id = workspace_id

    def create_source(
        self, source_definition_id: str, source_name: str, query: str, bearer_token: str
    ) -> str:
        """
        Creates a source with the specified arguments.

        Args:
            source_definition_id (str): Source definition ID.
            source_name (str): Name of the source.
            query (str): The search query.
            bearer_token (str): Bearer token for the application.

        Returns:
            str: ID of the created source.
        """
        url = self.BASE_URL + "/sources/create"

        payload = json.dumps(
            {
                "sourceDefinitionId": source_definition_id,
                "connectionConfiguration": {"query": query, "api_key": bearer_token},
                "workspaceId": self.workspace_id,
                "name": source_name,
            }
        )

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        ).json()

        return response["sourceId"]

    def create_connection(
        self,
        connection_name: str,
        source_id: str,
        destination_id: str,
        sync_mode: str = "full_refresh",
        destination_sync_mode: str = "append",
        alias_name: str = "tweets",
    ) -> str:
        """
        Creates a connection with the specified arguments.

        Args:
            connection_name (str): Name of the connection.
            source_id (str): Source ID.
            destination_id (str): Destination ID.
            sync_mode (str, optional): Synchronization mode. Defaults to "full_refresh".
            destination_sync_mode (str, optional): Synchronization mode for the destination. Defaults to "append".
            alias_name (str, optional): Alias for the configured data stream. Defaults to "tweets".

        Returns:
            str: ID of the created connection.
        """
        url = self.BASE_URL + "/connections/create"

        payload = json.dumps(
            {
                "name": connection_name,
                "namespaceDefinition": "destination",
                "sourceId": source_id,
                "destinationId": destination_id,
                "syncCatalog": {
                    "streams": [
                        {
                            "stream": {
                                "name": "tweets",
                                "jsonSchema": {
                                    "type": "object",
                                    "$schema": "http://json-schema.org/draft-07/schema#",
                                    "properties": {
                                        "id": {"type": ["null", "string"]},
                                        "text": {"type": ["null", "string"]},
                                        "edit_history_tweet_ids": {
                                            "type": ["null", "array"]
                                        },
                                    },
                                },
                                "supportedSyncModes": ["full_refresh", "incremental"],
                            },
                            "config": {
                                "syncMode": sync_mode,
                                "destinationSyncMode": destination_sync_mode,
                                "aliasName": alias_name,
                                "selected": "true",
                            },
                        }
                    ]
                },
                "scheduleType": "manual",
                "status": "active",
                "geography": "auto",
                "notifySchemaChanges": "true",
                "nonBreakingChangesPreference": "ignore",
            }
        )

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        ).json()

        return response["connectionId"]

class DatasetConfig(BaseConfig):
    def __init__(self, airbyte_username: str, airbyte_password: str, workspace_id: str):
        """
        Dataset configuration class.

        Args:
            airbyte_username (str): Airbyte username.
            airbyte_password (str): Airbyte password.
            workspace_id (str): Airbyte workspace ID.
        """
        super().__init__(airbyte_username, airbyte_password)
        self.workspace_id = workspace_id
        self.dataset_config = {
            "0000-Dataset-GOT-Movie": {
                "dataset_name": "movie",
                "file_url": "https://drive.google.com/uc?export=download&id=1doLbhxFP5y4TRoMUpx6kgaIR3MUFVDVX"
            },
            "0000-Dataset-GOT-Jon": {
                "dataset_name": "jon",
                "file_url": "https://drive.google.com/uc?export=download&id=1Uji4IajDAYlAj3yhQdQ9B1NcSFg-pqrG"
            },
            "0000-Dataset-GOT-Daenerys": {
                "dataset_name": "daenerys",
                "file_url": "https://drive.google.com/uc?export=download&id=1hL3eh3K2lKtMNEkaG2JSgNSXjoNtHyTG"
            }
        }

    def get_dataset_config(self) -> dict:
        return self.dataset_config

    def create_source(
        self, source_definition_id: str, source_name: str, file_url: str, dataset_name: str
    ) -> str:
        """
        Creates a File source with the specified arguments.

        Args:
            source_definition_id (str): Source definition ID.
            source_name (str): Name of the source.
            file_url (str): The URL path to access the file which should be replicated.
            dataset_name (str): The Name of the final table to replicate this file into
                (should include letters, numbers dash and underscores only).

        Returns:
            str: ID of the created source.
        """
        url = self.BASE_URL + "/sources/create"
        false = False

        payload = json.dumps(
            {
                "sourceDefinitionId": source_definition_id,
                "workspaceId": self.workspace_id,
                "connectionConfiguration": {
                    "url": file_url,
                    "format": "csv",
                    "provider": {
                        "storage": "HTTPS",
                        "user_agent": false
                    },
                    "dataset_name": dataset_name,
                    "reader_options": "{\"dtype\" : {\"quoted_verified\": \"string\"}}"
                    },
                "name": source_name,
                "sourceName": "File (CSV, JSON, Excel, Feather, Parquet)",
            }
        )

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        ).json()

        return response["sourceId"]

    def discover_schema(
            self,
            source_id: str
    ) -> str:


        url = self.BASE_URL + "/sources/discover_schema"

        payload = json.dumps({"sourceId": source_id})

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        ).json()

        return response["catalog"]

    def create_connection(
        self,
        connection_name: str,
        source_id: str,
        destination_id: str,
        data_catalog: str
    ) -> str:
        """
        Creates a connection with the specified arguments.

        Args:
            connection_name (str): Name of the connection.
            source_id (str): Source ID.
            destination_id (str): Destination ID.
            sync_mode (str, optional): Synchronization mode. Defaults to "full_refresh".
            destination_sync_mode (str, optional): Synchronization mode for the destination. Defaults to "append".
            alias_name (str, optional): Alias for the configured data stream. Defaults to "tweets".

        Returns:
            str: ID of the created connection.
        """
        url = self.BASE_URL + "/connections/create"

        payload = json.dumps(
            {
                "workspaceId": self.workspace_id,
                "name": connection_name,
                "sourceId": source_id,
                "destinationId": destination_id,
                "syncCatalog": data_catalog,
                "status": "active",
                "notifySchemaChanges": "true",
                "scheduleType": "manual"
            }
        )

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        ).json()

        return response["connectionId"]


class DestinationConfig(BaseConfig):
    def __init__(self, airbyte_username: str, airbyte_password: str, workspace_id: str):
        """
        Destination configuration class.

        Args:
            airbyte_username (str): Airbyte username.
            airbyte_password (str): Airbyte password.
            workspace_id (str): Workspace ID.
        """
        super().__init__(airbyte_username, airbyte_password)
        self.workspace_id = workspace_id

    def create_csv_destination(
        self,
        destination_definition_id: str,
        destination_name: str,
        destination_path: str,
    ) -> str:
        """
        Creates a local CSV destination with the specified arguments.

        Args:
            destination_definition_id (str): Destination definition ID.
            destination_name (str): Name of the destination.
            destination_path (str): Path to the destination.

        Returns:
            str: ID of the created destination.
        """
        url = self.BASE_URL + "/destinations/create"

        payload = json.dumps(
            {
                "workspaceId": self.workspace_id,
                "name": destination_name,
                "destinationDefinitionId": destination_definition_id,
                "connectionConfiguration": {"destination_path": destination_path},
            }
        )

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        ).json()

        return response["destinationId"]

    def create_mongodb_destination(
        self,
        destination_definition_id: str,
        destination_name: str,
        database: str,
        username: str,
        password: str,
        host: str,
        port: int
    ) -> str:
        """
        Creates a MongoDB destination with the specified arguments.

        Args:
            destination_definition_id (str): Destination definition ID.
            destination_name (str): Name of the destination.
            database (str): Name of the database.
            username (str): Name of the MongoDB user.
            password (str): Password of the MongoDB user.
            host (str): Host machine of the MongoDB database.
            port (int): Por of the MongoDB machine.

        Returns:
            str: ID of the created destination.
        """
        url = self.BASE_URL + "/destinations/create"
        false = False

        payload = json.dumps(
            {
                "workspaceId": self.workspace_id,
                "name": destination_name,
                "destinationName": "MongoDB",
                "destinationDefinitionId": destination_definition_id,
                "connectionConfiguration": {
                    "database": database,
                    "auth_type": {
                        "password": password,
                        "username": username,
                        "authorization": "login/password"
                    },
                    "instance_type": {
                        "tls": false,
                        "host": host,
                        "port": port,
                        "instance": "standalone"
                    },
                    "tunnel_method": {
                        "tunnel_method": "NO_TUNNEL"
                    }
                },
            }
        )

        headers = {"Content-Type": "application/json"}

        response = requests.post(
            url=url, data=payload, headers=headers, auth=self.BASIC_AUTH
        ).json()

        return response["destinationId"]



def main():
    # Read credentials
    config_path = "../.credentials.yml"
    credentials = parse_config_file(config_path)

    # Configure workspace
    airbyte = AirbyteConfig(credentials["AIRBYTE"]["USERNAME"], credentials["AIRBYTE"]["PASSWORD"])
    airbyte.list_workspaces()
    workspace_id = airbyte.create_workspace("custom_name", "custom_account@email.com")
    print(">> New workspace created:", workspace_id)
    assert airbyte.update_workspace_initial_setup(workspace_id) == requests.codes.ALL_OK

    # Get destination definition ID
    destination_definition = airbyte.list_latest_destination_definitions("MongoDB")
    destination_definition_id = destination_definition["destinationDefinitionId"]

    # Configure data destination
    destination = DestinationConfig(credentials["AIRBYTE"]["USERNAME"], credentials["AIRBYTE"]["PASSWORD"], workspace_id)
    destination_name = "MongoDB>>>Dataset"
    destination_id = destination.create_mongodb_destination(
        destination_definition_id, destination_name, "raw_dataset",
        credentials["MONGODB"]["USERNAME"], credentials["MONGODB"]["PASSWORD"],
        credentials["MONGODB"]["HOST"], credentials["MONGODB"]["PORT"]
    )
    assert airbyte.check_connection_to_destination(destination_id) == "succeeded"
    print(f">> New destination created: {destination_name} ({destination_id})")

    # Get source definition ID
    source_definition = airbyte.list_latest_source_definitions("File (CSV, JSON, Excel, Feather, Parquet)")
    source_definition_id = source_definition["sourceDefinitionId"]

    # Configure data source
    dataset = DatasetConfig(credentials["AIRBYTE"]["USERNAME"], credentials["AIRBYTE"]["PASSWORD"], workspace_id)

    for config_name, config in dataset.get_dataset_config().items():
        source_id = dataset.create_source(
            source_definition_id, config_name, config["file_url"], config["dataset_name"]
        )
        assert airbyte.check_connection_to_source(source_id) == "succeeded"
        print(f">> New source created: {config_name} ({source_id})")

        # Discover data catalog
        data_catalog = dataset.discover_schema(source_id)

        # Configure data connection
        connection_name =  f"{config_name} <> {destination_name}"
        connection_id = dataset.create_connection(
            connection_name, source_id, destination_id, data_catalog
        )
        assert connection_id
        print(f">> New connection created: {connection_name} ({connection_id})")

    # The next line will trigger a manual sync of the connection established above
    # assert airbyte.trigger_connection_manual_sync(connection_id) == "running"


if __name__ == "__main__":
    main()
