import re
from dataclasses import dataclass
from datetime import datetime

import click
import requests
from bs4 import BeautifulSoup
from click_default_group import DefaultGroup


@dataclass
class URLData:
    title: str = None
    author: str = None
    pub_date: str = None
    publisher: str = None


@click.group(cls=DefaultGroup, default="create", default_if_no_args=True)
@click.version_option()
def cli():
    """Easily create citations from website URLs."""


@cli.command(name="create")
@click.argument("url")
@click.option(
    "-f",
    "--fmt",
    type=click.Choice(
        ["mla", "apa", "chicago", "IEEE", "Harvard"], case_sensitive=False
    ),
    default="mla",
    show_default=True,
    help="The citation format",
)
@click.option(
    "--no-date",
    is_flag=True,
    help="Omit the accessed date from the citation",
)
@click.option(
    "--no-url",
    is_flag=True,
    help="Omit the URL from the citation",
)
@click.option(
    "--override",
    type=(str, str),
    multiple=True,
    help="Override specific fields. Usage: --override <field> <value>",
)
def create_citation(url, fmt, no_date, no_url, override):
    """Generate citations in common formats."""
    url_data = get_webpage_details(url)

    # Apply overrides
    overrides = dict(override)
    if "author" in overrides:
        url_data.author = overrides["author"]
    if "title" in overrides:
        url_data.title = overrides["title"]
    if "publisher" in overrides:
        url_data.publisher = overrides["publisher"]
    if "pub_date" in overrides:
        url_data.pub_date = overrides["pub_date"]

    citation = get_citation(url, url_data, fmt, no_date, no_url)
    click.echo(citation)


@cli.command(name="batch")
@click.argument("f", type=click.File("r"))
@click.option(
    "-f",
    "--fmt",
    type=click.Choice(
        ["mla", "apa", "chicago", "IEEE", "Harvard"], case_sensitive=False
    ),
    default="mla",
    show_default=True,
    help="The citation format",
)
@click.option(
    "--no-date",
    is_flag=True,
    help="Omit the accessed date from the citation",
)
@click.option(
    "--no-url",
    is_flag=True,
    help="Omit the URL from the citation",
)
@click.option(
    "--override",
    type=(str, str),
    multiple=True,
    help="Override specific fields. Usage: --override <field> <value>",
)
def batch_citations(f, fmt, no_date, no_url, override):
    """Generate citations for multiple URLs."""
    urls = [line.strip() for line in f.readlines()]
    for url in urls:
        if url:
            url_data = get_webpage_details(url)

            # Apply overrides
            overrides = dict(override)
            if "author" in overrides:
                url_data.author = overrides["author"]
            if "title" in overrides:
                url_data.title = overrides["title"]
            if "publisher" in overrides:
                url_data.publisher = overrides["publisher"]
            if "pub_date" in overrides:
                url_data.pub_date = overrides["pub_date"]

            citation = get_citation(url, url_data, fmt, no_date, no_url)
            click.echo(citation)


def get_webpage_details(url):
    """Extracts title, author, publication date, and publisher from the given URL."""
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")

        title = soup.title.string.strip() if soup.title else None

        author_meta = soup.find("meta", attrs={"name": "author"}) or soup.find(
            "meta", attrs={"property": "article:author"}
        )
        author = (
            author_meta["content"].strip()
            if author_meta and "content" in author_meta.attrs
            else None
        )

        date_meta = soup.find("meta", attrs={"name": "date"}) or soup.find(
            "meta", attrs={"property": "article:published_time"}
        )
        if date_meta and "content" in date_meta.attrs:
            pub_date = date_meta["content"].strip()
            pub_date = datetime.strptime(pub_date, "%Y-%m-%d").strftime("%d %b. %Y")
        else:
            pub_date = None

        publisher_meta = soup.find("meta", attrs={"name": "publisher"}) or soup.find(
            "meta", attrs={"property": "og:site_name"}
        )
        publisher = (
            publisher_meta["content"].strip()
            if publisher_meta and "content" in publisher_meta.attrs
            else None
        )

        return URLData(
            title=title, author=author, pub_date=pub_date, publisher=publisher
        )
    except Exception:
        return URLData()


def get_citation(url, url_data, fmt, no_date, no_url):
    """Generates a citation string based on the extracted URL data and specified format."""
    date_accessed = datetime.today().strftime("%d %B %Y") if not no_date else None

    citation_parts = []

    if fmt.lower() == "apa":
        if url_data.author:
            citation_parts.append(f"{url_data.author}")
        citation_parts.append("(n.d.).")
        if url_data.title:
            citation_parts.append(f"{url_data.title}.")
        if url_data.publisher:
            citation_parts.append(f"{url_data.publisher}.")
        if date_accessed:
            citation_parts.append(f"Retrieved {date_accessed}")
        if not no_url:
            citation_parts.append(f"from {url}")
    elif fmt.lower() == "mla":
        if url_data.author:
            citation_parts.append(f"{url_data.author}.")
        if url_data.title:
            citation_parts.append(f'"{url_data.title}."')
        if url_data.publisher:
            citation_parts.append(f"{url_data.publisher}")
        if not no_url:
            citation_parts.append(f"{url}")
        if date_accessed:
            citation_parts.append(f"Accessed {date_accessed}.")
    elif fmt.lower() == "chicago":
        if url_data.author:
            citation_parts.append(f"{url_data.author}.")
        if url_data.title:
            citation_parts.append(f'"{url_data.title}."')
        if url_data.publisher:
            citation_parts.append(f"{url_data.publisher}.")
        if date_accessed:
            citation_parts.append(f"Accessed {date_accessed}.")
        if not no_url:
            citation_parts.append(f"{url}.")
    elif fmt.lower() == "ieee":
        if url_data.author:
            citation_parts.append(f"{url_data.author},")
        if url_data.title:
            citation_parts.append(f'"{url_data.title},"')
        if url_data.publisher:
            citation_parts.append(f"{url_data.publisher}.")
        citation_parts.append("[Online].")
        if not no_url:
            citation_parts.append(f"Available: {url}")
        if date_accessed:
            citation_parts.append(
                f'[Accessed: {datetime.today().strftime("%d-%b-%Y")}]'
            )
    elif fmt.lower() == "harvard":
        if url_data.author:
            citation_parts.append(f"{url_data.author},")
        if url_data.title:
            citation_parts.append(f"{url_data.title}.")
        if not no_url:
            citation_parts.append(f"Available at: {url}")
        if date_accessed:
            citation_parts.append(f"(Accessed: {date_accessed})")
    else:
        return "Unsupported format. Please use one of the following: apa, mla, chicago, IEEE, Harvard."

    citation = " ".join(part for part in citation_parts if part).strip()
    citation = re.sub(r"\s+", " ", citation)
    citation = re.sub(r"([,\.])\1+", r"\1", citation)
    citation = re.sub(r"\s([,\.])", r"\1", citation)
    return citation
