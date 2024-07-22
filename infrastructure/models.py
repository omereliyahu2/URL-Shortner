from sqlalchemy import Column, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class URLMapping(Base):
    __tablename__ = "url_mappings"
    short_url = Column(String, primary_key=True, index=True)
    original_url = Column(String, index=True)