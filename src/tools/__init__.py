"""Tools package - exports all available tools."""

# Calculator tools
from src.tools.calculators import (
    calculate_e1rm,
    calculate_ipf_gl,
    calculate_plates,
    e1rm,
    ipf_gl,
    plates,
    ALL_TOOLS as CALCULATOR_TOOLS,
)

# Sheets tools
from src.tools.sheets import (
    read_training_sheet,
    update_training_cell,
    list_training_sheets,
    get_sheets_client,
    get_newest_sheet,
    read_sheet,
    ALL_TOOLS as SHEETS_TOOLS,
)

# YouTube tools
from src.tools.youtube import (
    load_youtube_transcript,
    get_coach_channel_info,
    suggest_youtube_search,
    load_youtube,
    ALL_TOOLS as YOUTUBE_TOOLS,
)

# Web search tools
from src.tools.web_search import (
    search_web,
    ALL_TOOLS as WEB_TOOLS,
)

# All tools for agent binding
ALL_TOOLS = CALCULATOR_TOOLS + SHEETS_TOOLS + YOUTUBE_TOOLS + WEB_TOOLS

__all__ = [
    # Calculator
    "calculate_e1rm",
    "calculate_ipf_gl",
    "calculate_plates",
    "e1rm",
    "ipf_gl",
    "plates",
    # Sheets
    "read_training_sheet",
    "update_training_cell",
    "list_training_sheets",
    "get_sheets_client",
    "get_newest_sheet",
    "read_sheet",
    # YouTube
    "load_youtube_transcript",
    "get_coach_channel_info",
    "suggest_youtube_search",
    "load_youtube",
    # Web
    "search_web",
    # All tools list
    "ALL_TOOLS",
]
