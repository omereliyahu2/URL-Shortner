from typing import Any

from sqlalchemy import create_engine

from domain.db_manager_interface import DBManagerInterface
from sqlalchemy.orm import Session, sessionmaker

from infrastructure.models import Base


class DBManager(DBManagerInterface):
    def __init__(self):
        database_url = "postgresql://user:password@your-rds-instance/dbname"
        engine = create_engine(database_url)
        session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base.metadata.create_all(bind=engine)
        self.db: Session = session_local()

    def add(self, obj: Any):
        self.db.add(obj)

    def commit(self) -> None:
        self.db.commit()

    def refresh(self, obj: Any) -> None:
        self.db.refresh(obj)

    def query(self, obj: Any) -> Any:
        self.db.query(obj)
