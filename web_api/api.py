from urllib.parse import urlparse

from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse

from domain.models import URLRequest
from domain.url_handler import URLHandler
from bootstrap.bootstrap import injector
from fastapi import FastAPI, Request

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8001", "https://omereliyahu2.github.io"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
url_handler: URLHandler = injector.get(URLHandler)


@app.post("/shorten/")
def create_short_url(url_request: URLRequest, fastapi_request: Request):
    return url_handler.shorten_url(url_request=url_request, fastapi_request=fastapi_request)


@app.get("/{short_url}")
def redirect_to_url(short_url: str):
    original_url = url_handler.get_original_url(short_url=short_url)
    parsed_url = urlparse(original_url)
    if not parsed_url.scheme:
        # Default to http if no scheme is provided
        original_url = "http://" + original_url
    return RedirectResponse(url=original_url)
