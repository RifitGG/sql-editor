# app.py
import sys
from PyQt5.QtWidgets import (
    QMainWindow, QApplication, QWidget, QSplitter, QListWidget,
    QPlainTextEdit, QHBoxLayout, QVBoxLayout, QAction, QFileDialog,
    QMessageBox, QPushButton, QDialog, QLineEdit, QLabel
)
from PyQt5.QtCore import Qt
from db_manager import DBManager
from table_editor import TableEditorWindow

class MainWindow(QMainWindow):
    """
    Главное окно приложения SQLite DB Manager.
    """
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("SQLite DB Manager")
        self.resize(1000, 600)
        self.db_manager = DBManager()
        self.init_ui()
        self.apply_dark_theme()

    def init_ui(self) -> None:
        # Центральный виджет с разделителем на две панели
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        splitter = QSplitter(Qt.Horizontal)

        # Левая панель: список таблиц и кнопки управления
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        self.table_list = QListWidget()
        left_layout.addWidget(self.table_list)
        btn_add_table = QPushButton("Добавить таблицу")
        btn_add_table.clicked.connect(self.add_table)
        btn_view_edit = QPushButton("Просмотр/Редактирование")
        btn_view_edit.clicked.connect(self.view_edit_table)
        btn_delete_table = QPushButton("Удалить таблицу")
        btn_delete_table.clicked.connect(self.delete_table)
        left_layout.addWidget(btn_add_table)
        left_layout.addWidget(btn_view_edit)
        left_layout.addWidget(btn_delete_table)
        left_panel.setLayout(left_layout)

        # Правая панель: SQL редактор и область вывода
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        self.sql_editor = QPlainTextEdit()
        self.sql_editor.setPlaceholderText("Введите SQL запросы здесь...")
        right_layout.addWidget(self.sql_editor)
        btn_sql_run = QPushButton("Выполнить SQL")
        btn_sql_run.clicked.connect(self.run_sql)
        btn_sql_clear = QPushButton("Очистить SQL")
        btn_sql_clear.clicked.connect(self.clear_sql)
        btn_layout = QHBoxLayout()
        btn_layout.addWidget(btn_sql_run)
        btn_layout.addWidget(btn_sql_clear)
        right_layout.addLayout(btn_layout)
        self.output_editor = QPlainTextEdit()
        self.output_editor.setReadOnly(True)
        right_layout.addWidget(self.output_editor)
        right_panel.setLayout(right_layout)

        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(1, 3)

        main_layout = QHBoxLayout()
        main_layout.addWidget(splitter)
        central_widget.setLayout(main_layout)

        self.create_menu()
        self.refresh_table_list()

    def create_menu(self) -> None:
        menubar = self.menuBar()
        file_menu = menubar.addMenu("Файл")
        new_db_action = QAction("Новая база", self)
        new_db_action.triggered.connect(self.new_database)
        open_db_action = QAction("Открыть базу", self)
        open_db_action.triggered.connect(self.open_database)
        export_sql_action = QAction("Экспорт SQL", self)
        export_sql_action.triggered.connect(self.export_sql)
        exit_action = QAction("Выход", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(new_db_action)
        file_menu.addAction(open_db_action)
        file_menu.addAction(export_sql_action)
        file_menu.addSeparator()
        file_menu.addAction(exit_action)

        sql_menu = menubar.addMenu("SQL")
        run_sql_action = QAction("Выполнить SQL", self)
        run_sql_action.triggered.connect(self.run_sql)
        sql_menu.addAction(run_sql_action)

    def apply_dark_theme(self) -> None:
        # Простейший dark stylesheet
        dark_stylesheet = """
            QMainWindow { background-color: #2e2e2e; color: #ffffff; }
            QWidget { background-color: #2e2e2e; color: #ffffff; }
            QMenuBar { background-color: #3e3e3e; color: #ffffff; }
            QMenu { background-color: #3e3e3e; color: #ffffff; }
            QPushButton { background-color: #3e3e3e; color: #ffffff; }
            QLineEdit, QPlainTextEdit { background-color: #3e3e3e; color: #ffffff; }
            QListWidget { background-color: #3e3e3e; color: #ffffff; }
        """
        self.setStyleSheet(dark_stylesheet)

    def new_database(self) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, "Новая база данных", "", "SQLite Database (*.db);;Все файлы (*)"
        )
        if filename:
            try:
                self.db_manager.new_database(filename)
                QMessageBox.information(self, "База данных", f"Создана новая база: {filename}")
                self.refresh_table_list()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def open_database(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(
            self, "Открыть базу данных", "", "SQLite Database (*.db);;Все файлы (*)"
        )
        if filename:
            try:
                self.db_manager.open_database(filename)
                QMessageBox.information(self, "База данных", f"Открыта база: {filename}")
                self.refresh_table_list()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def export_sql(self) -> None:
        try:
            sql_dump = self.db_manager.export_sql()
            dlg = QDialog(self)
            dlg.setWindowTitle("SQL дамп")
            layout = QVBoxLayout()
            text_edit = QPlainTextEdit()
            text_edit.setPlainText(sql_dump)
            layout.addWidget(text_edit)
            btn_save = QPushButton("Сохранить в файл")
            btn_save.clicked.connect(lambda: self.save_dump(sql_dump))
            layout.addWidget(btn_save)
            dlg.setLayout(layout)
            dlg.resize(600, 400)
            dlg.exec_()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def save_dump(self, sql_dump: str) -> None:
        filename, _ = QFileDialog.getSaveFileName(
            self, "Сохранить SQL дамп", "", "SQL File (*.sql);;Все файлы (*)"
        )
        if filename:
            try:
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(sql_dump)
                QMessageBox.information(self, "Успех", f"Дамп сохранён в {filename}")
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

    def run_sql(self) -> None:
        sql = self.sql_editor.toPlainText().strip()
        if not sql:
            return
        try:
            self.db_manager.execute_script(sql)
            self.refresh_table_list()
            self.output_editor.setPlainText("SQL выполнен успешно.")
        except Exception as e:
            QMessageBox.critical(self, "SQL ошибка", str(e))

    def clear_sql(self) -> None:
        self.sql_editor.clear()

    def refresh_table_list(self) -> None:
        self.table_list.clear()
        try:
            tables = self.db_manager.get_tables()
            self.table_list.addItems(tables)
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

    def add_table(self) -> None:
        if not self.db_manager.conn:
            QMessageBox.warning(self, "Внимание", "База не открыта!")
            return
        dialog = AddTableDialog(self, self.db_manager, self.refresh_table_list)
        dialog.exec_()

    def view_edit_table(self) -> None:
        current_item = self.table_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Внимание", "Не выбрана таблица!")
            return
        table_name = current_item.text()
        editor = TableEditorWindow(self, self.db_manager, table_name)
        editor.exec_()

    def delete_table(self) -> None:
        current_item = self.table_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "Внимание", "Не выбрана таблица!")
            return
        table_name = current_item.text()
        reply = QMessageBox.question(
            self, "Подтверждение", f"Удалить таблицу {table_name}? Все данные будут потеряны.",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                self.db_manager.drop_table(table_name)
                QMessageBox.information(self, "Успех", f"Таблица {table_name} удалена.")
                self.refresh_table_list()
            except Exception as e:
                QMessageBox.critical(self, "Ошибка", str(e))

class AddTableDialog(QDialog):
    """
    Диалог для создания новой таблицы без необходимости знания SQL.
    Позволяет добавить произвольное количество столбцов с указанием имени, типа и PK.
    """
    def __init__(self, parent, db_manager: DBManager, refresh_callback) -> None:
        super().__init__(parent)
        self.db_manager = db_manager
        self.refresh_callback = refresh_callback
        self.setWindowTitle("Создание таблицы")
        self.columns = []  # список кортежей: (QLineEdit для имени, QComboBox для типа, QCheckBox для PK)
        self.init_ui()

    def init_ui(self) -> None:
        from PyQt5.QtWidgets import QComboBox, QCheckBox, QFormLayout
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        self.table_name_edit = QLineEdit()
        form_layout.addRow("Имя таблицы:", self.table_name_edit)
        layout.addLayout(form_layout)

        self.columns_layout = QVBoxLayout()
        layout.addLayout(self.columns_layout)
        btn_add_column = QPushButton("Добавить столбец")
        btn_add_column.clicked.connect(self.add_column_row)
        layout.addWidget(btn_add_column)
        btn_create = QPushButton("Создать таблицу")
        btn_create.clicked.connect(self.create_table)
        layout.addWidget(btn_create)
        self.setLayout(layout)
        self.add_column_row()  # добавляем первую строку

    def add_column_row(self) -> None:
        from PyQt5.QtWidgets import QComboBox, QCheckBox, QHBoxLayout, QLineEdit, QLabel
        row_widget = QWidget()
        row_layout = QHBoxLayout()
        row_widget.setLayout(row_layout)
        label = QLabel("Столбец:")
        row_layout.addWidget(label)
        name_edit = QLineEdit()
        row_layout.addWidget(name_edit)
        type_combo = QComboBox()
        type_combo.addItems(["INTEGER", "TEXT", "REAL", "BLOB"])
        row_layout.addWidget(type_combo)
        pk_checkbox = QCheckBox("PK")
        row_layout.addWidget(pk_checkbox)
        self.columns.append((name_edit, type_combo, pk_checkbox))
        self.columns_layout.addWidget(row_widget)

    def create_table(self) -> None:
        table_name = self.table_name_edit.text().strip()
        if not table_name:
            QMessageBox.warning(self, "Внимание", "Необходимо указать имя таблицы!")
            return
        col_defs = []
        for name_edit, type_combo, pk_checkbox in self.columns:
            col_name = name_edit.text().strip()
            if not col_name:
                continue
            col_type = type_combo.currentText()
            col_def = f"{col_name} {col_type}"
            if pk_checkbox.isChecked():
                col_def += " PRIMARY KEY"
            col_defs.append(col_def)
        if not col_defs:
            QMessageBox.warning(self, "Внимание", "Необходимо добавить хотя бы один столбец!")
            return
        sql = f"CREATE TABLE {table_name} ({', '.join(col_defs)});"
        try:
            cur = self.db_manager.conn.cursor()
            cur.execute(sql)
            self.db_manager.conn.commit()
            QMessageBox.information(self, "Успех", f"Таблица {table_name} создана.")
            self.refresh_callback()
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", str(e))

if __name__ == "__main__":
    # Для отладки модуля
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
