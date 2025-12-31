"""Prompt loader for external prompt files."""

from pathlib import Path

_PROMPTS_DIR = Path(__file__).parent


def load_prompt(name: str) -> str:
    """Load a prompt from the prompts directory.

    Args:
        name: Prompt file name without extension (e.g., 'system', 'plan', 'grade')

    Returns:
        The prompt text content.
    """
    prompt_file = _PROMPTS_DIR / f"{name}.txt"
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
    return prompt_file.read_text(encoding="utf-8")


# Pre-load commonly used prompts for performance
SYSTEM_PROMPT = load_prompt("system")
PLAN_PROMPT = load_prompt("plan")
GRADE_PROMPT = load_prompt("grade")
