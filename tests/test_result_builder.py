from __future__ import annotations

import os
import tempfile
from datetime import date

import pandas as pd
import pytest

from engine.matcher import MatchResult
from engine.result_builder import (
    COLUMNS,
    _LABEL_MISMATCH,
    _LABEL_UNMATCHED,
    build_result_table,
    export_to_excel,
)

_MATCH_COLS = [
    "buy_item", "buy_po_code", "buy_invoice_date", "buy_quantity", "buy_total_money",
    "sell_item", "sell_so_code", "sell_invoice_date", "sell_quantity", "sell_total_money",
]
_BUY_COLS = ["item", "po_code", "invoice_date", "quantity", "total_money"]
_SELL_COLS = ["item", "so_code", "invoice_date", "quantity", "total_money"]


def _match_row(
    buy_item="ItemA",
    buy_po="PO-1",
    buy_date=date(2024, 1, 1),
    buy_qty=10,
    buy_money=1000,
    sell_item="ItemA",
    sell_so="SO-1",
    sell_date=date(2024, 1, 1),
    sell_qty=10,
    sell_money=1000,
) -> dict:
    return {
        "buy_item": buy_item, "buy_po_code": buy_po, "buy_invoice_date": buy_date,
        "buy_quantity": buy_qty, "buy_total_money": buy_money,
        "sell_item": sell_item, "sell_so_code": sell_so, "sell_invoice_date": sell_date,
        "sell_quantity": sell_qty, "sell_total_money": sell_money,
    }


def _make_result(exact=None, mismatches=None, unmatched_buy=None, unmatched_sell=None) -> MatchResult:
    return MatchResult(
        exact_matches=pd.DataFrame(exact or [], columns=_MATCH_COLS),
        amount_mismatches=pd.DataFrame(mismatches or [], columns=_MATCH_COLS),
        unmatched_buy=pd.DataFrame(unmatched_buy or [], columns=_BUY_COLS),
        unmatched_sell=pd.DataFrame(unmatched_sell or [], columns=_SELL_COLS),
    )


def _section_indices(df: pd.DataFrame) -> tuple[int, int]:
    """Return (mismatch_label_idx, unmatched_label_idx) in the result DataFrame."""
    buyer_col = df["Buyer Side"].tolist()
    return buyer_col.index(_LABEL_MISMATCH), buyer_col.index(_LABEL_UNMATCHED)


def test_all_three_sections_in_correct_order():
    """2 exact matches + 1 amount mismatch + 1 unmatched produce all three sections in order."""
    result = _make_result(
        exact=[
            _match_row(buy_item="Beta", buy_date=date(2024, 1, 2)),
            _match_row(buy_item="Alpha", buy_date=date(2024, 1, 1)),
        ],
        mismatches=[
            _match_row(buy_item="Gamma", buy_money=1000, sell_money=1005),
        ],
        unmatched_buy=[
            {"item": "Delta", "po_code": "PO-X", "invoice_date": date(2024, 1, 3), "quantity": 5, "total_money": 500},
        ],
    )
    df = build_result_table(result, "BUY_CO", "SELL_CO")

    mismatch_idx, unmatched_idx = _section_indices(df)

    # Section 1 data exists before the mismatch separator
    assert mismatch_idx >= 2  # at least 2 exact match rows before sep
    # Sections appear in the right order
    assert mismatch_idx < unmatched_idx
    # Section 1 data rows have expected Buyer Side value
    assert df.iloc[0]["Buyer Side"] == "BUY_CO"
    # Section 2 data exists between the two separators
    assert unmatched_idx > mismatch_idx + 1
    # Section 3 data exists after the unmatched separator
    assert len(df) > unmatched_idx + 1


