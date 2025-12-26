"""Simple tests."""

from src.tools.calculators import e1rm, ipf_gl, plates


def test_e1rm():
    assert e1rm(100, 5) == 116.7
    assert e1rm(140, 1) == 140


def test_ipf_gl():
    result = ipf_gl(600, 83, is_male=True)
    assert result > 0


def test_plates():
    result = plates(140)
    assert result["actual"] == 140
    assert 25 in result["plates"]
