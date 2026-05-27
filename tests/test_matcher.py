from __future__ import annotations

from datetime import date

import pandas as pd
import pytest

from engine.matcher import AMOUNT_TOLERANCE, match_transactions


def make_buy(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["item", "po_code", "invoice_date", "quantity", "total_money"])


def make_sell(rows: list[tuple]) -> pd.DataFrame:
    return pd.DataFrame(rows, columns=["item", "so_code", "invoice_date", "quantity", "total_money"])


def test_exact_match_basic():
    buy = make_buy([("ItemA", "PO001", date(2024, 1, 10), 21000, 8683038)])
    sell = make_sell([("ItemA", "SO001", date(2024, 1, 10), 21000, 8683038)])
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 1
    assert len(result.amount_mismatches) == 0
    assert len(result.unmatched_buy) == 0
    assert len(result.unmatched_sell) == 0
    row = result.exact_matches.iloc[0]
    assert row["buy_total_money"] == 8683038
    assert row["sell_total_money"] == 8683038


def test_amount_mismatch_small_diff():
    buy = make_buy([("ItemA", "PO001", date(2024, 1, 10), 21000, 8683038)])
    sell = make_sell([("ItemA", "SO001", date(2024, 1, 10), 21000, 8683036)])
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 0
    assert len(result.amount_mismatches) == 1
    assert len(result.unmatched_buy) == 0
    assert len(result.unmatched_sell) == 0
    row = result.amount_mismatches.iloc[0]
    assert row["buy_total_money"] == 8683038
    assert row["sell_total_money"] == 8683036


def test_unmatched_buy():
    buy = make_buy([("ItemA", "PO001", date(2024, 1, 10), 21000, 8683038)])
    sell = make_sell([])
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 0
    assert len(result.amount_mismatches) == 0
    assert len(result.unmatched_buy) == 1
    assert len(result.unmatched_sell) == 0


def test_unmatched_sell():
    buy = make_buy([])
    sell = make_sell([("ItemA", "SO001", date(2024, 1, 10), 21000, 8683038)])
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 0
    assert len(result.amount_mismatches) == 0
    assert len(result.unmatched_buy) == 0
    assert len(result.unmatched_sell) == 1


def test_one_to_one_consumption_two_identical_pairs():
    """Two buy rows and two sell rows with identical (money, qty) — each buy claims one sell."""
    buy = make_buy([
        ("ItemA", "PO001", date(2024, 1, 10), 21000, 8683038),
        ("ItemB", "PO002", date(2024, 1, 11), 21000, 8683038),
    ])
    sell = make_sell([
        ("ItemA", "SO001", date(2024, 1, 10), 21000, 8683038),
        ("ItemB", "SO002", date(2024, 1, 11), 21000, 8683038),
    ])
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 2
    assert len(result.amount_mismatches) == 0
    assert len(result.unmatched_buy) == 0
    assert len(result.unmatched_sell) == 0


def test_one_to_one_second_sell_not_reused():
    """One buy row with two matching sell rows — only one sell row is consumed."""
    buy = make_buy([("ItemA", "PO001", date(2024, 1, 10), 21000, 8683038)])
    sell = make_sell([
        ("ItemA", "SO001", date(2024, 1, 10), 21000, 8683038),
        ("ItemA", "SO002", date(2024, 1, 11), 21000, 8683038),
    ])
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 1
    assert len(result.unmatched_sell) == 1


def test_date_tiebreaker_nearest():
    """Three buy/sell rows all sharing (money, qty) — paired by closest invoice_date."""
    buy = make_buy([
        ("ItemA", "PO001", date(2024, 1, 1),  21000, 8683038),
        ("ItemB", "PO002", date(2024, 1, 15), 21000, 8683038),
        ("ItemC", "PO003", date(2024, 1, 30), 21000, 8683038),
    ])
    sell = make_sell([
        ("ItemA", "SO001", date(2024, 1, 2),  21000, 8683038),   # closest to Jan 1
        ("ItemB", "SO002", date(2024, 1, 14), 21000, 8683038),   # closest to Jan 15
        ("ItemC", "SO003", date(2024, 1, 28), 21000, 8683038),   # closest to Jan 30
    ])
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 3
    assert len(result.unmatched_buy) == 0
    assert len(result.unmatched_sell) == 0
    # Verify buy Jan 1 paired with sell Jan 2
    row = result.exact_matches[result.exact_matches["buy_invoice_date"] == date(2024, 1, 1)].iloc[0]
    assert row["sell_invoice_date"] == date(2024, 1, 2)


