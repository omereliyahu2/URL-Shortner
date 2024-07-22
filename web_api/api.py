from domain.db_manager_interface import DBManagerInterface
from domain.models import URLRequest
from infrastructure.db_manager_concrete import DBManager
from infrastructure.models import URLMapping
from web_api.main import injector
import shortuuid
from fastapi import FastAPI, HTTPException, Request

web_domain = "omer.com"

app = FastAPI()
db: DBManagerInterface = injector.get(DBManager)


@app.post("/shorten/")
def create_short_url(url_request: URLRequest, fastapi_request: Request):
    short_url = shortuuid.uuid()[:6]
    url_mapping = URLMapping(short_url=short_url, original_url=url_request.url)
    db.add(obj=url_mapping)
    db.commit()
    db.refresh(obj=url_mapping)
    base_url = fastapi_request.url.scheme + "://" + fastapi_request.url.netloc
    return {"shortUrl": f"{base_url}/{short_url}"}


@app.get("/{short_url}")
def redirect_to_url(short_url: str):
    url_mapping = db.query(URLMapping).filter(URLMapping.short_url == short_url).first()
    if url_mapping is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return {"url": url_mapping.original_url}