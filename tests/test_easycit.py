from unittest import mock

import pytest
import requests
from click.testing import CliRunner

from easycit.cli import WebPageDetails, cli, generate_citation, get_webpage_details


@pytest.fixture(scope="module")
def runner():
    return CliRunner()


class TestCitationGenerator:
    def test_version(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["--version"])
            assert result.exit_code == 0
            assert result.output.startswith("cli, version ")

    def test_create_citation(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["create", "http://example.com"])
            assert result.exit_code == 0
            assert "example.com" in result.output

    def test_create_citation_with_format(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli, ["create", "http://example.com", "--fmt", "apa"]
            )
            assert result.exit_code == 0
            assert "(n.d.)" in result.output

    def test_create_citation_no_date(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["create", "http://example.com", "--no-date"])
            assert result.exit_code == 0
            assert "Accessed" not in result.output

    def test_create_citation_no_url(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(cli, ["create", "http://example.com", "--no-url"])
            assert result.exit_code == 0
            assert "example.com" not in result.output

    def test_create_citation_override(self, runner):
        with runner.isolated_filesystem():
            result = runner.invoke(
                cli,
                ["create", "http://example.com", "--override", "author", "John Doe"],
            )
            assert result.exit_code == 0
            assert "John Doe" in result.output

    def test_batch_citations(self, runner):
        with runner.isolated_filesystem():
            with open("urls.txt", "w") as f:
                f.write("http://example.com\nhttp://example.org\n")
            result = runner.invoke(cli, ["batch", "urls.txt"])
            assert result.exit_code == 0
            assert "example.com" in result.output
            assert "example.org" in result.output

    def test_get_webpage_details(self, mocker):
        mocker.patch("requests.get")
        mock_response = mock.Mock()
        mock_response.content = '<html><head><title>Example Domain</title><meta name="author" content="John Doe"></head></html>'
        requests.get.return_value = mock_response

        details = get_webpage_details("http://example.com")
        assert details.title == "Example Domain"
        assert details.author == "John Doe"

    def test_generate_citation(self):
        webpage_details = WebPageDetails(
            url="http://example.com",
            title="Example Domain",
            author="John Doe",
            publisher="Example Publisher",
            date_published="01 Jan. 2020",
        )
        citation_metadata = generate_citation(webpage_details, "mla", True, False)
        assert "John Doe." in citation_metadata.citation
        assert '"Example Domain."' in citation_metadata.citation
        assert "Example Publisher" in citation_metadata.citation
        assert (
            'John Doe. "Example Domain." Example Publisher http://example.com'
            == citation_metadata.citation
        )
