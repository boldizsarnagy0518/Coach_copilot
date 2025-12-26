"""Google Sheets tools with LangChain decorators."""

import re
from pathlib import Path
from langchain_core.tools import tool
from pydantic import BaseModel, Field

import gspread
from google.oauth2.service_account import Credentials
from src.config import settings


SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


# --- Pydantic Schemas ---


class ReadSheetInput(BaseModel):
    """Input for reading a sheet."""

    sheet_name: str = Field(
        default="", description="Sheet name to read, empty for newest"
    )


class UpdateCellInput(BaseModel):
    """Input for updating a cell."""

    cell: str = Field(description="Cell reference like 'A1' or 'B5'")
    value: str = Field(description="Value to write")
    sheet_name: str = Field(default="", description="Sheet name, empty for newest")


# --- Helper Functions ---


def get_sheets_client(credentials_path: str = None, spreadsheet_id: str = None):
    """Get authenticated Sheets client."""
    creds_path = Path(credentials_path or settings.google_sheets_credentials_path or "")
    sheet_id = spreadsheet_id or settings.google_sheets_spreadsheet_id

    if not creds_path.exists():
        return None

    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    client = gspread.authorize(creds)
    return client.open_by_key(sheet_id) if sheet_id else None


def get_gspread_client(credentials_path: str = None):
    """Get raw gspread client (for listing all spreadsheets)."""
    creds_path = Path(credentials_path or settings.google_sheets_credentials_path or "")

    if not creds_path.exists():
        return None

    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    return gspread.authorize(creds)


def list_all_spreadsheets(credentials_path: str = None) -> list[dict]:
    """List all spreadsheets shared with the service account."""
    client = get_gspread_client(credentials_path)
    if not client:
        return []

    try:
        sheets = client.openall()
        return [{"name": s.title, "id": s.id} for s in sheets]
    except Exception as e:
        print(f"Error listing spreadsheets: {e}")
        return []


def get_spreadsheet_by_name(name: str, credentials_path: str = None):
    """Get a spreadsheet by its title (athlete name)."""
    client = get_gspread_client(credentials_path)
    if not client:
        return None

    try:
        return client.open(name)
    except Exception as e:
        print(f"Error opening spreadsheet '{name}': {e}")
        return None


def parse_sheet_name(name: str) -> tuple[int, int]:
    """Parse CnumberBnumber format. Example: C3B6 -> (3, 6)"""
    match = re.match(r"C(\d+)B(\d+)", name, re.IGNORECASE)
    if match:
        return int(match.group(1)), int(match.group(2))
    return 0, 0


def get_newest_sheet(spreadsheet) -> str:
    """Find the newest sheet using CnumberBnumber logic."""
    if not spreadsheet:
        return None

    sheets = [(ws.title, parse_sheet_name(ws.title)) for ws in spreadsheet.worksheets()]
    sheets.sort(key=lambda x: (x[1][0], x[1][1]), reverse=True)
    return sheets[0][0] if sheets else None


def read_sheet(spreadsheet, sheet_name: str = None) -> list[dict]:
    """Read sheet as list of dicts."""
    if not spreadsheet:
        return []

    sheet_name = sheet_name or get_newest_sheet(spreadsheet)
    if not sheet_name:
        return []

    worksheet = spreadsheet.worksheet(sheet_name)

    try:
        rows = worksheet.get_all_values()
        if not rows:
            return []

        headers = rows[0]
        data = []
        for row in rows[1:]:
            item = {h: val for h, val in zip(headers, row) if h.strip()}
            data.append(item)
        return data
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return []


# --- Tool Functions ---


@tool(args_schema=ReadSheetInput)
def read_training_sheet(sheet_name: str = "") -> str:
    """Read training data from Google Sheets. Use when user asks about their workout, training plan, or schedule."""
    spreadsheet = get_sheets_client()
    if not spreadsheet:
        return "Error: Google Sheets not configured. Check credentials."

    data = read_sheet(spreadsheet, sheet_name if sheet_name else None)
    if not data:
        return "No training data found."

    # Format for LLM consumption
    lines = []
    for i, row in enumerate(data[:10], 1):  # Limit to 10 rows
        row_str = ", ".join(f"{k}: {v}" for k, v in row.items() if v)
        lines.append(f"Row {i}: {row_str}")

    return f"Training data ({len(data)} rows total, showing first 10):\n" + "\n".join(
        lines
    )


@tool(args_schema=UpdateCellInput)
def update_training_cell(cell: str, value: str, sheet_name: str = "") -> str:
    """Update a specific cell in the training sheet. Use when user wants to modify their plan."""
    spreadsheet = get_sheets_client()
    if not spreadsheet:
        return "Error: Google Sheets not configured."

    target_sheet = sheet_name if sheet_name else get_newest_sheet(spreadsheet)
    if not target_sheet:
        return "Error: No sheet found."

    try:
        worksheet = spreadsheet.worksheet(target_sheet)
        worksheet.update_acell(cell, value)
        return f"Successfully updated {cell} to '{value}' in sheet '{target_sheet}'"
    except Exception as e:
        return f"Error updating cell: {e}"


@tool
def list_training_sheets() -> str:
    """List all available training sheets. Use when user asks about their training history or blocks."""
    spreadsheet = get_sheets_client()
    if not spreadsheet:
        return "Error: Google Sheets not configured."

    sheets = [ws.title for ws in spreadsheet.worksheets()]
    sheets_sorted = sorted(sheets, key=lambda x: parse_sheet_name(x), reverse=True)

    return f"Available training sheets ({len(sheets)}):\n" + "\n".join(
        f"- {s}" for s in sheets_sorted
    )


# Export all tools
ALL_TOOLS = [read_training_sheet, update_training_cell, list_training_sheets]
