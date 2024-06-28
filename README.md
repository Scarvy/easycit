# easycit - Create Citations from the command-line

[![PyPI](https://img.shields.io/pypi/v/easycit.svg)](https://pypi.org/project/easycit/)
[![Changelog](https://img.shields.io/github/v/release/Scarvy/easycit?include_prereleases&label=changelog)](https://github.com/Scarvy/easycit/releases)
[![Tests](https://github.com/Scarvy/easycit/actions/workflows/test.yml/badge.svg)](https://github.com/Scarvy/easycit/actions/workflows/test.yml)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/Scarvy/easycit/blob/master/LICENSE)

Easily create citations from website URLs.

## Installation

> [!WARNING]
> Not available to pip install... yet. I apologize for the inconvenience.

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
easycit <URL> -f <format>
```

#### Available Options

* -f, --fmt [mla|apa|chicago|IEEE|Harvard]: The citation format (default: mla).
* --no-date: Omit the accessed date from the citation.
* --no-url: Omit the URL from the citation.
* --override <field> <value>: Override specific fields (e.g., --override author "John Doe").

### Batch Processing
To generate citations for multiple URLs from a file, use the following command:

```bash
easycit batch_citations <file> -f <format>
```

### Examples

**Generate an MLA citation:**

```bash
easycit https://realpython.com/python-serialize-data/ -f mla
```

**Generate an APA citation without the accessed date:**

```bash
easycit https://realpython.com/python-serialize-data/ -f apa --no-date
```

**Generate a Chicago citation without the URL:**

```bash
easycit https://realpython.com/python-serialize-data/ -f chicago --no-url
```

**Override the author and title fields:**

```bash
easycit https://realpython.com/python-serialize-data/ -f apa --override author "John Doe"
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
