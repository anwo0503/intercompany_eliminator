from __future__ import annotations

import os
from datetime import date

import pandas as pd
from PySide6.QtCore import (
    QAbstractTableModel,
    QDate,
    QModelIndex,
    QObject,
    Qt,
    QThread,
    Signal,
    Slot,
)
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDateEdit,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from engine.mapping import get_valid_pairs
from engine.matcher import match_transactions
from engine.parser import filter_by_period, parse_buy_file, parse_sell_file
from engine.result_builder import build_result_table, export_to_excel


_LABEL_MISMATCH = "--- AMOUNT MISMATCHES ---"
_LABEL_UNMATCHED = "--- UNMATCHED TRANSACTIONS ---"
_SEPARATOR_LABELS = {_LABEL_MISMATCH, _LABEL_UNMATCHED}

_COLOR_MISMATCH = QColor("#FFFACD")
_COLOR_UNMATCHED = QColor("#FFE4E4")
_COLOR_SEPARATOR = QColor("#D9D9D9")


class ResultTableModel(QAbstractTableModel):
    """Table model wrapping a result DataFrame with section-aware row coloring."""

    def __init__(self, df: pd.DataFrame, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._df = df.reset_index(drop=True)
        self._row_sections: list[str] = self._compute_sections()

    def _compute_sections(self) -> list[str]:
        sections: list[str] = []
        current = "exact"
        for i in range(len(self._df)):
            val = self._df.iloc[i, 0]
            if isinstance(val, str) and val in _SEPARATOR_LABELS:
                sections.append("separator")
                if val == _LABEL_MISMATCH:
                    current = "mismatch"
                elif val == _LABEL_UNMATCHED:
                    current = "unmatched"
            else:
                sections.append(current)
        return sections

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._df)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._df.columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        if not index.isValid():
            return None
        row, col = index.row(), index.column()

        if role == Qt.DisplayRole:
            val = self._df.iloc[row, col]
            if val is None:
                return ""
            try:
                if pd.isna(val):
                    return ""
            except (TypeError, ValueError):
                pass
            if isinstance(val, date):
                return val.strftime("%d/%m/%Y")
            return str(val)

        if role == Qt.BackgroundRole:
            sec = self._row_sections[row]
            if sec == "separator":
                return _COLOR_SEPARATOR
            if sec == "mismatch":
                return _COLOR_MISMATCH
            if sec == "unmatched":
                return _COLOR_UNMATCHED
            return None

        if role == Qt.TextAlignmentRole:
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return str(self._df.columns[section])
        return str(section + 1)

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        self.layoutAboutToBeChanged.emit()
        self._df = self._sort_within_sections(column, order)
        self._row_sections = self._compute_sections()
        self.layoutChanged.emit()

    def _sort_within_sections(self, column: int, order: Qt.SortOrder) -> pd.DataFrame:
        """Sort each section independently, keeping separator rows anchored."""
        df = self._df
        col_name = df.columns[column]
        ascending = order == Qt.AscendingOrder

        label_indices = [
            i for i in range(len(df))
            if isinstance(df.iloc[i, 0], str) and df.iloc[i, 0] in _SEPARATOR_LABELS
        ]

        if not label_indices:
            return df.sort_values(col_name, ascending=ascending, na_position="last").reset_index(drop=True)

        def _sorted_section(sub: pd.DataFrame) -> pd.DataFrame:
            try:
                return sub.sort_values(col_name, ascending=ascending, na_position="last")
            except Exception:
                return sub

        parts: list[pd.DataFrame] = []
        prev_end = 0
        for label_idx in label_indices:
            # blank row immediately precedes the label row
            sep_start = max(prev_end, label_idx - 1)
            if sep_start > prev_end:
                parts.append(_sorted_section(df.iloc[prev_end:sep_start].copy()))
            parts.append(df.iloc[sep_start: label_idx + 1])
            prev_end = label_idx + 1

        if prev_end < len(df):
            parts.append(_sorted_section(df.iloc[prev_end:].copy()))

        return pd.concat(parts, ignore_index=True)


