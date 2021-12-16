# wiki-redirector

A little web service providing short URLs that redirect to pages in the
[Nextstrain team wiki](https://nextstrain.atlassian.net/wiki).

## Usage

| URL                                        | Redirects to
|--------------------------------------------|-------------
| `https://wiki.nextstrain.org`              | Wiki homepage
| `https://wiki.nextstrain.org/t/:title`     | Page whose title contains or matches `:title`


## Deployment

Deployed with Heroku.  See the [_Procfile_](Procfile).


## Development

First, put your Atlassian user and API token in your _~/.netrc_ file:

    machine nextstrain.atlassian.net
      login you@example.com
      password 8J+RgAo=

Or define `ATLASSIAN_USER` and `ATLASSIAN_TOKEN` in your environment.

Second, make sure you're running Python 3.10.1, perhaps using
[pyenv](https://github.com/pyenv/pyenv) or
[conda](https://docs.conda.io/en/latest/miniconda.html).

Then, create and activate a `.venv/`:

    make venv
    source .venv/bin/activate

Now, start the web server:

    ./serve.py

If you need to update or add dependencies, modify
[_requirements.in_](requirements.in) and then run:

    make requirements.txt
    make venv


## Memory

Redirects are remembered for link stability and speed.

A small in-process LRU cache is used to remember redirects for a given title
within the lifetime of the process.  If `S3_BUCKET` is defined in the
environment (along with valid AWS credentials), redirects will be permanently
remembered.

This memory is important for making short links resolve consistently over time
to the same pages.


## Security and privacy considerations

Our wiki is private, but this web service is public, which exposes the
following information:

  - Page titles, via `/t/…` hits/misses and sometimes `Location` header values
  - Page URLs, via `Location`
  - Page IDs, via `Location`

None of these are (currently) sensitive.

No page content is revealed.  To keep it that way, this service should never
attempt to even _match_ user input to page content, as that would enable an
[oracle attack](https://en.wikipedia.org/wiki/Oracle_attack) to reveal page
contents.
