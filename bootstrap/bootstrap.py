import uvicorn
from injector import Injector, Module, singleton

from domain.db_manager_interface import DBManagerInterface
from domain.secrets_manager_interface import SecretsManagerInterface
from domain.url_handler import URLHandler
from infrastructure.db_manager import DBManager
from infrastructure.secrets_manager import SecretsManager


class AppModule(Module):
    def configure(self, binder):
        binder.bind(SecretsManagerInterface, to=SecretsManager, scope=singleton)
        binder.bind(DBManagerInterface, to=DBManager, scope=singleton)
        binder.bind(URLHandler, to=URLHandler, scope=singleton)


injector = Injector([AppModule()])
