# table_editor.py
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QWidget, QMessageBox
)
from PyQt5.QtCore import Qt
from typing import List, Any, Optional, Dict, Callable
from db_manager import DBManager

class RowEditorDialog(QDialog):
    """
    Диалог для добавления или редактирования строки таблицы.
    Проводится валидация данных в зависимости от типа столбца.
    """
    def __init__(
        self,
        parent: QWidget,
        db_manager: DBManager,
        table_name: str,
        columns_info: List[Any],
        mode: str = "add",
        rowid: Optional[int] = None,
        current_values: Optional[List[Any]] = None,
        refresh_callback: Optional[Callable[[], None]] = None
    ) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.table_name = table_name
        self.columns_info = columns_info  # список кортежей: (cid, name, type, notnull, dflt_value, pk)
        self.mode = mode
        self.rowid = rowid
        self.refresh_callback = refresh_callback
        self.setWindowTitle("Добавить строку" if mode == "add" else f"Редактировать строку {rowid}")
        self.inputs: Dict[str, QLineEdit] = {}
        self.init_ui(current_values)

    def init_ui(self, current_values: Optional[List[Any]]) -> None:
        layout = QVBoxLayout()
        # Для каждого столбца создаём поле ввода
        for i, col in enumerate(self.columns_info):
            col_name = col[1]
            col_type = (col[2] or "TEXT").upper()
            notnull = col[3]
            label = QLabel(f"{col_name} ({col_type})" + (" *" if notnull else ""))
            input_edit = QLineEdit()
            if self.mode == "edit" and current_values:
                value = current_values[i]
                if value is not None:
                    input_edit.setText(str(value))
            self.inputs[col_name] = input_edit
            row_layout = QHBoxLayout()
            row_layout.addWidget(label)
            row_layout.addWidget(input_edit)
            layout.addLayout(row_layout)
        btn_text = "Добавить" if self.mode == "add" else "Сохранить"
        btn_submit = QPushButton(btn_text)
        btn_submit.clicked.connect(self.on_submit)
        layout.addWidget(btn_submit)
        self.setLayout(layout)

    def on_submit(self) -> None:
        columns = []
        values = []
        # Валидация и преобразование данных
        for col in self.columns_info:
            col_name = col[1]
            col_type = (col[2] or "TEXT").upper()
            notnull = col[3]
            text = self.inputs[col_name].text().strip()
            if not text:
                if notnull:
                    QMessageBox.critical(self, "Ошибка", f"Поле '{col_name}' обязательно для заполнения!")
                    return
                else:
                    processed = None
            else:
                if col_type == "INTEGER":
                    try:
                        processed = int(text)
                    except ValueError:
                        QMessageBox.critical(self, "Ошибка", f"Поле '{col_name}' должно быть целым числом!")
                        return
                elif col_type == "REAL":
                    try:
                        processed = float(text)
                    except ValueError:
                        QMessageBox.critical(self, "Ошибка", f"Поле '{col_name}' должно быть числом с плавающей точкой!")
                        return
                else:
                    processed = text
            columns.append(col_name)
            values.append(processed)
        try:
            if self.mode == "add":
                self.db_manager.insert_row(self.table_name, columns, values)
                QMessageBox.information(self, "Успех", "Строка добавлена.")
            else:
                self.db_manager.update_row(self.table_name, columns, values, self.rowid)  # type: ignore
                QMessageBox.information(self, "Успех", "Строка обновлена.")
            if self.refresh_callback:
                self.refresh_callback()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

class TableEditorWindow(QDialog):
    """
    Окно для просмотра и редактирования данных таблицы.
    Отображает содержимое таблицы с возможностью добавления, редактирования и удаления строк.
    """
    def __init__(self, parent: QWidget, db_manager: DBManager, table_name: str) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.table_name = table_name
        self.setWindowTitle(f"Таблица: {table_name}")
        self.resize(600, 400)
        self.columns_info: List[Any] = self.db_manager.get_table_info(table_name)
        self.columns: List[str] = [col[1] for col in self.columns_info]
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout()
        self.table_widget = QTableWidget()
        layout.addWidget(self.table_widget)
        btn_layout = QHBoxLayout()
        btn_add = QPushButton("Добавить строку")
        btn_add.clicked.connect(self.add_row)
        btn_edit = QPushButton("Редактировать строку")
        btn_edit.clicked.connect(self.edit_row)
        btn_delete = QPushButton("Удалить строку")
        btn_delete.clicked.connect(self.delete_row)
        btn_layout.addWidget(btn_add)
        btn_layout.addWidget(btn_edit)
        btn_layout.addWidget(btn_delete)
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.refresh_table()

    def refresh_table(self) -> None:
        try:
            rows = self.db_manager.get_table_rows(self.table_name)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))
            return
        # Первая колонка – rowid, далее данные столбцов
        self.table_widget.clear()
        self.table_widget.setRowCount(len(rows))
        self.table_widget.setColumnCount(len(self.columns) + 1)
        headers = ["RowID"] + self.columns
        self.table_widget.setHorizontalHeaderLabels(headers)
        for row_idx, row_data in enumerate(rows):
            for col_idx, value in enumerate(row_data):
                item = QTableWidgetItem(str(value) if value is not None else "")
                self.table_widget.setItem(row_idx, col_idx, item)
        self.table_widget.resizeColumnsToContents()

    def add_row(self) -> None:
        dialog = RowEditorDialog(
            self, self.db_manager, self.table_name,
            self.columns_info, mode="add", refresh_callback=self.refresh_table
        )
        dialog.exec_()

    def edit_row(self) -> None:
        selected = self.table_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Внимание", "Не выбрана строка!")
            return
        rowid_item = self.table_widget.item(selected, 0)
        if rowid_item is None:
            return
        try:
            rowid = int(rowid_item.text())
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Неверный идентификатор строки.")
            return
        current_values = []
        for col in range(1, self.table_widget.columnCount()):
            item = self.table_widget.item(selected, col)
            current_values.append(item.text() if item is not None else "")
        dialog = RowEditorDialog(
            self, self.db_manager, self.table_name,
            self.columns_info, mode="edit", rowid=rowid,
            current_values=current_values, refresh_callback=self.refresh_table
        )
        dialog.exec_()

    def delete_row(self) -> None:
        selected = self.table_widget.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Внимание", "Не выбрана строка!")
            return
        rowid_item = self.table_widget.item(selected, 0)
        if rowid_item is None:
            return
        try:
            rowid = int(rowid_item.text())
        except ValueError:
            QMessageBox.critical(self, "Ошибка", "Неверный идентификатор строки.")
            return
        reply = QMessageBox.question(
            self, "Подтверждение", f"Удалить строку {rowid}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.db_manager.delete_row(self.table_name, rowid)
                QMessageBox.information(self, "Успех", "Строка удалена.")
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))
