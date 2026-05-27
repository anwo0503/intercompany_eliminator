from __future__ import annotations

import pytest
from engine.mapping import get_valid_pairs, resolve_company_name


def test_resolve_exact_match() -> None:
    assert resolve_company_name("CTY CỔ PHẦN DƯỢC S.PHARM") == "SP"


def test_resolve_case_insensitive_and_whitespace() -> None:
    assert resolve_company_name("  cty cổ phần dược s.pharm  ") == "SP"


def test_resolve_external_returns_none() -> None:
    assert resolve_company_name("WUHAN GRAND HOYO CO., LTD") is None


def test_resolve_all_short_codes() -> None:
    assert resolve_company_name("TVP") == "TVP"
    assert resolve_company_name("MBP") == "MBP"
    assert resolve_company_name("SP") == "SP"
    assert resolve_company_name("Trade") == "ATrade"
    assert resolve_company_name("Lab") == "ALab"


def test_resolve_tvpharm_branch() -> None:
    assert (
        resolve_company_name(
            "Aikya Corporation : Aikya Dược : TVPharm Holding : TVPharm : CN Hà Nội"
        )
        == "TVP"
    )


def test_get_valid_pairs_contains_expected() -> None:
    pairs = get_valid_pairs()
    expected = [
        ("TVP", "SP"),
        ("TVP", "MBP"),
        ("SP", "TVP"),
        ("MBP", "TVP"),
        ("TVP", "ATrade"),
        ("MBP", "ATrade"),
        ("SP", "ATrade"),
        ("TVP", "ALab"),
        ("MBP", "ALab"),
        ("SP", "ALab"),
    ]
    assert pairs == expected


def test_get_valid_pairs_returns_copy() -> None:
    pairs1 = get_valid_pairs()
    pairs2 = get_valid_pairs()
    assert pairs1 is not pairs2
