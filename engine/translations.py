from __future__ import annotations

_TRANSLATIONS: dict[str, dict[str, str]] = {
    "vi": {
        "window_title": "ICE — Đối chiếu giao dịch nội bộ",
        "import_buy": "Nhập file Mua",
        "import_sell": "Nhập file Bán",
        "no_file": "Chưa chọn file",
        "pair_label": "Cặp Mua-Bán:",
        "start_date": "Ngày bắt đầu:",
        "end_date": "Ngày kết thúc:",
        "run_button": "Chạy đối chiếu",
        "export_button": "Xuất ra Excel",
        "results_label": "Kết quả",
        "col_buyer": "Bên mua",
        "col_seller": "Bên bán",
        "col_date_buy": "Ngày HĐ — Bên mua",
        "col_date_sell": "Ngày HĐ — Bên bán",
        "col_item": "Mặt hàng",
        "col_quantity": "Số lượng",
        "col_money_buy": "Tiền — Bên mua",
        "col_money_sell": "Tiền — Bên bán",
        "col_difference": "Chênh lệch",
        "col_po": "Đơn hàng mua",
        "col_so": "Đơn hàng bán",
        "separator_mismatch": "--- CHÊNH LỆCH SỐ TIỀN ---",
        "separator_unmatched": "--- GIAO DỊCH KHÔNG KHỚP ---",
        "subtotal": "Tổng cộng",
        "export_filename": "ICE_Ketqua_{buyer}_{seller}_{date}.xlsx",
    },
    "en": {
        "window_title": "ICE — InterCompany Eliminator",
        "import_buy": "Import Buy File",
        "import_sell": "Import Sell File",
        "no_file": "No file selected",
        "pair_label": "Buyer-Seller Pair:",
        "start_date": "Start Date:",
        "end_date": "End Date:",
        "run_button": "Run Matching",
        "export_button": "Export to Excel",
        "results_label": "Results",
        "col_buyer": "Buyer Side",
        "col_seller": "Seller Side",
        "col_date_buy": "Invoice date — Buyer side",
        "col_date_sell": "Invoice date — Seller side",
        "col_item": "Item",
        "col_quantity": "Quantity",
        "col_money_buy": "Total money — Buyer side",
        "col_money_sell": "Total money — Seller side",
        "col_difference": "Difference",
        "col_po": "Purchase order",
        "col_so": "Sales order",
        "separator_mismatch": "--- AMOUNT MISMATCHES ---",
        "separator_unmatched": "--- UNMATCHED TRANSACTIONS ---",
        "subtotal": "Subtotal",
        "export_filename": "ICE_Result_{buyer}_{seller}_{date}.xlsx",
    },
}

# Maps internal (English) column names to translation keys
COL_KEY: dict[str, str] = {
    "Buyer Side": "col_buyer",
    "Seller Side": "col_seller",
    "Invoice date — Buyer side": "col_date_buy",
    "Invoice date — Seller side": "col_date_sell",
    "Item": "col_item",
    "Quantity": "col_quantity",
    "Total money — Buyer side": "col_money_buy",
    "Total money — Seller side": "col_money_sell",
    "Difference": "col_difference",
    "Purchase order": "col_po",
    "Sales order": "col_so",
}

# Maps internal (English) separator labels to translation keys
SEP_KEY: dict[str, str] = {
    "--- AMOUNT MISMATCHES ---": "separator_mismatch",
    "--- UNMATCHED TRANSACTIONS ---": "separator_unmatched",
}

_lang: str = "vi"


def set_language(lang: str) -> None:
    """Set language to 'vi' or 'en'."""
    global _lang
    if lang not in _TRANSLATIONS:
        raise ValueError(f"Unsupported language: {lang!r}")
    _lang = lang


def t(key: str) -> str:
    """Return the translated string for the current language setting."""
    return _TRANSLATIONS[_lang][key]
