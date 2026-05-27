from __future__ import annotations

_MAPPING: dict[str, str] = {
    "aikya corporation : alpha lab": "ALab",
    "mbp_cty alpha lab": "ALab",
    "trade công ty tnhh alpha lab": "ALab",
    "cty tnhh alpha lab": "ALab",
    "lab": "ALab",
    "aikya corporation : alpha trade": "ATrade",
    "cty tnhh alpha trade": "ATrade",
    "công ty tnhh alpha trade": "ATrade",
    "mb_cty alpha trade": "ATrade",
    "sp công ty tnhh alpha trade": "ATrade",
    "lab alpha trade": "ATrade",
    "trade": "ATrade",
    "aikya corporation : aikya dược : mebiphar": "MBP",
    "công ty cổ phần dược phẩm và sinh học y tế": "MBP",
    "trade công ty cổ phần dược phẩm và sinh học y tế": "MBP",
    "sp công ty cổ phần dược phẩm và sinh học y tế": "MBP",
    "alab mebiphar": "MBP",
    "mbp": "MBP",
    "aikya corporation : aikya dược : s.pharm": "SP",
    "cty cổ phần dược s.pharm": "SP",
    "mb ct cp dược s.pharm": "SP",
    "trade cty cổ phần dược s. pharm": "SP",
    "sp": "SP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn an giang": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn bình dương": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn bình thuận": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn cà mau": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn cần thơ": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn gia lai": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn hcm 2": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn hà nội": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn hải dương": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn khánh hòa": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn nam định": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn nghệ an": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn phú thọ": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn quảng ngãi": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn thanh hóa": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn tiền giang": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn tp.hcm": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn trà vinh": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn vĩnh long": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn đà nẵng": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn đắk lắk": "TVP",
    "aikya corporation : aikya dược : tvpharm holding : tvpharm : cn đồng nai": "TVP",
    "mb dược tv.pharm": "TVP",
    "công ty cổ phần dược phẩm tv.pharm": "TVP",
    "trade công ty cổ phần dược phẩm tv.pharm": "TVP",
    "sp công ty cổ phần dược phẩm tv.pharm": "TVP",
    "tvp": "TVP",
}

_VALID_PAIRS: list[tuple[str, str]] = [
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


def resolve_company_name(name: str) -> str | None:
    """Look up a company name and return its short code (TVP, SP, MBP, ATrade, ALab).
    Returns None if the name is not an internal company (i.e., external supplier/customer).
    Matching is case-insensitive and strips leading/trailing whitespace.
    """
    return _MAPPING.get(name.strip().lower())


def get_valid_pairs() -> list[tuple[str, str]]:
    """Return all valid intercompany buyer-seller pairs for the UI dropdown.
    Each pair is (buyer_short_code, seller_short_code).
    """
    return list(_VALID_PAIRS)
