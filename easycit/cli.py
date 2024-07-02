import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

import click
import pyperclip
import requests
import sqlite_utils
from bs4 import BeautifulSoup
from click_default_group import DefaultGroup


@dataclass
class CitationMetaData:
    citation: str = None
    format_type: str = None
    url: str = None
    title: str = None
    author: str = None
    publisher: str = None
    date_published: str = None
    date_accessed: datetime = None


@dataclass
class WebPageDetails:
    url: str = None
    title: str = None
    author: str = None
    publisher: str = None
    date_published: str = None


def user_dir() -> Path:
    return Path(click.get_app_dir("easycit"))


def user_database_path() -> Path:
    return user_dir() / "logs.db"


def init_database():
    db_path = user_database_path()
    if not db_path.exists():
        db = sqlite_utils.Database(db_path)
        db.create_table(
            "citations",
            {
                "citation": str,
                "format_type": str,
                "url": str,
                "title": str,
                "author": str,
                "publisher": str,
                "date_published": str,
                "date_accessed": str,
            },
            hash_id_columns=["citation"],
        )
        db["citations"].enable_fts(["citation"], create_triggers=True, replace=True)
        return db
    else:
        return sqlite_utils.Database(db_path)


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
@click.option(
    "--dump", is_flag=False, default=True, help="Don't dump citation to stdout."
)
@click.option(
    "--log",
    is_flag=False,
    default=True,
    help="Prevent citation from being logged into the database.",
)
def create_citation(url, fmt, no_date, no_url, override, dump, log):
    """Generate citations in common formats."""

    citation_metadata = get_citation_metadata(url, fmt, no_date, no_url, dict(override))

    if dump:
        click.echo(citation_metadata.citation)
    if log:
        db = init_database()
        citations_table = db.table("citations")
        citations_table.upsert(asdict(citation_metadata), hash_id="id")
        citations_table.populate_fts(["citation"])

    # copy to clipboard
    pyperclip.copy(citation_metadata.citation)


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
@click.option(
    "--dump", is_flag=False, default=True, help="Don't dump citation to stdout."
)
@click.option(
    "--log",
    is_flag=False,
    default=True,
    help="Prevent citation from being logged into the database.",
)
def batch_citations(f, fmt, no_date, no_url, override, dump, log):
    """Generate citations for multiple URLs."""
    urls = [line.strip() for line in f.readlines()]

    citations = []

    for url in urls:
        if url:
            citation_metadata = get_citation_metadata(
                url, fmt, no_date, no_url, dict(override)
            )

            if dump:
                click.echo(citation_metadata.citation)
            if log:
                db = init_database()
                citations_table = db.table("citations")
                citations_table.upsert(asdict(citation_metadata), hash_id="id")
                citations_table.populate_fts(["citation"])

            # copy to clipboard
            citations.append(citation_metadata.citation)

    # build a single string of all of the citations and copy to the clipboard
    pyperclip.copy("\n".join(citation for citation in citations))


LOGS_SQL = """
    select
        id,
        citation,
        format_type,
        url,
        title,
        author,
        publisher,
        date_published,
        date_accessed
    from
        citations
    order by
        id{limit}
    """


@cli.group(
    cls=DefaultGroup,
    default="list",
    default_if_no_args=True,
)
def logs():
    "Tools for exploring logged citations."


@logs.command(name="list")
@click.option(
    "-n",
    "--count",
    type=int,
    default=None,
    help="Number of entries to show - defaults to 3, use 0 for all",
)
@click.option("-q", "--query", help="Search for logs matching this string")
def logs_list(count, query):
    """Show logged citations."""
    db = init_database()

    limit = ""
    if count is not None and count > 0:
        limit = " limit {}".format(count)

    sql = LOGS_SQL

    sql_format = {"limit": limit}

    final_sql = sql.format(**sql_format)

    if query:  # full-text search
        for row in list(db["citations"].search(query)):
            click.echo(f"{row["citation"]}")
    else:
        rows = list(db.query(final_sql))
        for row in rows:
            click.echo(f"{row["citation"]}")


@logs.command(name="path")
def logs_path():
    "Output the path to the logs.db file"
    click.echo(user_database_path())


