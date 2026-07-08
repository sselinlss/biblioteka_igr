from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFormLayout, QPushButton, QLineEdit, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QFileDialog, QComboBox, QSpinBox,
    QSplitter, QGroupBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QImage
from PIL import Image
import database
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Библиотека видеоигр")
        self.resize(1200, 700)
        self.setMinimumSize(900, 500)

        self.setStyleSheet("""QMainWindow {background-color: #8498d9;}""")

        self.db = database.DatabaseManager()
        self.db.init_db()
        logging.info("База данных инициализирована")

        self.current_id = None
        self.current_image_path = ""

        self._setup_ui()
        self._bind_signals()
        self._refresh_table()
        logging.info("Приложение запущено")

    def _get_image_path(self, path):
        if not path:
            return None

        if os.path.exists(path):
            return path

        project_dir = os.path.dirname(os.path.abspath(__file__))
        relative_path = os.path.join(project_dir, path)
        if os.path.exists(relative_path):
            return relative_path

        filename = os.path.basename(path)
        possible_path = os.path.join(project_dir, "assets", "posters", filename)
        if os.path.exists(possible_path):
            return possible_path

        possible_path2 = os.path.join(project_dir, "posters", filename)
        if os.path.exists(possible_path2):
            return possible_path2

        return None

    def _setup_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Фильтр по платформе:"))
        self.cb_filter = QComboBox()
        self.cb_filter.addItem("Все")
        self.cb_filter.addItems(["PC", "PS5", "Xbox", "Mobile"])
        filter_layout.addWidget(self.cb_filter)
        left_layout.addLayout(filter_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Постер", "Название", "Платформа", "Часы", "Статус", "Оценка"
        ])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.table.verticalHeader().setDefaultSectionSize(200)
        self.table.setColumnWidth(0, 140)

        left_layout.addWidget(self.table)

        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Добавить")
        self.btn_edit = QPushButton("Изменить")
        self.btn_delete = QPushButton("Удалить")
        self.btn_clear = QPushButton("Очистить поля")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_delete)
        btn_layout.addWidget(self.btn_clear)
        left_layout.addLayout(btn_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        form_group = QGroupBox("Информация об игре")
        form_layout = QFormLayout(form_group)

        self.le_title = QLineEdit()
        self.le_title.setPlaceholderText("Введите название")
        form_layout.addRow("Название:", self.le_title)

        self.cb_platform = QComboBox()
        self.cb_platform.addItems(["PC", "PS5", "Xbox", "Mobile"])
        form_layout.addRow("Платформа:", self.cb_platform)

        self.sb_hours = QSpinBox()
        self.sb_hours.setRange(0, 9999)
        self.sb_hours.setSuffix(" ч")
        form_layout.addRow("Часы игры:", self.sb_hours)

        self.cb_status = QComboBox()
        self.cb_status.addItems(["Не начата", "В процессе", "Пройдена"])
        form_layout.addRow("Статус:", self.cb_status)

        self.sb_rating = QSpinBox()
        self.sb_rating.setRange(0, 10)
        form_layout.addRow("Оценка (0-10):", self.sb_rating)

        right_layout.addWidget(form_group)

        poster_group = QGroupBox("Постер игры")
        poster_layout = QVBoxLayout(poster_group)

        self.lbl_poster = QLabel("Постер игры")
        self.lbl_poster.setAlignment(Qt.AlignCenter)
        self.lbl_poster.setMinimumHeight(250)
        self.lbl_poster.setStyleSheet(
            """background-color: #f0f0f0; border: 2px dashed #aaa; border-radius: 10px; font-size: 16px; color: #666;""")
        poster_layout.addWidget(self.lbl_poster)

        self.btn_load_poster = QPushButton("Загрузить постер")
        poster_layout.addWidget(self.btn_load_poster)
        right_layout.addWidget(poster_group)

        right_layout.addStretch()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([700, 350])
        main_layout.addWidget(splitter)

    def _bind_signals(self):
        self.btn_add.clicked.connect(self._on_add)
        self.btn_edit.clicked.connect(self._on_edit)
        self.btn_delete.clicked.connect(self._on_delete)
        self.btn_clear.clicked.connect(self._clear_fields)
        self.btn_load_poster.clicked.connect(self._on_load_poster)
        self.table.itemSelectionChanged.connect(self._on_select_row)
        self.cb_filter.currentTextChanged.connect(self._refresh_table)

    def _load_poster_from_path(self, path):
        try:
            real_path = self._get_image_path(path)

            if not real_path:
                logging.warning(f"Постер не найден: {path}")
                self.lbl_poster.setText("Постер не найден")
                self.lbl_poster.setStyleSheet(
                    """background-color: #f0f0f0; border: 2px solid #ff4444; border-radius: 10px; font-size: 16px; color: #666;""")
                return

            img = Image.open(real_path).convert("RGBA")
            img.thumbnail((200, 280), Image.LANCZOS)

            qt_img = QImage(
                img.tobytes(),
                img.width,
                img.height,
                QImage.Format_RGBA8888
            )
            pixmap = QPixmap.fromImage(qt_img)

            self.lbl_poster.setPixmap(pixmap)
            self.lbl_poster.setAlignment(Qt.AlignCenter)
            self.lbl_poster.setStyleSheet("border: 2px solid #4CAF50; border-radius: 10px;")
            logging.info(f"Постер загружен: {real_path}")

        except Exception as e:
            logging.error(f"Ошибка загрузки постера: {e}")
            self.lbl_poster.setText("Ошибка загрузки")
            self.lbl_poster.setStyleSheet(
                """ background-color: #f0f0f0; border: 2px solid #ff4444; border-radius: 10px; font-size: 16px; color: #666;""")

    def _on_select_row(self):
        try:
            selected = self.table.selectionModel().selectedRows()
            if not selected:
                return

            row = selected[0].row()

            id_item = self.table.item(row, 1)
            if id_item is None:
                logging.warning("Ячейка с ID пустая")
                return

            self.current_id = id_item.data(Qt.UserRole)
            if self.current_id is None:
                logging.warning("ID игры не найден")
                return

            title_item = self.table.item(row, 1)
            platform_item = self.table.item(row, 2)
            hours_item = self.table.item(row, 3)
            status_item = self.table.item(row, 4)
            rating_item = self.table.item(row, 5)

            if title_item:
                self.le_title.setText(title_item.text())
            if platform_item:
                self.cb_platform.setCurrentText(platform_item.text())
            if hours_item:
                self.sb_hours.setValue(int(hours_item.text() or 0))
            if status_item:
                self.cb_status.setCurrentText(status_item.text())
            if rating_item:
                self.sb_rating.setValue(int(rating_item.text() or 5))

            game = self.db.get_game_by_id(self.current_id)
            if game and game[6]:
                self._load_poster_from_path(game[6])
            else:
                self.lbl_poster.setText("Постер отсутствует")
                self.lbl_poster.setStyleSheet(
                    """background-color: #f0f0f0; border: 2px dashed #aaa; border-radius: 10px; font-size: 16px; color: #666;""")
        except Exception as e:
            logging.error(f"Ошибка при выборе строки: {e}")
            QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные:\n{e}")

    def _refresh_table(self):
        self.table.setRowCount(0)

        platform_filter = self.cb_filter.currentText()
        if platform_filter == "Все":
            platform_filter = None

        games = self.db.get_all_games(platform_filter)

        for i, game in enumerate(games):
            self.table.insertRow(i)

            image_path = game[6] if len(game) > 6 else None

            if image_path:
                real_path = self._get_image_path(image_path)
                if real_path and os.path.exists(real_path):
                    try:
                        img = Image.open(real_path).convert("RGBA")
                        img.thumbnail((130, 182), Image.LANCZOS)
                        qt_img = QImage(
                            img.tobytes(),
                            img.width,
                            img.height,
                            QImage.Format_RGBA8888
                        )
                        pixmap = QPixmap.fromImage(qt_img)

                        label = QLabel()
                        label.setPixmap(pixmap)
                        label.setAlignment(Qt.AlignCenter)
                        self.table.setCellWidget(i, 0, label)
                    except Exception as e:
                        logging.error(f"Ошибка загрузки мини-постера: {e}")
                else:
                    logging.warning(f"Файл не найден: {image_path}")
            else:
                logging.warning(f"Нет пути к постеру для игры {game[1]}")

            self.table.setItem(i, 1, QTableWidgetItem(game[1]))
            self.table.setItem(i, 2, QTableWidgetItem(game[2]))
            self.table.setItem(i, 3, QTableWidgetItem(str(game[3])))
            self.table.setItem(i, 4, QTableWidgetItem(game[4]))
            self.table.setItem(i, 5, QTableWidgetItem(str(game[5])))

            self.table.item(i, 1).setData(Qt.UserRole, game[0])

        self.table.setColumnWidth(0, 140)
        for col in range(1, 6):
            self.table.horizontalHeader().setSectionResizeMode(col, QHeaderView.Stretch)

    def _on_add(self):
        if not self.le_title.text().strip():
            logging.warning("Попытка добавить игру без названия")
            QMessageBox.warning(self, "Ошибка", "Название обязательно!")
            self.le_title.setFocus()
            return

        reply = QMessageBox.question(
            self,
            "Постер",
            "Хотите загрузить постер для этой игры?",
            QMessageBox.Yes | QMessageBox.No
        )

        poster_path = ''
        if reply == QMessageBox.Yes:
            path, _ = QFileDialog.getOpenFileName(
                self,
                "Выберите постер",
                "",
                "Images (*.png *.jpg *.jpeg *.bmp)"
            )
            if path:
                project_dir = os.path.dirname(os.path.abspath(__file__))
                poster_path = os.path.relpath(path, project_dir)
                logging.info(f"Выбран постер: {poster_path}")

        data = {
            "title": self.le_title.text().strip(),
            "platform": self.cb_platform.currentText(),
            "hours": self.sb_hours.value(),
            "status": self.cb_status.currentText(),
            "rating": self.sb_rating.value(),
            "image_path": poster_path
        }

        self.db.insert_game(data)
        self._refresh_table()
        self._clear_fields()
        logging.info(f"Игра добавлена: {data['title']}")
        QMessageBox.information(self, "Успех", "Игра добавлена!")

    def _on_edit(self):
        if not self.current_id:
            logging.warning("Попытка редактирования без выбранной игры")
            QMessageBox.warning(self, "Внимание", "Выберите игру!")
            return

        data = {
            "id": self.current_id,
            "title": self.le_title.text().strip(),
            "platform": self.cb_platform.currentText(),
            "hours": self.sb_hours.value(),
            "status": self.cb_status.currentText(),
            "rating": self.sb_rating.value(),
            "image_path": self.current_image_path
        }

        self.db.update_game(data)
        self._refresh_table()
        logging.info(f"Игра обновлена: {data['title']} (ID: {self.current_id})")
        QMessageBox.information(self, "Успех", "Игра обновлена!")

    def _on_delete(self):
        if not self.current_id:
            logging.warning("Попытка удаления без выбранной игры")
            QMessageBox.warning(self, "Внимание", "Выберите игру!")
            return

        reply = QMessageBox.question(
            self, "Подтверждение",
            "Удалить выбранную игру?",
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            game = self.db.get_game_by_id(self.current_id)
            title = game[1] if game else "Unknown"
            self.db.delete_game(self.current_id)
            self._refresh_table()
            self._clear_fields()
            logging.info(f"Игра удалена: {title} (ID: {self.current_id})")

    def _on_load_poster(self):
        if not self.current_id:
            logging.warning("Попытка загрузки постера без выбранной игры")
            QMessageBox.warning(self, "Внимание", "Сначала выберите игру в таблице!")
            return

        path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите постер",
            "",
            "Images (*.png *.jpg *.jpeg *.bmp)"
        )
        if not path:
            return

        try:
            project_dir = os.path.dirname(os.path.abspath(__file__))
            rel_path = os.path.relpath(path, project_dir)
            self.current_image_path = rel_path

            img = Image.open(path).convert("RGBA")
            img.thumbnail((200, 280), Image.LANCZOS)

            qt_img = QImage(
                img.tobytes(),
                img.width,
                img.height,
                QImage.Format_RGBA8888
            )
            pixmap = QPixmap.fromImage(qt_img)

            self.lbl_poster.setPixmap(pixmap)
            self.lbl_poster.setAlignment(Qt.AlignCenter)
            self.lbl_poster.setStyleSheet("border: 2px solid #4CAF50; border-radius: 10px;")

            self.db.update_game({
                'id': self.current_id,
                'title': self.le_title.text().strip(),
                'platform': self.cb_platform.currentText(),
                'hours': self.sb_hours.value(),
                'status': self.cb_status.currentText(),
                'rating': self.sb_rating.value(),
                'image_path': rel_path
            })
            self._refresh_table()
            logging.info(f"Постер загружен для игры ID {self.current_id}: {rel_path}")

        except Exception as e:
            logging.error(f"Ошибка загрузки постера: {e}")
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить:\n{e}")

    def _clear_fields(self):
        self.le_title.clear()
        self.cb_platform.setCurrentIndex(0)
        self.sb_hours.setValue(0)
        self.cb_status.setCurrentIndex(0)
        self.sb_rating.setValue(5)
        self.lbl_poster.setText("Постер игры")
        self.lbl_poster.setStyleSheet("""
            background-color: #f0f0f0;
            border: 2px dashed #aaa;
            border-radius: 10px;
            font-size: 16px;
            color: #666;
        """)
        self.current_image_path = ''
        self.current_id = None
        logging.info("Поля очищены")

    def closeEvent(self, event):
        reply = QMessageBox.question(
            self,
            "Выход",
            "Вы уверены, что хотите выйти?",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )

        if reply == QMessageBox.Yes:
            self.db.close()
            logging.info("Приложение закрыто")
            event.accept()
        else:
            event.ignore()
