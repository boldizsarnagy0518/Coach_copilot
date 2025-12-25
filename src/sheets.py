"""Google Sheets integration with CnumberBnumber logic."""

import re
from pathlib import Path
import gspread
from google.oauth2.service_account import Credentials
from src.config import settings


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def get_sheets_client(credentials_path: str = None, spreadsheet_id: str = None):
    """Get authenticated Sheets client."""
    creds_path = Path(credentials_path or settings.google_sheets_credentials_path or "")
    sheet_id = spreadsheet_id or settings.google_sheets_spreadsheet_id

    if not creds_path.exists():
        return None

    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id) if sheet_id else None


def parse_sheet_name(name: str) -> tuple[int, int]:
    """
    Parse CnumberBnumber format.
    Example: C3B6 -> (3, 6)

    Logic: C > B, so C3B1 is newer than C2B10
    """
    match = re.match(r"C(\d+)B(\d+)", name, re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 0


def get_newest_sheet(spreadsheet) -> str:
    """
    Find the newest sheet using CnumberBnumber logic.
    C3B6 > C3B4 > C2B10
    """
    if not spreadsheet:
        return None

    sheets = [(ws.title, parse_sheet_name(ws.title)) for ws in spreadsheet.worksheets()]
    sheets.sort(key=lambda x: (x[1][0], x[1][1]), reverse=True)
    return sheets[0][0] if sheets else None


def read_sheet(spreadsheet, sheet_name: str = None) -> list[dict]:
    """Read sheet as list of dicts (first row = headers)."""
    if not spreadsheet:
        return []

    sheet_name = sheet_name or get_newest_sheet(spreadsheet)
    if not sheet_name:
        return []

    worksheet = spreadsheet.worksheet(sheet_name)

    # get_all_records() fails if headers have duplicates (even empty strings)
    # So we use get_all_values() and parse manually
    try:
        rows = worksheet.get_all_values()
        if not rows:
            return []

        headers = rows[0]
        data = []
        for row in rows[1:]:
            # Zip headers with row values, ignoring empty headers
            item = {h: val for h, val in zip(headers, row) if h.strip()}
            data.append(item)
        return data
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return []


def append_row(spreadsheet, values: list, sheet_name: str = None):
    """Append row to the newest sheet."""
    if not spreadsheet:
        return

    sheet_name = sheet_name or get_newest_sheet(spreadsheet)
    if not sheet_name:
        return

    worksheet = spreadsheet.worksheet(sheet_name)
    worksheet.append_row(values)
