from __future__ import annotations

from dataclasses import dataclass
from datetime import date

import pandas as pd


AMOUNT_TOLERANCE = 10


@dataclass
class MatchResult:
    exact_matches: pd.DataFrame
    amount_mismatches: pd.DataFrame
    unmatched_buy: pd.DataFrame
    unmatched_sell: pd.DataFrame


def _aggregate_buy(buy_df: pd.DataFrame) -> pd.DataFrame:
    df = buy_df.copy()
    df["_key"] = df["item"] + "|" + df["po_code"]
    return (
        df.groupby("_key", sort=False)
        .agg(
            item=("item", "first"),
            po_code=("po_code", "first"),
            invoice_date=("invoice_date", lambda s: min((d for d in s if d is not None), default=None)),
            quantity=("quantity", "sum"),
            total_money=("total_money", "sum"),
        )
        .reset_index(drop=True)
    )


def _aggregate_sell(sell_df: pd.DataFrame) -> pd.DataFrame:
    df = sell_df.copy()
    df["_key"] = df["item"] + "|" + df["so_code"]
    return (
        df.groupby("_key", sort=False)
        .agg(
            item=("item", "first"),
            so_code=("so_code", "first"),
            invoice_date=("invoice_date", lambda s: min((d for d in s if d is not None), default=None)),
            quantity=("quantity", "sum"),
            total_money=("total_money", "sum"),
        )
        .reset_index(drop=True)
    )


def _date_diff(d1: date | None, d2: date | None) -> int:
    if d1 is None or d2 is None:
        return 999_999
    return abs((d1 - d2).days)


def _pick_best(sell_df: pd.DataFrame, candidates: list[int], buy_date: date | None) -> int:
    if len(candidates) == 1:
        return candidates[0]
    exact = [i for i in candidates if sell_df.at[i, "invoice_date"] == buy_date]
    if exact:
        return exact[0]
    return min(candidates, key=lambda i: _date_diff(sell_df.at[i, "invoice_date"], buy_date))


_MATCH_COLS = [
    "buy_item", "buy_po_code", "buy_invoice_date", "buy_quantity", "buy_total_money",
    "sell_item", "sell_so_code", "sell_invoice_date", "sell_quantity", "sell_total_money",
]
_BUY_COLS = ["item", "po_code", "invoice_date", "quantity", "total_money"]
_SELL_COLS = ["item", "so_code", "invoice_date", "quantity", "total_money"]


def match_transactions(
    buy_df: pd.DataFrame,
    sell_df: pd.DataFrame,
    tolerance: int = AMOUNT_TOLERANCE,
) -> MatchResult:
    """Run the matching algorithm on cleaned Buy and Sell data. Returns categorized results."""
    list1 = _aggregate_buy(buy_df)
    list2 = _aggregate_sell(sell_df)

    claimed: set[int] = set()
    exact_pairs: list[dict] = []
    mismatch_pairs: list[dict] = []
    unmatched_buy_rows: list[dict] = []

    for _, buy_row in list1.iterrows():
        unclaimed = ~list2.index.isin(claimed)

        # Phase 1: exact (total_money, quantity) match
        exact_mask = (
            unclaimed
            & (list2["total_money"] == buy_row["total_money"])
            & (list2["quantity"] == buy_row["quantity"])
        )
        exact_candidates = list2.index[exact_mask].tolist()

        if exact_candidates:
            best = _pick_best(list2, exact_candidates, buy_row["invoice_date"])
            claimed.add(best)
            sell_row = list2.loc[best]
            exact_pairs.append({
                "buy_item": buy_row["item"],
                "buy_po_code": buy_row["po_code"],
                "buy_invoice_date": buy_row["invoice_date"],
                "buy_quantity": buy_row["quantity"],
                "buy_total_money": buy_row["total_money"],
                "sell_item": sell_row["item"],
                "sell_so_code": sell_row["so_code"],
                "sell_invoice_date": sell_row["invoice_date"],
                "sell_quantity": sell_row["quantity"],
                "sell_total_money": sell_row["total_money"],
            })
            continue

        # Phase 2: quantity matches, money within tolerance (amount mismatch)
        mismatch_mask = (
            unclaimed
            & (list2["quantity"] == buy_row["quantity"])
            & ((list2["total_money"] - buy_row["total_money"]).abs() <= tolerance)
        )
        mismatch_candidates = list2.index[mismatch_mask].tolist()

        if mismatch_candidates:
            best = _pick_best(list2, mismatch_candidates, buy_row["invoice_date"])
            claimed.add(best)
            sell_row = list2.loc[best]
            mismatch_pairs.append({
                "buy_item": buy_row["item"],
                "buy_po_code": buy_row["po_code"],
                "buy_invoice_date": buy_row["invoice_date"],
                "buy_quantity": buy_row["quantity"],
                "buy_total_money": buy_row["total_money"],
                "sell_item": sell_row["item"],
                "sell_so_code": sell_row["so_code"],
                "sell_invoice_date": sell_row["invoice_date"],
                "sell_quantity": sell_row["quantity"],
                "sell_total_money": sell_row["total_money"],
            })
        else:
            unmatched_buy_rows.append(buy_row[_BUY_COLS].to_dict())

    unmatched_sell_rows = [list2.loc[i, _SELL_COLS].to_dict() for i in list2.index if i not in claimed]

    return MatchResult(
        exact_matches=pd.DataFrame(exact_pairs, columns=_MATCH_COLS) if exact_pairs else pd.DataFrame(columns=_MATCH_COLS),
        amount_mismatches=pd.DataFrame(mismatch_pairs, columns=_MATCH_COLS) if mismatch_pairs else pd.DataFrame(columns=_MATCH_COLS),
        unmatched_buy=pd.DataFrame(unmatched_buy_rows, columns=_BUY_COLS) if unmatched_buy_rows else pd.DataFrame(columns=_BUY_COLS),
        unmatched_sell=pd.DataFrame(unmatched_sell_rows, columns=_SELL_COLS) if unmatched_sell_rows else pd.DataFrame(columns=_SELL_COLS),
    )