def test_date_tiebreaker_prefers_exact_date():
    """When an exact date match exists among candidates, it is preferred over a closer one."""
    buy = make_buy([("ItemA", "PO001", date(2024, 1, 10), 21000, 8683038)])
    sell = make_sell([
        ("ItemA", "SO001", date(2024, 1, 11), 21000, 8683038),  # 1 day away
        ("ItemB", "SO002", date(2024, 1, 10), 21000, 8683038),  # exact date match
    ])
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 1
    assert result.exact_matches.iloc[0]["sell_so_code"] == "SO002"
    assert len(result.unmatched_sell) == 1


def test_beyond_tolerance_is_unmatched():
    """Difference > 10 VND → both rows go to unmatched."""
    buy = make_buy([("ItemA", "PO001", date(2024, 1, 10), 21000, 8683038)])
    sell = make_sell([("ItemA", "SO001", date(2024, 1, 10), 21000, 8683027)])  # diff = 11
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 0
    assert len(result.amount_mismatches) == 0
    assert len(result.unmatched_buy) == 1
    assert len(result.unmatched_sell) == 1


def test_at_tolerance_boundary():
    """Difference = 10 VND → amount mismatch (within tolerance)."""
    buy = make_buy([("ItemA", "PO001", date(2024, 1, 10), 21000, 8683038)])
    sell = make_sell([("ItemA", "SO001", date(2024, 1, 10), 21000, 8683028)])  # diff = 10
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 0
    assert len(result.amount_mismatches) == 1
    assert len(result.unmatched_buy) == 0
    assert len(result.unmatched_sell) == 0


def test_aggregation_sums_by_key():
    """Multiple buy rows with the same item+po_code are aggregated before matching."""
    buy = make_buy([
        ("ItemA", "PO001", date(2024, 1, 5),  10000, 4000000),
        ("ItemA", "PO001", date(2024, 1, 10), 11000, 4683038),
    ])
    sell = make_sell([("ItemA", "SO001", date(2024, 1, 7), 21000, 8683038)])
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 1
    assert result.exact_matches.iloc[0]["buy_quantity"] == 21000
    assert result.exact_matches.iloc[0]["buy_total_money"] == 8683038
    # invoice_date should be the earliest
    assert result.exact_matches.iloc[0]["buy_invoice_date"] == date(2024, 1, 5)


def test_empty_inputs():
    buy = make_buy([])
    sell = make_sell([])
    result = match_transactions(buy, sell)
    assert len(result.exact_matches) == 0
    assert len(result.amount_mismatches) == 0
    assert len(result.unmatched_buy) == 0
    assert len(result.unmatched_sell) == 0


def test_custom_tolerance():
    """Tolerance parameter controls the mismatch threshold."""
    buy = make_buy([("ItemA", "PO001", date(2024, 1, 10), 21000, 8683038)])
    sell = make_sell([("ItemA", "SO001", date(2024, 1, 10), 21000, 8683033)])  # diff = 5
    # With tolerance=3, diff=5 is too large → unmatched
    result_tight = match_transactions(buy, sell, tolerance=3)
    assert len(result_tight.amount_mismatches) == 0
    assert len(result_tight.unmatched_buy) == 1
    # With tolerance=5, diff=5 is within tolerance → mismatch
    result_loose = match_transactions(buy, sell, tolerance=5)
    assert len(result_loose.amount_mismatches) == 1
    assert len(result_loose.unmatched_buy) == 0


def test_amount_tolerance_constant():
    assert AMOUNT_TOLERANCE == 10
