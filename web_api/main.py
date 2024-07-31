import uvicorn
from injector import Injector, Module, singleton

from domain.db_manager_interface import DBManagerInterface
from domain.secrets_manager_interface import SecretsManagerInterface
from infrastructure.db_manager import DBManager
from infrastructure.secrets_manager import SecretsManager


class AppModule(Module):
    def configure(self, binder):
        binder.bind(SecretsManagerInterface, to=SecretsManager, scope=singleton)
        binder.bind(DBManagerInterface, to=DBManager, scope=singleton)


injector = Injector([AppModule()])


def run_server(port: int = 8080, host: str = "localhost", reload: bool = False):
    uvicorn.run("api:app", host=host, port=port, reload=reload)


if __name__ == "__main__":
    run_server(port=8080, host="localhost", reload=False)