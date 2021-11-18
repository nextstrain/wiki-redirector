#!/usr/bin/env python
import httpx
import logging
from functools import partial
from os import environ
from starlette.applications import Starlette
from starlette.routing import Route
from starlette.responses import RedirectResponse
from urllib.parse import (
    quote_plus as urlescape,
    unquote_plus as urlunescape,
    urljoin)

Redirect302 = partial(RedirectResponse, status_code = 302)

ua = httpx.AsyncClient()

logging.basicConfig(
    level = logging.INFO,
    format = "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
    datefmt = "%Y-%m-%d %H:%M:%S%z")

log = logging.getLogger("wiki-redirector")


SITE = "https://nextstrain.atlassian.net"
SPACE = "NEXTSTRAIN"

try:
    AUTH = (environ["WIKI_USER"], environ["WIKI_TOKEN"])
except KeyError:
    # httpx will fallback to using creds from a ~/.netrc file, if available,
    # which is handy in dev.
    AUTH = None


def create_app():
    return Starlette(
        routes = [
            Route("/", homepage),
            Route("/t/{title}", title_search) ])


def homepage(request):
    return Redirect302(wiki_url(f"/spaces/{SPACE}"))


async def title_search(request):
    title = urlunescape(request.path_params["title"])

    log.info(f"Searching for page with title {title!r}")

    search = await ua.get(
        wiki_url("/rest/api/content/search"),
        auth = AUTH,
        params = {
            "cql": f'space = "{SPACE}" and type = page and title ~ "{text_query(title)}"',
            "limit": 1 })

    results = search.json()["results"]

    if not results:
        return Redirect302(wiki_url(f"/search?text={urlescape(title)}"))

    return Redirect302(wiki_url(results[0]["_links"]["webui"]))


def text_query(q):
    return q.replace('"', "")


def wiki_url(path):
    relative_path = path.lstrip("/")
    return urljoin(SITE, f"/wiki/{relative_path}")


if __name__ == "__main__":
    import uvicorn
    from pathlib import Path

    module = Path(__file__).stem

    uvicorn.run(f"{module}:create_app", factory = True, reload = True)