def get_citation_metadata(
    url: str, fmt: str, no_date: bool, no_url: bool, overrides: dict
) -> CitationMetaData:
    """Get citation metadata from webpage and user ovverride values.

    Args:
        url (str): the url of the webpage.
        fmt (str): the citation format style.
        no_date (bool): If to omit the date from the citation string. Default is False.
        no_url (bool): If to omit the url from the citation string. Default to False.
        overrides (dict): A dictionary of values to override in the citation string.

    Returns:
        CitationMetaData: a dataclass containing metadata about the citation and webpage.
    """
    webpage_metadata = get_webpage_details(url)

    if "author" in overrides:
        webpage_metadata.author = overrides["author"]
    if "title" in overrides:
        webpage_metadata.title = overrides["title"]
    if "publisher" in overrides:
        webpage_metadata.publisher = overrides["publisher"]
    if "pub_date" in overrides:
        webpage_metadata.date_published = overrides["pub_date"]

    return generate_citation(webpage_metadata, fmt, no_date, no_url)


def get_webpage_details(url: str) -> WebPageDetails:
    """Extracts title, author, publication date, and publisher from the given URL.

    Args:
        url (str): the url of the webpage.

    Returns:
        WebPageDetails: a dataclass containing webpage metadata.
    """
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

        return WebPageDetails(
            url=url,
            title=title,
            author=author,
            publisher=publisher,
            date_published=pub_date,
        )
    except Exception:
        return WebPageDetails()


def generate_citation(
    website_metadata: WebPageDetails, fmt: str, no_date: bool, no_url: bool
) -> CitationMetaData:
    """Generates a citation string based on the extracted URL data and specified format.

    Args:
        website_metadata (WebPageDetails): a dataclass of website meta.
        fmt (str): the citation format style.
        no_date (bool): If to omit the date from the citation string. Default is False.
        no_url (bool): If to omit the url from the citation string. Default to False.

    Returns:
        CitationMetaData: _description_
    """
    date_accessed = datetime.today().strftime("%d %B %Y") if not no_date else None

    citation_parts = []

    if fmt.lower() == "apa":
        if website_metadata.author:
            citation_parts.append(f"{website_metadata.author}")
        citation_parts.append("(n.d.).")
        if website_metadata.title:
            citation_parts.append(f"{website_metadata.title}.")
        if website_metadata.publisher:
            citation_parts.append(f"{website_metadata.publisher}.")
        if date_accessed:
            citation_parts.append(f"Retrieved {date_accessed}")
        if not no_url:
            citation_parts.append(f"from {website_metadata.url}")
    elif fmt.lower() == "mla":
        if website_metadata.author:
            citation_parts.append(f"{website_metadata.author}.")
        if website_metadata.title:
            citation_parts.append(f'"{website_metadata.title}."')
        if website_metadata.publisher:
            citation_parts.append(f"{website_metadata.publisher}")
        if not no_url:
            citation_parts.append(f"{website_metadata.url}")
        if date_accessed:
            citation_parts.append(f"Accessed {date_accessed}.")
    elif fmt.lower() == "chicago":
        if website_metadata.author:
            citation_parts.append(f"{website_metadata.author}.")
        if website_metadata.title:
            citation_parts.append(f'"{website_metadata.title}."')
        if website_metadata.publisher:
            citation_parts.append(f"{website_metadata.publisher}.")
        if date_accessed:
            citation_parts.append(f"Accessed {date_accessed}.")
        if not no_url:
            citation_parts.append(f"{website_metadata.url}.")
    elif fmt.lower() == "ieee":
        if website_metadata.author:
            citation_parts.append(f"{website_metadata.author},")
        if website_metadata.title:
            citation_parts.append(f'"{website_metadata.title},"')
        if website_metadata.publisher:
            citation_parts.append(f"{website_metadata.publisher}.")
        citation_parts.append("[Online].")
        if not no_url:
            citation_parts.append(f"Available: {website_metadata.url}")
        if date_accessed:
            citation_parts.append(
                f'[Accessed: {datetime.today().strftime("%d-%b-%Y")}]'
            )
    elif fmt.lower() == "harvard":
        if website_metadata.author:
            citation_parts.append(f"{website_metadata.author},")
        if website_metadata.title:
            citation_parts.append(f"{website_metadata.title}.")
        if not no_url:
            citation_parts.append(f"Available at: {website_metadata.url}")
        if date_accessed:
            citation_parts.append(f"(Accessed: {date_accessed})")
    else:
        return "Unsupported format. Please use one of the following: apa, mla, chicago, IEEE, Harvard."

    citation = " ".join(part for part in citation_parts if part).strip()
    citation = re.sub(r"\s+", " ", citation)
    citation = re.sub(r"([,\.])\1+", r"\1", citation)
    citation = re.sub(r"\s([,\.])", r"\1", citation)

    return CitationMetaData(
        citation=citation,
        date_accessed=date_accessed,
        format_type=fmt,
        **{
            key: value
            for key, value in asdict(website_metadata).items()
            if key not in ["citation", "date_accessed", "format_type"]
        },
    )