class _MatchWorker(QThread):
    """Runs the match pipeline in a background thread."""

    finished = Signal(object)
    error = Signal(str)

    def __init__(
        self,
        buy_path: str,
        sell_path: str,
        buyer: str,
        seller: str,
        start: date,
        end: date,
    ) -> None:
        super().__init__()
        self._buy_path = buy_path
        self._sell_path = sell_path
        self._buyer = buyer
        self._seller = seller
        self._start = start
        self._end = end

    def run(self) -> None:
        try:
            buy_df = parse_buy_file(self._buy_path, self._seller)
            sell_df = parse_sell_file(self._sell_path, self._buyer)
            buy_df = filter_by_period(buy_df, self._start, self._end)
            sell_df = filter_by_period(sell_df, self._start, self._end)
            result = match_transactions(buy_df, sell_df)
            result_df = build_result_table(result, self._buyer, self._seller)
            self.finished.emit(result_df)
        except Exception as exc:
            self.error.emit(str(exc))


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("ICE — InterCompany Eliminator")
        self.setMinimumSize(1000, 700)

        self._buy_path: str | None = None
        self._sell_path: str | None = None
        self._result_df: pd.DataFrame | None = None
        self._worker: _MatchWorker | None = None

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(8)
        root.setContentsMargins(12, 12, 12, 12)

        root.addWidget(self._build_import_section())
        root.addWidget(self._build_options_section())
        root.addWidget(self._build_run_button())
        root.addWidget(self._build_results_section(), stretch=1)
        root.addWidget(self._build_export_button())

        self._update_run_button()

    def _build_import_section(self) -> QGroupBox:
        box = QGroupBox("File Import")
        layout = QVBoxLayout(box)

        buy_row = QHBoxLayout()
        self._btn_buy = QPushButton("Import Buy File")
        self._lbl_buy = QLabel("No file selected")
        self._btn_buy.setFixedWidth(140)
        self._btn_buy.clicked.connect(self._import_buy)
        buy_row.addWidget(self._btn_buy)
        buy_row.addWidget(self._lbl_buy, stretch=1)
        layout.addLayout(buy_row)

        sell_row = QHBoxLayout()
        self._btn_sell = QPushButton("Import Sell File")
        self._lbl_sell = QLabel("No file selected")
        self._btn_sell.setFixedWidth(140)
        self._btn_sell.clicked.connect(self._import_sell)
        sell_row.addWidget(self._btn_sell)
        sell_row.addWidget(self._lbl_sell, stretch=1)
        layout.addLayout(sell_row)

        return box

    def _build_options_section(self) -> QGroupBox:
        box = QGroupBox("Options")
        layout = QHBoxLayout(box)

        layout.addWidget(QLabel("Buyer-Seller Pair:"))
        self._combo_pair = QComboBox()
        for buyer, seller in get_valid_pairs():
            self._combo_pair.addItem(f"{buyer} ↔ {seller}", (buyer, seller))
        self._combo_pair.currentIndexChanged.connect(self._update_run_button)
        layout.addWidget(self._combo_pair)

        layout.addSpacing(24)
        layout.addWidget(QLabel("Start Date:"))
        self._date_start = QDateEdit()
        self._date_start.setDisplayFormat("dd/MM/yyyy")
        self._date_start.setCalendarPopup(True)
        today = QDate.currentDate()
        self._date_start.setDate(QDate(today.year(), today.month(), 1))
        layout.addWidget(self._date_start)

        layout.addSpacing(12)
        layout.addWidget(QLabel("End Date:"))
        self._date_end = QDateEdit()
        self._date_end.setDisplayFormat("dd/MM/yyyy")
        self._date_end.setCalendarPopup(True)
        self._date_end.setDate(today)
        layout.addWidget(self._date_end)

        layout.addStretch()
        return box

    def _build_run_button(self) -> QPushButton:
        self._btn_run = QPushButton("Run Matching")
        self._btn_run.setFixedHeight(40)
        self._btn_run.clicked.connect(self._run_matching)
        return self._btn_run

    def _build_results_section(self) -> QGroupBox:
        box = QGroupBox("Results")
        layout = QVBoxLayout(box)
        self._table = QTableView()
        self._table.setSortingEnabled(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.setAlternatingRowColors(False)
        self._table.setSelectionBehavior(QTableView.SelectRows)
        layout.addWidget(self._table)
        return box

    def _build_export_button(self) -> QPushButton:
        self._btn_export = QPushButton("Export to Excel")
        self._btn_export.setFixedHeight(36)
        self._btn_export.setEnabled(False)
        self._btn_export.clicked.connect(self._export)
        return self._btn_export

    def _import_buy(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Buy File", "", "Excel Files (*.xlsx)"
        )
        if path:
            self._buy_path = path
            self._lbl_buy.setText(os.path.basename(path))
            self._update_run_button()

    def _import_sell(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Open Sell File", "", "Excel Files (*.xlsx)"
        )
        if path:
            self._sell_path = path
            self._lbl_sell.setText(os.path.basename(path))
            self._update_run_button()

    def _update_run_button(self) -> None:
        self._btn_run.setEnabled(
            self._buy_path is not None
            and self._sell_path is not None
            and self._combo_pair.currentIndex() >= 0
        )

    def _run_matching(self) -> None:
        buyer, seller = self._combo_pair.currentData()
        start = self._date_start.date().toPython()
        end = self._date_end.date().toPython()

        self._btn_run.setEnabled(False)
        self._btn_run.setText("Running…")
        QApplication.setOverrideCursor(Qt.WaitCursor)

        self._worker = _MatchWorker(
            self._buy_path, self._sell_path, buyer, seller, start, end
        )
        self._worker.finished.connect(self._on_match_done)
        self._worker.error.connect(self._on_match_error)
        self._worker.start()

    @Slot(object)
    def _on_match_done(self, result_df: pd.DataFrame) -> None:
        QApplication.restoreOverrideCursor()
        self._result_df = result_df
        model = ResultTableModel(result_df)
        self._table.setModel(model)
        self._table.resizeColumnsToContents()
        self._btn_export.setEnabled(True)
        self._btn_run.setText("Run Matching")
        self._update_run_button()

    @Slot(str)
    def _on_match_error(self, message: str) -> None:
        QApplication.restoreOverrideCursor()
        self._btn_run.setText("Run Matching")
        self._update_run_button()
        QMessageBox.critical(self, "Processing Error", message)

    def _export(self) -> None:
        if self._result_df is None:
            return
        buyer, seller = self._combo_pair.currentData()
        today_str = date.today().strftime("%Y%m%d")
        default_name = f"ICE_Result_{buyer}_{seller}_{today_str}.xlsx"

        path, _ = QFileDialog.getSaveFileName(
            self, "Export to Excel", default_name, "Excel Files (*.xlsx)"
        )
        if not path:
            return
        try:
            export_to_excel(self._result_df, path)
            QMessageBox.information(self, "Export Complete", f"Saved to:\n{path}")
        except Exception as exc:
            QMessageBox.critical(self, "Export Error", str(exc))
