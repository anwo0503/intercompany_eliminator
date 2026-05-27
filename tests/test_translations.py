from __future__ import annotations

import pytest

from engine.translations import _TRANSLATIONS, set_language, t


def test_vi_col_buyer() -> None:
    set_language("vi")
    assert t("col_buyer") == "Bên mua"


def test_en_col_buyer() -> None:
    set_language("en")
    assert t("col_buyer") == "Buyer Side"


def test_all_keys_present_in_both_languages() -> None:
    vi_keys = set(_TRANSLATIONS["vi"].keys())
    en_keys = set(_TRANSLATIONS["en"].keys())
    assert vi_keys == en_keys, (
        f"Key mismatch — only in vi: {vi_keys - en_keys}, only in en: {en_keys - vi_keys}"
    )


def test_no_key_error_for_any_key() -> None:
    for lang in ("vi", "en"):
        set_language(lang)
        for key in _TRANSLATIONS[lang]:
            t(key)  # must not raise KeyError


def test_language_switching() -> None:
    set_language("vi")
    assert t("col_buyer") == "Bên mua"
    set_language("en")
    assert t("col_buyer") == "Buyer Side"
    set_language("vi")
    assert t("col_buyer") == "Bên mua"


def test_invalid_language_raises() -> None:
    with pytest.raises(ValueError):
        set_language("fr")


def test_separator_labels() -> None:
    set_language("vi")
    assert t("separator_mismatch") == "--- CHÊNH LỆCH SỐ TIỀN ---"
    assert t("separator_unmatched") == "--- GIAO DỊCH KHÔNG KHỚP ---"
    set_language("en")
    assert t("separator_mismatch") == "--- AMOUNT MISMATCHES ---"
    assert t("separator_unmatched") == "--- UNMATCHED TRANSACTIONS ---"


def test_subtotal_label() -> None:
    set_language("vi")
    assert t("subtotal") == "Tổng cộng"
    set_language("en")
    assert t("subtotal") == "Subtotal"


def test_export_filename_format() -> None:
    set_language("vi")
    name = t("export_filename").format(buyer="A", seller="B", date="20240101")
    assert name == "ICE_Ketqua_A_B_20240101.xlsx"
    set_language("en")
    name = t("export_filename").format(buyer="A", seller="B", date="20240101")
    assert name == "ICE_Result_A_B_20240101.xlsx"
