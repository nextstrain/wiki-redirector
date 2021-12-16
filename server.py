#!/usr/bin/env python
import httpx
import logging
import logging.config
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from os import environ
from urllib.parse import (
    quote_plus as urlescape,
    unquote_plus as urlunescape,
    urljoin)


SITE = "https://nextstrain.atlassian.net"
SPACE = "NEXTSTRAIN"

try:
    AUTH = (environ["ATLASSIAN_USER"], environ["ATLASSIAN_TOKEN"])
except KeyError:
    # httpx will fallback to using creds from a ~/.netrc file, if available,
    # which is handy in dev.
    AUTH = None


app = FastAPI()

ua = httpx.AsyncClient()

log = logging.getLogger("wiki-redirector")

LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "stderr": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "[%(asctime)s] %(levelprefix)s %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S%z",
            "use_colors": None, # auto-detect based on isatty()
        },
    },
    "handlers": {
        "stderr": {
            "formatter": "stderr",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr",
        },
    },
    "loggers": {
        "": {"handlers": ["stderr"], "level": environ.get("LOG_LEVEL", "INFO").upper()},
        "uvicorn": {"handlers": []},
    },
}

logging.config.dictConfig(LOG_CONFIG)


@app.get("/", response_class = RedirectResponse, status_code = 302)
def homepage():
    return wiki_url(f"/spaces/{SPACE}")


@app.get("/t/{title}", response_class = RedirectResponse, status_code = 302)
async def title_search(title: str):
    # title is already URL-decoded, but also support "+ as space" encoding
    # (like is used in query param values) for convenience when typing out
    # these URLs.
    title = title.replace("+", " ")

    log.info(f"Searching for page with title {title!r}")

    if results := await search_pages(title):
        page = results[0]
        log.info(f"Found page {page['title']!r} (id {page['id']}); redirecting")
        return wiki_url(page["_links"]["webui"])

    log.info("No page found; redirecting to full wiki search")
    return wiki_url(f"/search?text={urlescape(title)}")


async def search_pages(title):
    query = f'space = "{SPACE}" and type = page and title ~ "{text_query(title)}"'

    log.debug(f"Search query: {query!r}")

    search = await ua.get(
        wiki_url("/rest/api/content/search"),
        auth = AUTH,
        params = {
            "cql": query,
            "limit": 1 })

    search.raise_for_status()

    return search.json()["results"]


def text_query(q):
    return q.replace('"', "")


def wiki_url(path):
    relative_path = path.lstrip("/")
    return urljoin(SITE, f"/wiki/{relative_path}")


if __name__ == "__main__":
    # Dev mode when run directly.
    import uvicorn
    from pathlib import Path

    module = Path(__file__).stem

    uvicorn.run(f"{module}:app", reload = True, log_config = LOG_CONFIG)
