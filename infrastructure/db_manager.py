from typing import Any

from injector import inject
from sqlalchemy import create_engine

from domain.db_manager_interface import DBManagerInterface
from sqlalchemy.orm import Session, sessionmaker

from domain.secrets_manager_interface import SecretsManagerInterface
from infrastructure.models import Base


class DBManager(DBManagerInterface):
    @inject
    def __init__(self, secrets_manager: SecretsManagerInterface):
        secret = secrets_manager.get_secret("url_database-1")
        database_url = f"{secret['engine']}://{secret['usename']}:{secret['password']}@{secret['host']}:{secret['port']}/{secret['dbname']}"
        engine = create_engine(database_url, connect_args={"connect_timeout": 20})
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db: Session = session_local()

    def add(self, obj: Any):
        self.db.add(obj)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj: Any) -> None:
        self.db.refresh(obj)

    def filter_query(self, model: Any, value_to_compare: Base, comparison_target) -> Any:
        return self.db.query(model).filter(value_to_compare == comparison_target).first()
