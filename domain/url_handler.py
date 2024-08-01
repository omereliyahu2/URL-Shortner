from injector import inject

from domain.db_manager_interface import DBManagerInterface
from domain.models import URLRequest
from infrastructure.models import URLMapping
import shortuuid
from fastapi import Request, HTTPException


class URLHandler:
    @inject
    def __init__(self, db: DBManagerInterface):
        self.db = db

    def shorten_url(self, url_request: URLRequest, fastapi_request: Request):
        short_url = shortuuid.uuid()[:6]
        url_mapping = URLMapping(short_url=short_url, original_url=url_request.url)
        self.db.add(obj=url_mapping)
        self.db.commit()
        self.db.refresh(obj=url_mapping)
        base_url = fastapi_request.url.scheme + "://" + fastapi_request.url.netloc
        return {"shortUrl": f"{base_url}/{short_url}"}

    def get_original_url(self, short_url: str):
        url_mapping = self.db.filter_query(URLMapping, URLMapping.short_url, short_url)
        if url_mapping is None:
            raise HTTPException(status_code=404, detail="URL not found")
        return url_mapping.original_url
