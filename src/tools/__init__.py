"""All tools for the coach agent."""

from src.tools.calculators import ALL_TOOLS as CALCULATOR_TOOLS
from src.tools.sheets import ALL_TOOLS as SHEETS_TOOLS
from src.tools.youtube import ALL_TOOLS as YOUTUBE_TOOLS
from src.tools.web_search import ALL_TOOLS as WEB_TOOLS
from src.tools.rpe_logger import ALL_TOOLS as RPE_TOOLS
from src.tools.meet_tracker import ALL_TOOLS as MEET_TOOLS

ALL_TOOLS = (
    CALCULATOR_TOOLS + SHEETS_TOOLS + YOUTUBE_TOOLS + WEB_TOOLS + RPE_TOOLS + MEET_TOOLS
)
