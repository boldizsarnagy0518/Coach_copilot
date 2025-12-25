"""Powerlifting calculators."""


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
