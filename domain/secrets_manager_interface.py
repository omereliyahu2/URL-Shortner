class SecretsManagerInterface:
    def get_secret(self, secret_name: str) -> dict:
        raise NotImplementedError
