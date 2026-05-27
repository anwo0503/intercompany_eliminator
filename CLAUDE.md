# CLAUDE.md — ICE (InterCompany Eliminator)

## Project Overview

ICE is a desktop application that automates intercompany transaction reconciliation for Aikya Corporation's subsidiaries. Users import Purchase and Sell Excel files from the ERP, select a buyer-seller pair and reporting period, and the program matches transactions, producing a three-part result table: exact matches, amount mismatches, and unmatched transactions.

**Tech stack:** Python 3.12+, PySide6 (GUI), pandas + openpyxl (data processing), PyInstaller (packaging)

## Repository Structure

```
ice/
├── main.py                  # Entry point — launches the GUI
├── requirements.txt
├── CLAUDE.md                # This file
├── README.md
├── engine/
│   ├── __init__.py
│   ├── mapping.py           # Company name mapping (hardcoded lookup)
│   ├── parser.py            # Data ingestion & cleaning
│   ├── matcher.py           # Matching engine
│   └── result_builder.py    # Result generation & Excel export
├── ui/
│   ├── __init__.py
│   └── main_window.py       # PySide6 GUI
└── tests/
    ├── __init__.py
    ├── test_mapping.py
    ├── test_parser.py
    ├── test_matcher.py
    └── test_result_builder.py
```

## Architecture Rules

### Separation of concerns

The `engine/` package contains all business logic. It has **zero GUI imports** — no PySide6, no Qt. The `ui/` package calls into `engine/` but never the reverse. This separation exists so that all business logic is testable via pytest without launching a GUI.

### Column positions, not header names

ERP exports have messy headers with trailing dots (e.g., `"Tên nhà Cung cấp....................................................."`). Always reference columns by position (iloc), never by header name.

**Buy file key columns (0-indexed):**
- 0: Item (product name)
- 7: Supplier name
- 8: PO code (strip "Purchase Order #" prefix)
- 11: Invoice date
- 12: Quantity
- 17: Total money

**Sell file key columns (0-indexed):**
- 1: Subsidiary (seller name)
- 5: Invoice date
- 8: Product name
- 13: Quantity  
- 17: Total money (after discount)
- 25: Customer name
- 30: SO code (strip "Sales Order #" prefix)

### Company name resolution

All company name fields (supplier, customer, subsidiary) must be resolved through `engine/mapping.py` before any matching logic runs. The mapping table is hardcoded. If `resolve_company_name()` returns `None`, the row is an external transaction and must be dropped.

### Matching algorithm invariants

1. **Match key:** (total_money, quantity) after aggregation by product+order key
2. **Date tiebreaker:** when multiple rows share the same (money, qty), pair by closest invoice date
3. **1-to-1 consumption:** once a sell-side row is claimed by a match, it cannot be claimed again
4. **Tolerance:** money differences ≤ 10 VND → "amount mismatch" (section 2). Beyond that → "unmatched" (section 3)
5. **Both-direction matching:** unmatched rows from both buy and sell sides must be captured

## Coding Standards

### Python

- Use type hints on all function signatures
- Use `from __future__ import annotations` in all modules
- Prefer dataclasses for structured data (e.g., MatchResult)
- Use `pandas` for tabular operations, never manual row-by-row loops where vectorized operations are possible
- All monetary values stay as integers (VND has no decimals)

### Testing

- Every engine module has a corresponding test file
- Tests use small, hand-crafted DataFrames — not the real ERP files
- Run tests with: `pytest tests/ -v`
- No GUI tests — the UI is tested manually by the user

### Git workflow

- Work on feature branches, never commit directly to `main`
- Branch naming: `issue-N-short-description` (e.g., `issue-2-company-mapping`)
- Each PR addresses one issue
- PR description must include: what changed, how to test it, which issue it closes
- All tests must pass before merging

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
python main.py

# Run tests
pytest tests/ -v

# Package for distribution (after all features are complete)
pyinstaller --onedir --windowed --name ICE main.py
```

## What Not to Do

- Do not use header names to select columns from ERP data
- Do not allow a sell-side row to be matched more than once
- Do not put business logic in the UI layer
- Do not hardcode file paths — all file paths come from user selection via the GUI
- Do not use floating point for money — VND amounts are always integers