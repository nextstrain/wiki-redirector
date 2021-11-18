#!/usr/bin/env python
import httpx
import logging
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
    AUTH = (environ["WIKI_USER"], environ["WIKI_TOKEN"])
except KeyError:
    # httpx will fallback to using creds from a ~/.netrc file, if available,
    # which is handy in dev.
    AUTH = None


app = FastAPI()

ua = httpx.AsyncClient()

log = logging.getLogger("wiki-redirector")

logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S%z")


@app.get("/", response_class = RedirectResponse, status_code = 302)
def homepage():
    return wiki_url(f"/spaces/{SPACE}")


@app.get("/t/{title}", response_class = RedirectResponse, status_code = 302)
async def title_search(title: str):
    title = title.replace("+", " ")

    log.info(f"Searching for page with title {title!r}")

    search = await ua.get(
        wiki_url("/rest/api/content/search"),
        auth = AUTH,
        params = {
            "cql": f'space = "{SPACE}" and type = page and title ~ "{text_query(title)}"',
            "limit": 1 })

    results = search.json()["results"]

    if not results:
        log.info("No page found; redirecting to full wiki search")
        return wiki_url(f"/search?text={urlescape(title)}")

    page = results[0]
    log.info(f"Found page {page['title']!r} (id {page['id']}); redirecting")
    return wiki_url(page["_links"]["webui"])


def text_query(q):
    return q.replace('"', "")


def wiki_url(path):
    relative_path = path.lstrip("/")
    return urljoin(SITE, f"/wiki/{relative_path}")


if __name__ == "__main__":
    import uvicorn
    from pathlib import Path

    module = Path(__file__).stem

    uvicorn.run(f"{module}:app", reload = True)
