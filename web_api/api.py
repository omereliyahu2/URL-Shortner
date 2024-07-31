from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from domain.db_manager_interface import DBManagerInterface
from domain.models import URLRequest
from infrastructure.models import URLMapping
from web_api.main import injector
import shortuuid
from fastapi import FastAPI, HTTPException, Request

web_domain = "omer.com"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001"],  # Allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
db: DBManagerInterface = injector.get(DBManagerInterface)


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
    url_mapping = db.filter_query(URLMapping, URLMapping.short_url, short_url)
    if url_mapping is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return RedirectResponse(url=url_mapping.original_url)