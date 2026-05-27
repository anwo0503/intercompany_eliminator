from __future__ import annotations

from datetime import date
from unittest.mock import patch

import pandas as pd
import pytest

from engine.parser import filter_by_period, parse_buy_file, parse_sell_file


def _make_buy_raw(rows: list[dict]) -> pd.DataFrame:
    """Build a raw buy DataFrame (19 cols) from a list of row dicts."""
    raw_rows = []
    for row in rows:
        r: list[object] = [None] * 19
        r[0] = row.get("item", "")
        r[7] = row.get("supplier", "")
        r[8] = row.get("po_code", "")
        r[11] = row.get("invoice_date", "")
        r[12] = row.get("quantity", 0)
        r[17] = row.get("total_money", 0)
        raw_rows.append(r)
    return pd.DataFrame(raw_rows)


def _make_sell_raw(rows: list[dict]) -> pd.DataFrame:
    """Build a raw sell DataFrame (41 cols) from a list of row dicts."""
    raw_rows = []
    for row in rows:
        r: list[object] = [None] * 41
        r[1] = row.get("seller", "")
        r[5] = row.get("invoice_date", "")
        r[8] = row.get("item", "")
        r[13] = row.get("quantity", 0)
        r[17] = row.get("total_money", 0)
        r[25] = row.get("customer", "")
        r[30] = row.get("so_code", "")
        raw_rows.append(r)
    return pd.DataFrame(raw_rows)


_BUY_ROWS = [
    # 3 internal rows — supplier resolves to SP (the seller)
    {"item": "Drug A", "supplier": "cty cổ phần dược s.pharm", "po_code": "Purchase Order #POR26T007819", "invoice_date": "2026-01-05", "quantity": 10, "total_money": 500000},
    {"item": "Drug B", "supplier": "cty cổ phần dược s.pharm", "po_code": "Purchase Order #POR26T007820", "invoice_date": "2026-01-06", "quantity": 5, "total_money": 250000},
    {"item": "Drug C", "supplier": "sp", "po_code": "Purchase Order #POR26T007821", "invoice_date": "2026-01-07", "quantity": 20, "total_money": 1000000},
    # 2 external rows — supplier does not resolve
    {"item": "Drug X", "supplier": "External Corp", "po_code": "Purchase Order #EXT001", "invoice_date": "2026-01-05", "quantity": 1, "total_money": 99000},
    {"item": "Drug Y", "supplier": "Unknown Supplier", "po_code": "Purchase Order #EXT002", "invoice_date": "2026-01-05", "quantity": 2, "total_money": 99000},
]

_SELL_ROWS = [
    # 3 internal rows — customer resolves to TVP (the buyer)
    {"item": "Drug A", "seller": "sp", "customer": "công ty cổ phần dược phẩm tv.pharm", "so_code": "Sales Order #SOD26SP5", "invoice_date": "2026-01-05", "quantity": 10, "total_money": 500000},
    {"item": "Drug B", "seller": "sp", "customer": "tvp", "so_code": "Sales Order #SOD26SP6", "invoice_date": "2026-01-06", "quantity": 5, "total_money": 250000},
    {"item": "Drug C", "seller": "sp", "customer": "mb dược tv.pharm", "so_code": "Sales Order #SOD26SP7", "invoice_date": "2026-01-07", "quantity": 20, "total_money": 1000000},
    # 2 external rows — customer does not resolve
    {"item": "Drug X", "seller": "sp", "customer": "External Customer", "so_code": "Sales Order #EXT001", "invoice_date": "2026-01-05", "quantity": 1, "total_money": 99000},
    {"item": "Drug Y", "seller": "sp", "customer": "Outsider Co", "so_code": "Sales Order #EXT002", "invoice_date": "2026-01-05", "quantity": 2, "total_money": 99000},
]


def test_parse_buy_filters_external_rows():
    with patch("engine.parser.pd.read_excel", return_value=_make_buy_raw(_BUY_ROWS)):
        result = parse_buy_file("dummy.xlsx", "SP")
    assert len(result) == 3
    assert list(result.columns) == ["item", "supplier_short", "po_code", "invoice_date", "quantity", "total_money"]
    assert (result["supplier_short"] == "SP").all()


def test_parse_buy_strips_po_prefix():
    with patch("engine.parser.pd.read_excel", return_value=_make_buy_raw(_BUY_ROWS)):
        result = parse_buy_file("dummy.xlsx", "SP")
    assert result.iloc[0]["po_code"] == "POR26T007819"
    assert result.iloc[1]["po_code"] == "POR26T007820"


def test_parse_sell_filters_external_rows():
    with patch("engine.parser.pd.read_excel", return_value=_make_sell_raw(_SELL_ROWS)):
        result = parse_sell_file("dummy.xlsx", "TVP")
    assert len(result) == 3
    assert list(result.columns) == ["item", "customer_short", "seller_short", "so_code", "invoice_date", "quantity", "total_money"]
    assert (result["customer_short"] == "TVP").all()


def test_parse_sell_strips_so_prefix():
    with patch("engine.parser.pd.read_excel", return_value=_make_sell_raw(_SELL_ROWS)):
        result = parse_sell_file("dummy.xlsx", "TVP")
    assert result.iloc[0]["so_code"] == "SOD26SP5"
    assert result.iloc[1]["so_code"] == "SOD26SP6"


def test_excel_serial_date_conversion():
    from engine.parser import _parse_date
    assert _parse_date(46027) == date(2026, 1, 5)


def test_filter_by_period_includes_boundaries():
    df = pd.DataFrame({
        "invoice_date": [date(2026, 1, 1), date(2026, 1, 15), date(2026, 1, 31), date(2026, 2, 1)],
        "value": [1, 2, 3, 4],
    })
    result = filter_by_period(df, date(2026, 1, 1), date(2026, 1, 31))
    assert len(result) == 3
    assert list(result["value"]) == [1, 2, 3]


def test_filter_by_period_excludes_outside():
    df = pd.DataFrame({
        "invoice_date": [date(2025, 12, 31), date(2026, 1, 1), date(2026, 2, 1)],
        "value": [1, 2, 3],
    })
    result = filter_by_period(df, date(2026, 1, 1), date(2026, 1, 31))
    assert len(result) == 1
    assert result.iloc[0]["value"] == 2
