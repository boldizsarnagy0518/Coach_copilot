"""Powerlifting calculator tools with LangChain tool decorators."""

from langchain_core.tools import tool
from pydantic import BaseModel, Field


class E1RMInput(BaseModel):
    """Input for E1RM calculation."""

    weight: float = Field(description="Weight lifted in kg")
    reps: int = Field(description="Number of repetitions performed")


class IPFGLInput(BaseModel):
    """Input for IPF Goodlift points calculation."""

    total: float = Field(description="Total weight lifted (S+B+D) in kg")
    bodyweight: float = Field(description="Athlete's bodyweight in kg")
    is_male: bool = Field(default=True, description="True for male, False for female")


class PlatesInput(BaseModel):
    """Input for plate loading calculation."""

    target: float = Field(description="Target weight in kg")
    bar: float = Field(default=20.0, description="Bar weight in kg (default 20kg)")


@tool(args_schema=E1RMInput)
def calculate_e1rm(weight: float, reps: int) -> str:
    """Calculate estimated 1 rep max using Epley formula. Use when user asks about 1RM or provides weight x reps."""
    if reps == 1:
        return f"E1RM: {weight} kg (actual 1RM)"
    result = round(weight * (1 + reps / 30), 1)
    return f"E1RM: {result} kg (Epley formula: {weight} × (1 + {reps}/30))"


@tool(args_schema=IPFGLInput)
def calculate_ipf_gl(total: float, bodyweight: float, is_male: bool = True) -> str:
    """Calculate IPF Goodlift points. Use when user asks about IPF points or GL score."""
    if is_male:
        coeffs = [1199.72839, 1025.18162, 0.00921]
    else:
        coeffs = [610.32796, 1045.59282, 0.03048]

    denom = coeffs[0] - coeffs[1] * (2.71828 ** (-coeffs[2] * bodyweight))
    if denom <= 0:
        return "Error: Invalid calculation (bodyweight too low)"

    points = round(100 * total / denom, 2)
    gender = "male" if is_male else "female"
    return f"IPF GL Points: {points} ({gender}, {total}kg total at {bodyweight}kg BW)"


@tool(args_schema=PlatesInput)
def calculate_plates(target: float, bar: float = 20.0) -> str:
    """Calculate plates needed per side for a target weight. Use when user asks about plate loading."""
    available = [25, 20, 15, 10, 5, 2.5, 1.25]
    per_side = (target - bar) / 2
    result = {}

    for plate in available:
        count = int(per_side // plate)
        if count > 0:
            result[plate] = count
            per_side -= count * plate

    actual = bar + sum(w * c * 2 for w, c in result.items())
    plate_str = ", ".join(f"{c}×{w}kg" for w, c in result.items())

    return f"Per side: {plate_str}. Actual total: {actual}kg (target: {target}kg)"


def e1rm(weight: float, reps: int) -> float:
    """Epley formula: weight * (1 + reps/30)"""
    if reps == 1:
        return weight
    return round(weight * (1 + reps / 30), 1)


def ipf_gl(total: float, bodyweight: float, is_male: bool = True) -> float:
    """IPF Goodlift points."""
    if is_male:
        coeffs = [1199.72839, 1025.18162, 0.00921]
    else:
        coeffs = [610.32796, 1045.59282, 0.03048]

    denom = coeffs[0] - coeffs[1] * (2.71828 ** (-coeffs[2] * bodyweight))
    if denom <= 0:
        return 0.0
    return round(100 * total / denom, 2)


def plates(target: float, bar: float = 20.0) -> dict:
    """Calculate plates per side."""
    available = [25, 20, 15, 10, 5, 2.5, 1.25]
    per_side = (target - bar) / 2
    result = {}

    for plate in available:
        count = int(per_side // plate)
        if count > 0:
            result[plate] = count
            per_side -= count * plate

    actual = bar + sum(w * c * 2 for w, c in result.items())
    return {"plates": result, "actual": actual}


ALL_TOOLS = [calculate_e1rm, calculate_ipf_gl, calculate_plates]
