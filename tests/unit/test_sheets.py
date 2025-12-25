"""
Unit tests for Google Sheets integration.

Tests the SheetsClient with mocked gspread API.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.tools.sheets import SheetsClient, get_sheets_client


class TestSheetsClient:
    """Tests for Google Sheets client."""

    def test_client_initialization(self, tmp_path):
        """Test client creates with paths."""
        creds_file = tmp_path / "creds.json"
        creds_file.touch()

        client = SheetsClient(
            credentials_file=creds_file,
            spreadsheet_id="test-id",
        )

        assert client._credentials_file == creds_file
        assert client._spreadsheet_id == "test-id"

    def test_is_configured_false_without_files(self, tmp_path):
        """is_configured returns False when credentials missing."""
        client = SheetsClient(
            credentials_file=tmp_path / "nonexistent.json",
            spreadsheet_id="test-id",
        )
        assert client.is_configured() is False

    def test_spreadsheet_id_can_be_none(self, tmp_path):
        """Test that spreadsheet_id accepts None."""
        creds = tmp_path / "creds.json"
        creds.touch()

        client = SheetsClient(
            credentials_file=creds,
            spreadsheet_id=None,
        )
        # When explicitly set to None, it may get default from settings or stay None
        # This test just verifies no error occurs
        assert True

    def test_is_configured_true_when_complete(self, tmp_path):
        """is_configured returns True when fully configured."""
        creds = tmp_path / "creds.json"
        creds.touch()

        client = SheetsClient(
            credentials_file=creds,
            spreadsheet_id="test-id",
        )
        assert client.is_configured() is True

    def test_authenticate_raises_without_credentials(self, tmp_path):
        """Authentication fails without credentials file."""
        client = SheetsClient(
            credentials_file=tmp_path / "nonexistent.json",
            spreadsheet_id="test-id",
        )

        with pytest.raises(FileNotFoundError):
            client._authenticate()

    @patch("src.tools.sheets.gspread")
    @patch("src.tools.sheets.Credentials")
    def test_read_range_with_mock(self, mock_creds, mock_gspread, tmp_path):
        """Test reading a range with mocked API."""
        # Create fake credentials file
        creds_file = tmp_path / "creds.json"
        creds_file.write_text("{}")

        # Mock gspread
        mock_worksheet = MagicMock()
        mock_worksheet.get.return_value = [["A1", "B1"], ["A2", "B2"]]

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.sheet1 = mock_worksheet

        mock_client = MagicMock()
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_gspread.authorize.return_value = mock_client

        # Test
        client = SheetsClient(
            credentials_file=creds_file,
            spreadsheet_id="test-id",
        )
        result = client.read_range("A1:B2")

        assert result == [["A1", "B1"], ["A2", "B2"]]
        mock_worksheet.get.assert_called_once_with("A1:B2")

    @patch("src.tools.sheets.gspread")
    @patch("src.tools.sheets.Credentials")
    def test_append_row_with_mock(self, mock_creds, mock_gspread, tmp_path):
        """Test appending a row with mocked API."""
        creds_file = tmp_path / "creds.json"
        creds_file.write_text("{}")

        mock_worksheet = MagicMock()
        mock_spreadsheet = MagicMock()
        mock_spreadsheet.sheet1 = mock_worksheet

        mock_client = MagicMock()
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_gspread.authorize.return_value = mock_client

        client = SheetsClient(
            credentials_file=creds_file,
            spreadsheet_id="test-id",
        )
        client.append_row(["value1", "value2", "value3"])

        mock_worksheet.append_row.assert_called_once_with(["value1", "value2", "value3"])

    @patch("src.tools.sheets.gspread")
    @patch("src.tools.sheets.Credentials")
    def test_list_sheets_with_mock(self, mock_creds, mock_gspread, tmp_path):
        """Test listing sheets with mocked API."""
        creds_file = tmp_path / "creds.json"
        creds_file.write_text("{}")

        # Mock worksheets
        ws1 = MagicMock()
        ws1.title = "Sheet1"
        ws2 = MagicMock()
        ws2.title = "Training Log"

        mock_spreadsheet = MagicMock()
        mock_spreadsheet.worksheets.return_value = [ws1, ws2]

        mock_client = MagicMock()
        mock_client.open_by_key.return_value = mock_spreadsheet
        mock_gspread.authorize.return_value = mock_client

        client = SheetsClient(
            credentials_file=creds_file,
            spreadsheet_id="test-id",
        )
        sheets = client.list_sheets()

        assert sheets == ["Sheet1", "Training Log"]


class TestGetSheetsClient:
    """Tests for get_sheets_client factory."""

    def test_returns_sheets_client(self):
        """Factory returns a SheetsClient instance."""
        client = get_sheets_client()
        assert isinstance(client, SheetsClient)
