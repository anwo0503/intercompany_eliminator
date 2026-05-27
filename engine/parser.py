from __future__ import annotations

from datetime import date, datetime, timedelta

import pandas as pd

from engine.mapping import resolve_company_name

_EXCEL_EPOCH = datetime(1899, 12, 30)


def _clean_str(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace("_x000D_", "").strip()


def _parse_date(value: object) -> date | None:
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, (int, float)):
        return (_EXCEL_EPOCH + timedelta(days=int(value))).date()
    if isinstance(value, str):
        cleaned = value.replace("_x000D_", "").strip()
        if cleaned:
            try:
                return pd.to_datetime(cleaned).date()
            except Exception:
                return None
    return None


def parse_buy_file(filepath: str, seller_short: str) -> pd.DataFrame:
    """Parse and clean the Buy Excel file. Filter to rows where supplier matches seller_short."""
    raw = pd.read_excel(filepath, header=0)

    df = pd.DataFrame({
        "item": raw.iloc[:, 0].map(_clean_str),
        "supplier_short": raw.iloc[:, 7].map(_clean_str).map(resolve_company_name),
        "po_code": raw.iloc[:, 8].map(_clean_str).str.replace("Purchase Order #", "", regex=False).str.strip(),
        "invoice_date": raw.iloc[:, 11].map(_parse_date),
        "quantity": raw.iloc[:, 12],
        "total_money": raw.iloc[:, 17].astype(int),
    })

    return df[df["supplier_short"] == seller_short].reset_index(drop=True)


def parse_sell_file(filepath: str, buyer_short: str) -> pd.DataFrame:
    """Parse and clean the Sell Excel file. Filter to rows where customer matches buyer_short."""
    raw = pd.read_excel(filepath, header=0)

    df = pd.DataFrame({
        "item": raw.iloc[:, 8].map(_clean_str),
        "customer_short": raw.iloc[:, 25].map(_clean_str).map(resolve_company_name),
        "seller_short": raw.iloc[:, 1].map(_clean_str).map(resolve_company_name),
        "so_code": raw.iloc[:, 30].map(_clean_str).str.replace("Sales Order #", "", regex=False).str.strip(),
        "invoice_date": raw.iloc[:, 5].map(_parse_date),
        "quantity": raw.iloc[:, 13],
        "total_money": raw.iloc[:, 17].astype(int),
    })

    return df[df["customer_short"] == buyer_short].reset_index(drop=True)


def filter_by_period(df: pd.DataFrame, start_date: date, end_date: date) -> pd.DataFrame:
    """Filter DataFrame to rows within the reporting period based on invoice_date column."""
    mask = df["invoice_date"].map(lambda d: d is not None and start_date <= d <= end_date)
    return df[mask].reset_index(drop=True)
