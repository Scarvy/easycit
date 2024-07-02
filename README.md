# easycit - Create Citations from the command-line

[![PyPI](https://img.shields.io/pypi/v/easycit.svg)](https://pypi.org/project/easycit/)
[![Changelog](https://img.shields.io/github/v/release/Scarvy/easycit?include_prereleases&label=changelog)](https://github.com/Scarvy/easycit/releases)
[![Tests](https://github.com/Scarvy/easycit/actions/workflows/test.yml/badge.svg)](https://github.com/Scarvy/easycit/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/Scarvy/easycit/blob/master/LICENSE)

Easily create citations from website URLs.

## Installation

Install this tool using `pip`:
```bash
pip install easycit
```
## Usage

For help, run:
```bash
easycit --help
```
You can also use:
```bash
python -m easycit --help
```

### Generate a Citation

To generate a citation, use the following command:

```bash
easycit create <URL> -f <format>
```

#### Available Options

* -f, --fmt [mla|apa|chicago|IEEE|Harvard]: The citation format (default: mla).
* --no-date: Omit the accessed date from the citation.
* --no-url: Omit the URL from the citation.
* --override <field> <value>: Override specific fields (e.g., --override author "John Doe").
* --dump: Don't dump citation to stdout (default: True).
* --log: Prevent citation from being logged into the database (default: True).

### Batch Processing

To generate citations for multiple URLs from a file, use the following command:

```bash
easycit batch <file> -f <format>
```

#### Available Options

* -f, --fmt [mla|apa|chicago|IEEE|Harvard]: The citation format (default: mla).
* --no-date: Omit the accessed date from the citation.
* --no-url: Omit the URL from the citation.
* --override <field> <value>: Override specific fields (e.g., --override author "John Doe").
* --dump: Don't dump citation to stdout (default: True).
* --log: Prevent citation from being logged into the database (default: True).

### List Logs

To list the logged citations, use the following command:

```bash
easycit logs list
```

#### Available Options

* -n, --count <number>: Number of entries to show - defaults to 3, use 0 for all.
* -q, --query <string>: Search for logs matching this string.

### Examples

**Generate an MLA citation:**

```bash
easycit create https://realpython.com/python-serialize-data/ -f mla
```

**Generate an APA citation without the accessed date:**

```bash
easycit create https://realpython.com/python-serialize-data/ -f apa --no-date
```

**Generate a Chicago citation without the URL:**

```bash
easycit create https://realpython.com/python-serialize-data/ -f chicago --no-url
```

**Override the author and title fields:**

```bash
easycit create https://realpython.com/python-serialize-data/ -f apa --override author "John Doe" --override title "Custom Title"
```

**Generate citations for multiple URLs from a file:**

```bash
easycit batch urls.txt -f mla
```

**List all logged citations:**

```bash
easycit logs list --count 3
```

**Search for logged citations containing a specific string:**

```bash
easycit logs list --query "Python"
```

## Browsing logs using Datasette

You can also use [Datesette](https://datasette.io/) to browse your logs like this:

```bash
datasette "$(easycit logs path)"
```

## Development

To contribute to this tool, first checkout the code. Then create a new virtual environment:
```bash
cd easycit
python -m venv venv
source venv/bin/activate
```
Now install the dependencies and test dependencies:
```bash
pip install -e '.[test]'
```
To run the tests:
```bash
pytest
```