def test_section1_sorted_by_item_then_date():
    """Rows in section 1 are sorted by Item ascending, then invoice date ascending."""
    result = _make_result(
        exact=[
            _match_row(buy_item="Beta", buy_date=date(2024, 1, 2)),
            _match_row(buy_item="Alpha", buy_date=date(2024, 1, 3)),
            _match_row(buy_item="Alpha", buy_date=date(2024, 1, 1)),
        ],
    )
    df = build_result_table(result, "B", "S")

    mismatch_idx, _ = _section_indices(df)
    # blank row is at mismatch_idx - 1, so section 1 rows are [0 .. mismatch_idx - 2]
    section1 = df.iloc[: mismatch_idx - 1].reset_index(drop=True)

    assert section1["Item"].tolist() == ["Alpha", "Alpha", "Beta"]
    alpha = section1[section1["Item"] == "Alpha"]["Invoice date — Buyer side"].tolist()
    assert alpha == sorted(alpha)


def test_unmatched_buy_blank_columns():
    """Unmatched buy row: columns D (Seller date), H (Seller money), K (SO) are blank."""
    result = _make_result(
        unmatched_buy=[
            {"item": "ItemX", "po_code": "PO-1", "invoice_date": date(2024, 3, 1), "quantity": 2, "total_money": 200},
        ],
    )
    df = build_result_table(result, "B", "S")

    _, unmatched_idx = _section_indices(df)
    section3 = df.iloc[unmatched_idx + 1 :].reset_index(drop=True)
    row = section3.iloc[0]

    # Blank: D, H, K
    assert pd.isna(row["Invoice date — Seller side"])
    assert pd.isna(row["Total money — Seller side"])
    assert pd.isna(row["Sales order"])
    # Present: C, G, J
    assert row["Invoice date — Buyer side"] == date(2024, 3, 1)
    assert row["Total money — Buyer side"] == 200
    assert row["Purchase order"] == "PO-1"


def test_unmatched_sell_blank_columns():
    """Unmatched sell row: columns C (Buyer date), G (Buyer money), J (PO) are blank."""
    result = _make_result(
        unmatched_sell=[
            {"item": "ItemY", "so_code": "SO-2", "invoice_date": date(2024, 4, 1), "quantity": 3, "total_money": 300},
        ],
    )
    df = build_result_table(result, "B", "S")

    _, unmatched_idx = _section_indices(df)
    section3 = df.iloc[unmatched_idx + 1 :].reset_index(drop=True)
    row = section3.iloc[0]

    # Blank: C, G, J
    assert pd.isna(row["Invoice date — Buyer side"])
    assert pd.isna(row["Total money — Buyer side"])
    assert pd.isna(row["Purchase order"])
    # Present: D, H, K
    assert row["Invoice date — Seller side"] == date(2024, 4, 1)
    assert row["Total money — Seller side"] == 300
    assert row["Sales order"] == "SO-2"


def test_separator_rows_with_blank_preceding_row():
    """Section separator rows exist and are preceded by a blank row."""
    result = _make_result(
        exact=[_match_row()],
        mismatches=[_match_row(buy_money=1000, sell_money=1005)],
        unmatched_buy=[
            {"item": "X", "po_code": "PO-Z", "invoice_date": None, "quantity": 1, "total_money": 100},
        ],
    )
    df = build_result_table(result, "B", "S")

    mismatch_idx, unmatched_idx = _section_indices(df)

    # Blank row immediately before each label
    assert pd.isna(df.iloc[mismatch_idx - 1]["Buyer Side"])
    assert pd.isna(df.iloc[unmatched_idx - 1]["Buyer Side"])


def test_export_to_excel_creates_readable_file():
    """export_to_excel writes a valid Excel file with the correct number of columns."""
    result = _make_result(
        exact=[_match_row(buy_date=date(2024, 1, 1), sell_date=date(2024, 1, 1))],
    )
    df = build_result_table(result, "BUY", "SELL")

    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
        path = f.name
    try:
        export_to_excel(df, path)
        assert os.path.exists(path)
        assert os.path.getsize(path) > 0
        wb_df = pd.read_excel(path)
        assert list(wb_df.columns) == COLUMNS
    finally:
        os.unlink(path)
