import json

import boto3
from botocore.exceptions import ClientError

from domain.secrets_manager_interface import SecretsManagerInterface


class SecretsManager(SecretsManagerInterface):
    region_name = "us-east-1"

    def get_secret(self, secret_name: str) -> dict:

        session = boto3.session.Session()
        client = session.client(
            service_name='secretsmanager',
            region_name=self.region_name
        )

        try:
            get_secret_value_response = client.get_secret_value(
                SecretId=secret_name
            )
        except ClientError as e:
            raise e

        secret = get_secret_value_response['SecretString']
        secret = json.loads(secret)

        return secret
