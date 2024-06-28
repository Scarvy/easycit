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


@click.group(cls=DefaultGroup, default="create_citation", default_if_no_args=True)
@click.version_option()
def cli():
    """Easily create citations from website URLs."""


@cli.command(name="create_citation")
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
def create_citation(url, fmt, no_date, no_url):
    """Generate citations in common formats."""
    url_data = get_webpage_details(url)
    citation = get_citation(url, url_data, fmt, no_date, no_url)
    print(citation)


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

    if fmt.lower() == "apa":
        citation = f'{url_data.author or ""}. (n.d.). {url_data.title or ""}. {url_data.publisher or ""}.'
        if date_accessed:
            citation += f" Retrieved {date_accessed}"
        if not no_url:
            citation += f", from {url}"
    elif fmt.lower() == "mla":
        citation = f'{url_data.author or ""}. "{url_data.title or ""}." {url_data.publisher or ""}'
        if not no_url:
            citation += f", {url}"
        if date_accessed:
            citation += f". Accessed {date_accessed}."
    elif fmt.lower() == "chicago":
        citation = f'{url_data.author or ""}. "{url_data.title or ""}." {url_data.publisher or ""}.'
        if date_accessed:
            citation += f" Accessed {date_accessed}."
        if not no_url:
            citation += f" {url}."
    elif fmt.lower() == "ieee":
        citation = f'{url_data.author or ""}, "{url_data.title or ""}," {url_data.publisher or ""}. [Online]. Available: {url}'
        if date_accessed:
            citation += f'. [Accessed: {datetime.today().strftime("%d-%b-%Y")}]'
        if no_url:
            citation = citation.replace(f" Available: {url}", "")
    elif fmt.lower() == "harvard":
        citation = (
            f'{url_data.author or ""}, {url_data.title or ""}. Available at: {url}'
        )
        if date_accessed:
            citation += f" (Accessed: {date_accessed})"
        if no_url:
            citation = citation.replace(f" Available at: {url}", "")
    else:
        citation = "Unsupported format. Please use one of the following: apa, mla, chicago, IEEE, Harvard."

    citation = re.sub(r"\s+", " ", citation).strip()
    citation = re.sub(r"([,\.])\1+", r"\1", citation)
    citation = re.sub(r"\s([,\.])", r"\1", citation)
    return citation
