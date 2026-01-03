"""Google Sheets tools with LangChain decorators."""

from pathlib import Path
from langchain_core.tools import tool
from pydantic import BaseModel, Field

import gspread
from google.oauth2.service_account import Credentials
from src.config import settings


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.readonly",
]


class ReadSheetInput(BaseModel):
    """Input for reading a sheet."""

    sheet_name: str = Field(
        default="", description="Sheet name to read, empty for default"
    )


class UpdateCellInput(BaseModel):
    """Input for updating a cell."""

    cell: str = Field(description="Cell reference like 'A1'")
    value: str = Field(description="Value to write")
    sheet_name: str = Field(default="", description="Sheet name, empty for default")


def _get_client(credentials_path: str = None):
    """Shared helper to get authenticated gspread client."""
    creds_path = (
        Path(credentials_path)
        if credentials_path
        else settings.google_sheets_credentials_path
    )
    if not creds_path.exists():
        return None

    creds = Credentials.from_service_account_file(str(creds_path), scopes=SCOPES)
    return gspread.authorize(creds)


def get_sheets_client(spreadsheet_id: str = None):
    """Get the target Spreadsheet object."""
    client = _get_client()
    if not client:
        return None

    sheet_id = spreadsheet_id or settings.google_sheets_spreadsheet_id
    if sheet_id:
        try:
            return client.open_by_key(sheet_id)
        except Exception:
            pass  # Fallback to discovery

    # Auto-discovery
    try:
        sheets = client.openall()
        if not sheets:
            return None

        for sheet in sheets:
            if "boldi" in sheet.title.lower() or "training" in sheet.title.lower():
                return sheet
        return sheets[0]
    except Exception as e:
        print(f"Error finding sheet: {e}")
        return None


def list_all_spreadsheets(credentials_path: str = None) -> list[dict]:
    """List all available spreadsheets (for UI/Login)."""
    client = _get_client(credentials_path)
    if not client:
        return []

    try:
        return [{"name": s.title, "id": s.id} for s in client.openall()]
    except Exception:
        return []


def get_spreadsheet_by_name(name: str):
    """Get spreadsheet by exact name."""
    client = _get_client()
    return client.open(name) if client else None


def get_newest_sheet(spreadsheet) -> str:
    """Get the newest worksheet by CnBn naming convention (highest C and B numbers)."""
    if not spreadsheet:
        return None

    import re

    worksheets = spreadsheet.worksheets()

    # Find sheets matching CnBn pattern and sort by (cycle, block) numbers
    cnbn_sheets = []
    for ws in worksheets:
        match = re.match(r"C(\d+)B(\d+)", ws.title, re.IGNORECASE)
        if match:
            cycle, block = int(match.group(1)), int(match.group(2))
            cnbn_sheets.append((cycle, block, ws.title))

    if cnbn_sheets:
        # Sort by cycle desc, then block desc - get the newest
        cnbn_sheets.sort(reverse=True)
        newest = cnbn_sheets[0][2]
        print(f"---Found newest sheet: {newest}---")
        return newest

    # Fallback to first sheet if no CnBn pattern found
    return spreadsheet.sheet1.title


def read_sheet(spreadsheet, sheet_name: str = None) -> list[tuple[int, list[str]]]:
    """Read sheet as list of (real_row_index, row_data) tuples. 1-based indexing."""
    if not spreadsheet:
        return []

    sheet_name = sheet_name or get_newest_sheet(spreadsheet)
    worksheet = spreadsheet.worksheet(sheet_name)

    try:
        rows = worksheet.get_all_values()
        cleaned_rows = []
        for i, row in enumerate(rows, 1):  # 1-based index
            # Keep row if it has content, but store its REAL index
            if any(cell.strip() for cell in row):
                cleaned_rows.append((i, [c.strip() for c in row]))
        return cleaned_rows
    except Exception as e:
        print(f"Error reading sheet: {e}")
        return []


@tool(args_schema=ReadSheetInput)
def read_training_sheet(sheet_name: str = "") -> str:
    """Read training data from Google Sheets."""
    spreadsheet = get_sheets_client()
    if not spreadsheet:
        return "Error: Google Sheets not configured."

    # Always use newest sheet - ignore LLM's guess
    actual_sheet = get_newest_sheet(spreadsheet)
    print(f"---TOOL: Reading sheet '{actual_sheet}' (LLM requested: '{sheet_name}')---")

    data = read_sheet(spreadsheet, actual_sheet)
    if not data:
        return "No training data found."

    lines = []
    # Limit increased to 50 rows
    for i, row in data[:50]:  # i is the REAL row number
        cleaned_row = [c for c in row if c]
        if cleaned_row:
            lines.append(f"Row {i}: " + " | ".join(cleaned_row))

    return f"Training data ({len(data)} rows total, showing first 50):\n" + "\n".join(
        lines
    )


@tool(args_schema=UpdateCellInput)
def update_training_cell(cell: str, value: str, sheet_name: str = "") -> str:
    """Update a specific cell in the training sheet."""
    spreadsheet = get_sheets_client()
    if not spreadsheet:
        return "Error: Google Sheets not configured."

    target_sheet = sheet_name if sheet_name else get_newest_sheet(spreadsheet)
    try:
        worksheet = spreadsheet.worksheet(target_sheet)
        worksheet.update_acell(cell, value)
        return f"Updated {cell} to '{value}'"
    except Exception as e:
        return f"Error updating: {e}"


@tool
def list_training_sheets() -> str:
    """List available worksheet tabs."""
    spreadsheet = get_sheets_client()
    if not spreadsheet:
        return "Error: Google Sheets not configured."

    sheets = [ws.title for ws in spreadsheet.worksheets()]
    return f"Worksheets ({len(sheets)}): " + ", ".join(sheets)


ALL_TOOLS = [read_training_sheet, update_training_cell, list_training_sheets]
