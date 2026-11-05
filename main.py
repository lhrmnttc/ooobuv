import sys
import os
import uuid
import datetime

from PyQt6 import QtWidgets, uic, QtCore
from PyQt6.QtGui import QIcon, QPixmap, QFont
import psycopg  # psycopg3, pip install psycopg[binary]
import configparser
from pathlib import Path

# ---------- НАСТРОЙКИ БАЗЫ ДАННЫХ ----------

def get_connection():
    config = configparser.ConfigParser()

    config_path = Path(__file__).resolve().parent / "config.ini"

    if not config.read(config_path, encoding="utf-8"):
        raise FileNotFoundError("Файл config.ini не найден")

    db = config["database"]

    return psycopg.connect(
        dbname=db["name"],
        user=db["user"],
        password=db["password"],
        host=db["host"],
        port=db.getint("port")
    )


# ---------- РАБОТА С ПОЛЬЗОВАТЕЛЯМИ ----------
def get_user_by_credentials(login: str, password: str):
    """
    Получает пользователя по логину и паролю.
    Возвращает словарь:
    { id_user, fio, login, role }
    либо None.
    """
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id_user, fio, login, role
                FROM users
                WHERE login = %s AND password = %s
                """,
                (login, password),
            )
            row = cur.fetchone()

    if row is None:
        return None

    id_user, fio, login_db, role = row
    return {
        "id_user": id_user,
        "fio": fio,
        "login": login_db,
        "role": role,
    }

# ---------- ОКНО АВТОРИЗАЦИИ ----------
class AuthorizeWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("ui/authorize.ui", self)
        self.setFixedSize(self.size())
        self.setWindowIcon(QIcon("pics/icon.ico"))
        self.setWindowTitle("Авторизация")

        # Поля логина и пароля
        self.login_edit = getattr(self, "lineEdit_login", None)
        self.password_edit = getattr(self, "lineEdit_password", None)

        # Кнопки
        self.enterButton.clicked.connect(self.login_as_user)
        self.enterAsGuest.clicked.connect(self.login_as_guest)

    # --- вход как гость ---
    def login_as_guest(self):
        guest_user = {
            "id_user": None,
            "fio": "Гость",
            "login": None,
            "role": "guest",
        }
        self.open_products_window(guest_user)

    # --- вход по логину/паролю ---
    def login_as_user(self):
        # если вдруг поля не нашлись в ui
        if self.login_edit is None or self.password_edit is None:
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка формы",
                "Поля логина и пароля не найдены в форме авторизации.",
            )
            return

        login = self.login_edit.text().strip()
        password = self.password_edit.text().strip()

        # пустые поля
        if not login or not password:
            QtWidgets.QMessageBox.warning(
                self,
                "Ошибка ввода",
                "Логин и пароль не могут быть пустыми.",
            )
            return

        # обращаемся к БД с обработкой ошибок
        try:
            user = get_user_by_credentials(login, password)
        except psycopg.OperationalError:
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка подключения к БД",
                "Не удалось подключиться к базе данных.\n\n"
                "Проверьте:\n"
                "1. Запущен ли сервер PostgreSQL.\n"
                "2. Находится ли config.ini в той же папке с main.py.\n"
                "3. Доступность базы данных ООО «Обувь»."
            )
            return
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось выполнить запрос к базе данных:\n{e}",
            )
            return

        # пользователь не найден
        if user is None:
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка авторизации",
                "Неверный логин или пароль.",
            )
            return

        # успешный вход
        self.open_products_window(user)

    def open_products_window(self, user_info):
        self.products_window = ProductsWindow(current_user=user_info)
        self.products_window.show()
        self.close()


# ---------- ОКНО СПИСКА ТОВАРОВ ----------
class ProductsWindow(QtWidgets.QWidget):
    def __init__(self, current_user: dict):
        super().__init__()
        uic.loadUi("ui/spisokTovarov.ui", self)
        self.setFixedSize(self.size())
        self.setWindowIcon(QIcon("pics/icon.ico"))
        self.setWindowTitle("Список товаров 'ОООбувь'")

        self.current_user = current_user

        # Ссылки на виджеты фильтров / поиска / сортировки
        self.search_edit = getattr(self, "lineEdit_search", None)
        self.sort_combo = getattr(self, "comboBox_sort", None)
        self.suppliers_combo = getattr(self, "comboBox_suppliers", None)

        # Таймер для "отложенного" поиска (debounce)
        self.search_timer = QtCore.QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.setInterval(300)  # мс
        self.search_timer.timeout.connect(self.load_products)

        # Кнопки
        self.pushButton_back.clicked.connect(self.back_to_auth)
        self.pushButton_orders.clicked.connect(self.open_orders)
        self.pushButton_add_item.clicked.connect(self.open_add_product)

        # Права по ролям
        self.apply_role_permissions_products()
        self.init_filters_logic()

        # --- ScrollArea / карточки товаров ---
        self.item_template = getattr(self, "item_card", None)
        if self.item_template is not None:
            self.item_template.hide()

        self.products_layout = self.scrollAreaWidgetContents.layout()
        if self.products_layout is None:
            self.products_layout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)

        # Лейбл пользователя
        self.update_user_label()

        # Карта "карточка товара -> артикул", для клика/наведения
        self.card_articles: dict[QtWidgets.QFrame, str] = {}

        # Загрузка товаров + отрисовка карточек
        self.load_products()

    # ---- РОЛИ В СПИСКЕ ТОВАРОВ ----
    def apply_role_permissions_products(self):
        role = self.current_user.get("role")

        filter_widgets = [
            self.sort_combo,
            self.suppliers_combo,
            self.search_edit,
        ]

        def set_filters_visible(visible: bool):
            for w in filter_widgets:
                if w is not None:
                    w.setVisible(visible)

        if role in ("guest", "client"):
            self.pushButton_orders.setVisible(False)
            self.pushButton_add_item.setVisible(False)
            set_filters_visible(False)
        elif role == "manager":
            self.pushButton_orders.setVisible(True)
            self.pushButton_add_item.setVisible(False)
            set_filters_visible(True)
        elif role == "admin":
            self.pushButton_orders.setVisible(True)
            self.pushButton_add_item.setVisible(True)
            set_filters_visible(True)
        else:
            self.pushButton_orders.setVisible(False)
            self.pushButton_add_item.setVisible(False)
            set_filters_visible(False)

    def init_filters_logic(self):
        role = self.current_user.get("role")
        if role not in ("manager", "admin"):
            return

        # сортировка
        if self.sort_combo is not None:
            self.sort_combo.clear()
            self.sort_combo.addItem("Без сортировки", userData="none")
            self.sort_combo.addItem("По возрастанию", userData="amount_asc")
            self.sort_combo.addItem("По убыванию", userData="amount_desc")
            self.sort_combo.currentIndexChanged.connect(self.on_filters_changed)

        # фильтр по поставщику
        if self.suppliers_combo is not None:
            self.load_suppliers_for_filter()
            self.suppliers_combo.currentIndexChanged.connect(self.on_filters_changed)

        # поиск
        if self.search_edit is not None:
            self.search_edit.textChanged.connect(self.on_search_text_changed)

    def load_suppliers_for_filter(self):
        if self.suppliers_combo is None:
            return

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT DISTINCT supplier
                        FROM product
                        WHERE supplier IS NOT NULL AND supplier <> ''
                        ORDER BY supplier
                        """
                    )
                    rows = cur.fetchall()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка БД", str(e))
            return

        self.suppliers_combo.clear()
        self.suppliers_combo.addItem("Все поставщики", userData=None)

        for (supplier,) in rows:
            self.suppliers_combo.addItem(supplier, userData=supplier)

    def get_current_filters(self):
        search_text = ""
        if self.search_edit is not None:
            search_text = self.search_edit.text().strip()
            if search_text.lower() == "поиск":
                search_text = ""

        supplier_filter = None
        if self.suppliers_combo is not None and self.suppliers_combo.count() > 0:
            supplier_filter = self.suppliers_combo.currentData()

        sort_mode = "none"
        if self.sort_combo is not None and self.sort_combo.count() > 0:
            data = self.sort_combo.currentData()
            if isinstance(data, str) and data:
                sort_mode = data

        return search_text, supplier_filter, sort_mode

    def on_filters_changed(self, *_args):
        self.load_products()

    def on_search_text_changed(self, _text: str):
        role = self.current_user.get("role")
        if role not in ("manager", "admin"):
            return
        self.search_timer.start()

    def update_user_label(self):
        if not hasattr(self, "label_Uzver"):
            print("ВНИМАНИЕ: нет label_Uzver в spisokTovarov.ui")
            return

        role = self.current_user.get("role")
        fio = self.current_user.get("fio", "")

        if role == "guest":
            self.label_Uzver.setText("Гость")
        else:
            self.label_Uzver.setText(f"{fio}")

    # --- Работа с карточками товаров ---
    def clear_product_cards(self):
        if self.products_layout is None:
            return

        if hasattr(self, "card_articles"):
            self.card_articles.clear()

        while self.products_layout.count():
            item = self.products_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)
                widget.deleteLater()
            del item

    def create_product_card(
        self,
        article,
        name,
        uom,
        price,
        supplier,
        manufacturer,
        category,
        discount,
        amount,
        description,
        photo,
    ) -> QtWidgets.QFrame:
        discount = int(discount) if discount is not None else 0
        amount = int(amount) if amount is not None else 0

        card = QtWidgets.QFrame()
        card.setObjectName(f"product_card_{article}")
        card.setFont(QFont("Times New Roman"))

        base_stylesheet = ""
        if self.item_template is not None:
            card.setFrameShape(self.item_template.frameShape())
            card.setFrameShadow(self.item_template.frameShadow())
            base_stylesheet = self.item_template.styleSheet() or ""

        bg_style = ""
        if discount > 15:
            bg_style = "background-color: #2E8B57;"

        card.setStyleSheet(
            base_stylesheet + "font-family: 'Times New Roman'; " + bg_style
        )

        main_layout = QtWidgets.QHBoxLayout(card)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # ----- картинка -----
        picture_label = QtWidgets.QLabel()
        picture_label.setFixedSize(300, 200)
        picture_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        photo_path = photo or ""
        if not photo_path:
            photo_path = "pics/picture.png"

        pixmap = QPixmap(photo_path)
        if pixmap.isNull():
            pixmap = QPixmap("pics/picture.png")

        if not pixmap.isNull():
            pixmap = pixmap.scaled(
                300,
                200,
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            picture_label.setPixmap(pixmap)

        main_layout.addWidget(picture_label)

        # ----- правая текстовая часть -----
        info_layout = QtWidgets.QVBoxLayout()
        info_layout.setSpacing(6)

        header_layout = QtWidgets.QHBoxLayout()
        header_label = QtWidgets.QLabel(f"{category or '-'} | {name}")
        header_label.setStyleSheet("font-family: 'Times New Roman'; font-weight: bold;")
        header_layout.addWidget(header_label)
        info_layout.addLayout(header_layout)

        desc_label = QtWidgets.QLabel(f"Описание товара: {description or '-'}")
        desc_label.setWordWrap(True)
        info_layout.addWidget(desc_label)

        def make_row(caption: str, value: str, highlight=False):
            row_widget = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row_widget)
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(5)
            row_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

            cap = QtWidgets.QLabel(caption)
            val = QtWidgets.QLabel(value)

            row_layout.addWidget(cap)
            row_layout.addWidget(val)

            if highlight:
                row_widget.setStyleSheet("background-color: #ADD8E6;")

            return row_widget

        info_layout.addWidget(make_row("Производитель:", manufacturer or "-"))
        info_layout.addWidget(make_row("Поставщик:", supplier or "-"))

        # ----- Цена -----
        price_row = QtWidgets.QWidget()
        price_layout = QtWidgets.QHBoxLayout(price_row)
        price_layout.setContentsMargins(0, 0, 0, 0)
        price_layout.setSpacing(5)
        price_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        price_caption = QtWidgets.QLabel("Цена:")
        price_layout.addWidget(price_caption)

        price_value = float(price) if price is not None else 0.0
        price_str = f"{price_value:.2f}"

        if discount > 0:
            final_price = price_value * (100 - discount) / 100
            final_price_str = f"{final_price:.2f}"

            old_p = QtWidgets.QLabel(price_str)
            old_p.setStyleSheet(
                "font-family: 'Times New Roman'; color:red; text-decoration: line-through;"
            )
            new_p = QtWidgets.QLabel(final_price_str)

            price_layout.addWidget(old_p)
            price_layout.addWidget(new_p)
        else:
            price_layout.addWidget(QtWidgets.QLabel(price_str))

        info_layout.addWidget(price_row)

        info_layout.addWidget(make_row("Единица измерения:", uom or "-"))

        MANY_THRESHOLD = 5

        stock_text = "Много в наличии" if amount > MANY_THRESHOLD else "Мало в наличии"

        info_layout.addWidget(
            make_row("Количество на складе:", stock_text, highlight=(amount <= 0))
        )

        # КНОПКИ УДАЛЕНИЯ НА КАРТОЧКЕ БОЛЬШЕ НЕТ

        main_layout.addLayout(info_layout)

        # ----- правый блок скидки -----
        discount_frame = QtWidgets.QFrame()
        discount_frame.setFixedWidth(80)
        discount_frame.setStyleSheet("font-family: 'Times New Roman'; border: 0px;")

        discount_layout = QtWidgets.QVBoxLayout(discount_frame)
        discount_layout.setContentsMargins(0, 0, 0, 0)
        discount_layout.addStretch()

        discount_label_big = QtWidgets.QLabel(f"{discount}%" if discount > 0 else "")
        discount_label_big.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        discount_label_big.setStyleSheet(
            "font-size: 20px; font-weight: bold; color: black;"
        )

        discount_layout.addWidget(discount_label_big)
        discount_layout.addStretch()

        main_layout.addWidget(discount_frame)

        # сохраняем базовый стиль для возврата после ухода мыши
        card.setProperty("baseStylesheet", card.styleSheet())

        # регистрируем карточку в словаре и в eventFilter
        self.card_articles[card] = article
        card.installEventFilter(self)

        return card

    def eventFilter(self, obj, event):
        # Нас интересуют только карточки товаров
        if isinstance(obj, QtWidgets.QFrame) and obj in self.card_articles:
            et = event.type()

            if et == QtCore.QEvent.Type.Enter:
                base = obj.property("baseStylesheet")
                if base is None:
                    base = obj.styleSheet()
                    obj.setProperty("baseStylesheet", base)

                obj.setStyleSheet(base + " background-color: #00FA9A;")
                return True

            elif et == QtCore.QEvent.Type.Leave:
                base = obj.property("baseStylesheet") or ""
                obj.setStyleSheet(base)
                return True

            elif et == QtCore.QEvent.Type.MouseButtonPress:
                if event.button() == QtCore.Qt.MouseButton.LeftButton:
                    article = self.card_articles.get(obj)
                    if article:
                        self.on_product_card_clicked(article)
                    return True

        return super().eventFilter(obj, event)

    def on_product_card_clicked(self, article: str):
        role = self.current_user.get("role")
        if role == "admin":
            self.open_edit_product(article)

    def open_edit_product(self, article: str):
        self.add_product_window = AddTovarWindow(
            parent_window=self, product_article=article
        )
        self.add_product_window.show()
        self.hide()

    def load_products(self):
        self.clear_product_cards()

        search_text, supplier_filter, sort_mode = self.get_current_filters()

        query = """
            SELECT
                article,
                name,
                uom,
                price,
                supplier,
                manufacturer,
                category,
                discount,
                amount,
                description,
                photo
            FROM product
        """
        conditions = []
        params = []

        if search_text:
            words = [w.strip() for w in search_text.split() if w.strip()]

            for w in words:
                like = f"%{w}%"
                word_cond = (
                    "("
                    "LOWER(article)      LIKE LOWER(%s) OR "
                    "LOWER(name)         LIKE LOWER(%s) OR "
                    "LOWER(category)     LIKE LOWER(%s) OR "
                    "LOWER(manufacturer) LIKE LOWER(%s) OR "
                    "LOWER(supplier)     LIKE LOWER(%s) OR "
                    "LOWER(description)  LIKE LOWER(%s)"
                    ")"
                )
                conditions.append(word_cond)
                params.extend([like] * 6)

        if supplier_filter:
            conditions.append("supplier = %s")
            params.append(supplier_filter)

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        if sort_mode == "amount_asc":
            query += " ORDER BY amount ASC, name"
        elif sort_mode == "amount_desc":
            query += " ORDER BY amount DESC, name"
        else:
            query += " ORDER BY name"

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(query, params)
                    rows = cur.fetchall()
                    print("Товаров загружено:", len(rows))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка БД", str(e))
            return

        for row in rows:
            card = self.create_product_card(*row)
            self.products_layout.addWidget(card)

        self.products_layout.addStretch()

    # ---- навигация ----
    def back_to_auth(self):
        self.auth_window = AuthorizeWindow()
        self.auth_window.show()
        self.close()

    def open_orders(self):
        self.orders_window = OrdersWindow(current_user=self.current_user)
        self.orders_window.show()
        self.close()

    def open_add_product(self):
        self.add_product_window = AddTovarWindow(parent_window=self)
        self.add_product_window.show()
        self.hide()


# ---------- ОКНО СПИСКА ЗАКАЗОВ ----------
class OrdersWindow(QtWidgets.QWidget):
    def __init__(self, current_user: dict):
        super().__init__()
        uic.loadUi("ui/spisokZakazov.ui", self)
        self.setFixedSize(self.size())
        self.setWindowIcon(QIcon("pics/icon.ico"))
        self.setWindowTitle("Список заказов")

        self.current_user = current_user

        self.init_tests_button()

        self.pushButton_spisokTovarov.clicked.connect(self.open_products)
        self.pushButton_back.clicked.connect(self.back_to_auth)
        self.pushButton_addZakaz.clicked.connect(self.open_add_order)

        self.apply_role_permissions_orders()

        self.order_template = getattr(self, "order_card", None)
        if self.order_template is not None:
            self.order_template.hide()

        self.orders_layout = self.scrollAreaWidgetContents.layout()
        if self.orders_layout is None:
            self.orders_layout = QtWidgets.QVBoxLayout(self.scrollAreaWidgetContents)

        # словарь: карточка -> id_order (для клика/подсветки)
        self.card_orders: dict[QtWidgets.QFrame, int] = {}

        self.update_user_label()
        self.load_orders()

    def apply_role_permissions_orders(self):
        role = self.current_user.get("role")

        if role == "manager":
            self.pushButton_addZakaz.setVisible(False)
        elif role == "admin":
            self.pushButton_addZakaz.setVisible(True)
        else:
            self.pushButton_addZakaz.setVisible(False)

    def update_user_label(self):
        if not hasattr(self, "label_Uzver"):
            print("Нет label_Uzver в spisokZakazov.ui")
            return

        fio = self.current_user.get("fio", "")

        self.label_Uzver.setText(f"{fio}")

    def clear_order_cards(self):
        if self.orders_layout is None:
            return
        if hasattr(self, "card_orders"):
            self.card_orders.clear()

        for i in reversed(range(self.orders_layout.count())):
            item = self.orders_layout.itemAt(i)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def create_order_card(
        self,
        id_order,
        article,
        status,
        pvz_address,
        order_date,
        delivery_date,
    ) -> QtWidgets.QFrame:
        card = QtWidgets.QFrame()
        card.setObjectName(f"order_card_{id_order}")
        card.setFont(QFont("Times New Roman"))

        base_stylesheet = ""
        if self.order_template is not None:
            card.setFrameShape(self.order_template.frameShape())
            card.setFrameShadow(self.order_template.frameShadow())
            base_stylesheet = self.order_template.styleSheet() or ""

        card.setStyleSheet(base_stylesheet + "font-family: 'Times New Roman';")

        main_layout = QtWidgets.QHBoxLayout(card)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        info_layout = QtWidgets.QVBoxLayout()
        info_layout.setSpacing(6)

        def fmt_date(d):
            if d is None:
                return "-"
            try:
                return d.strftime("%d.%m.%Y")
            except AttributeError:
                return str(d)

        info_layout.addWidget(QtWidgets.QLabel(f"Артикул заказа: {article}"))
        info_layout.addWidget(QtWidgets.QLabel(f"Статус заказа: {status}"))
        info_layout.addWidget(QtWidgets.QLabel(f"Адрес пункта выдачи: {pvz_address}"))
        info_layout.addWidget(QtWidgets.QLabel(f"Дата заказа: {fmt_date(order_date)}"))

        # КНОПКИ УДАЛЕНИЯ ЗАКАЗА НА КАРТОЧКЕ БОЛЬШЕ НЕТ

        main_layout.addLayout(info_layout)

        date_frame = QtWidgets.QFrame()
        date_frame.setFixedWidth(140)
        date_frame.setStyleSheet("font-family: 'Times New Roman'; border: 0px;")

        date_layout = QtWidgets.QVBoxLayout(date_frame)
        date_layout.setContentsMargins(0, 0, 0, 0)
        date_layout.addStretch()

        date_label = QtWidgets.QLabel(fmt_date(delivery_date))
        date_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        date_label.setStyleSheet("font-size: 14px; font-weight: bold;")

        date_layout.addWidget(date_label)
        date_layout.addStretch()

        main_layout.addWidget(date_frame)

        card.setProperty("baseStylesheet", card.styleSheet())
        self.card_orders[card] = id_order
        card.installEventFilter(self)

        return card

    # --- hover и клик по карточке заказа ---
    def eventFilter(self, obj, event):
        if isinstance(obj, QtWidgets.QFrame) and obj in getattr(
            self, "card_orders", {}
        ):
            et = event.type()

            if et == QtCore.QEvent.Type.Enter:
                base = obj.property("baseStylesheet")
                if base is None:
                    base = obj.styleSheet()
                    obj.setProperty("baseStylesheet", base)
                obj.setStyleSheet(base + " background-color: #00FA9A;")
                return True

            elif et == QtCore.QEvent.Type.Leave:
                base = obj.property("baseStylesheet") or ""
                obj.setStyleSheet(base)
                return True

            elif et == QtCore.QEvent.Type.MouseButtonPress:
                if event.button() == QtCore.Qt.MouseButton.LeftButton:
                    order_id = self.card_orders.get(obj)
                    if order_id is not None:
                        self.on_order_card_clicked(order_id)
                    return True

        return super().eventFilter(obj, event)

    def on_order_card_clicked(self, order_id: int):
        role = self.current_user.get("role")
        if role == "admin":
            self.open_edit_order(order_id)

    def open_edit_order(self, order_id: int):
        self.add_order_window = AddZakazWindow(parent_window=self, order_id=order_id)
        self.add_order_window.show()
        self.hide()

    def load_orders(self):
        self.clear_order_cards()

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            o.id_order,
                            o.article,
                            o.status,
                            p.address,
                            o.order_date,
                            o.delivery_date
                        FROM orders o
                        JOIN pvz p ON o.id_pvz = p.id_pvz
                        ORDER BY o.order_date DESC
                        """
                    )
                    rows = cur.fetchall()
                    print("Заказов загружено:", len(rows))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка БД", str(e))
            return

        for row in rows:
            card = self.create_order_card(*row)
            self.orders_layout.addWidget(card)

        self.orders_layout.addStretch()

    def open_products(self):
        self.products_window = ProductsWindow(current_user=self.current_user)
        self.products_window.show()
        self.close()

    def back_to_auth(self):
        self.auth_window = AuthorizeWindow()
        self.auth_window.show()
        self.close()

    def open_add_order(self):
        self.add_order_window = AddZakazWindow(parent_window=self)
        self.add_order_window.show()
        self.hide()

    # Реализация кнопки
    def init_tests_button(self):
        if self.current_user.get("role") != "admin":
            return
        QtCore.QTimer.singleShot(0, self._init_test_button_orders)

    def _init_test_button_orders(self):
        try:
            self.pushButton_test = QtWidgets.QPushButton("Тест", self)
            self.pushButton_test.setObjectName("pushButton_test_orders")

            btn_w, btn_h = 160, 36
            x = self.width() - btn_w - 15
            y = self.height() - btn_h - 15
            self.pushButton_test.setGeometry(x, y, btn_w, btn_h)

            self.pushButton_test.setStyleSheet("""
                QPushButton {
                    background-color: #7fff00;
                    color: black;
                    font-family: 'Times New Roman';
                }
            """)

            self.pushButton_test.clicked.connect(self.open_tests_dialog_orders)
            self.pushButton_test.raise_()
            self.pushButton_test.show()

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Ошибка кнопки Тест", f"{type(e).__name__}: {e}"
            )

    # Реализация диалогового окна для выбора теста
    def open_tests_dialog_orders(self):
        msg = QtWidgets.QMessageBox(self)
        msg.setWindowTitle("Автотесты заказов")
        msg.setIcon(QtWidgets.QMessageBox.Icon.Question)
        msg.setText("Выберите автотест валидации данных при добавлении заказа:")

        btn1 = msg.addButton(
            "Тест 1: несуществующий артикул", QtWidgets.QMessageBox.ButtonRole.AcceptRole
        )
        btn2 = msg.addButton(
            "Тест 2: дата выдачи в прошлом", QtWidgets.QMessageBox.ButtonRole.AcceptRole
        )

        btn3 = msg.addButton(
            "Тест 3: добавление заказа", QtWidgets.QMessageBox.ButtonRole.AcceptRole
        )
        msg.addButton("Отмена", QtWidgets.QMessageBox.ButtonRole.RejectRole)

        msg.exec()

        clicked = msg.clickedButton()
        if clicked == btn1:
            self.test_order_nonexistent_article()
        elif clicked == btn2:
            self.test_order_delivery_date_in_past()
        elif clicked == btn3:
            self.test_order_positive_add()
        else:
            return

    def _pick_first_valid_pvz_index(self, w: "AddZakazWindow") -> int | None:
        for i in range(w.combo_pvz.count()):
            if w.combo_pvz.itemData(i) is not None:
                return i
        return None

    # Первый тест
    def test_order_nonexistent_article(self):
        from PyQt6.QtTest import QTest

        try:
            w = AddZakazWindow(parent_window=self)
            w.show()
            QTest.qWait(150)

            pvz_index = self._pick_first_valid_pvz_index(w)
            if pvz_index is None:
                w.close()
                QtWidgets.QMessageBox.warning(
                    self, "Невозможно запустить тест, нет доступных ПВЗ."
                )
                return
            w.combo_pvz.setCurrentIndex(pvz_index)

            w.edit_article.setText("A777TEST, 1")
            w.combo_status.setCurrentText("Новый")
            w.edit_order_date.setText("01.01.2026")
            w.edit_issue_date.setText("12.02.2026")
            w.edit_fio.setText("Иванов Петр Иванович")
            w.edit_code.setText("123")

            w.save_and_close()
            QTest.qWait(250)

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM orders WHERE article = 'Иванов Петр Иванович'")
                    row = cur.fetchone()

            if row is None:
                QtWidgets.QMessageBox.information(
                    self,
                    "Результат теста",
                    "Тест успешно пройден: Несуществующий артикул был отклонён, заказ в БД не создан.",
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Результат теста",
                    "Тест провален: Заказ с несуществующим артикулом сохранился в БД.",
                )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Автотест упал", f"{type(e).__name__}: {e}"
            )

    # Второй автотест
    def test_order_delivery_date_in_past(self):
        from PyQt6.QtTest import QTest

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT article FROM product ORDER BY id_product LIMIT 1")
                    r = cur.fetchone()

            if r is None:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Невозможно запустить тест",
                    "В БД нет товаров (таблица product пуста).",
                )
                return

            existing_article = r[0]

            w = AddZakazWindow(parent_window=self)
            w.show()
            QTest.qWait(150)

            w.edit_article.setText(f"{existing_article}, 1")
            w.combo_status.setCurrentText("Новый")

            pvz_index = self._pick_first_valid_pvz_index(w)
            if pvz_index is None:
                w.close()
                QtWidgets.QMessageBox.warning(
                    self, "Невозможно запустить тест", "В comboBox_pvz нет доступных ПВЗ."
                )
                return
            w.combo_pvz.setCurrentIndex(pvz_index)

            w.edit_order_date.setText("01.01.2026")
            w.edit_issue_date.setText("01.02.2026")
            w.edit_fio.setText("Иванов Иван Иванович")
            w.edit_code.setText("1234")

            w.save_and_close()
            QTest.qWait(250)

            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT 1 FROM orders WHERE client_fio = 'Иванов Иван Иванович'")
                    row = cur.fetchone()

            if row is None:
                QtWidgets.QMessageBox.information(
                    self,
                    "Результат теста",
                    "Тест успешно пройден: Дата выдачи в прошлом была отклонена, заказ в БД не создан.",
                )
            else:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Результат теста",
                    "Тест провален: Заказ с датой выдачи в прошлом сохранился в БД.",
                )

        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Автотест упал", f"{type(e).__name__}: {e}"
            )

    # Третий тест
    def test_order_positive_add(self):
        from PyQt6.QtTest import QTest

        # Выбор существующего товара, который есть на складе
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT article
                        FROM product
                        WHERE amount IS NOT NULL AND amount >= 1
                        ORDER BY id_product
                        LIMIT 1
                    """)
                    row = cur.fetchone()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка БД", str(e))
            return

        if row is None:
            QtWidgets.QMessageBox.warning(
                self,
                "Невозможно запустить тест",
                "Не найден товар с количеством на складе ≥ 1.",
            )
            return

        article = row[0]

        try:
            w = AddZakazWindow(parent_window=self)
            w.show()
            QTest.qWait(250)

            pvz_index = self._pick_first_valid_pvz_index(w)
            if pvz_index is None:
                w.close()
                QtWidgets.QMessageBox.warning(
                    self, "Невозможно запустить тест", "В comboBox_pvz нет доступных ПВЗ."
                )
                return

            w.combo_pvz.setCurrentIndex(pvz_index)
            w.edit_article.setText(f"{article}, 1")
            w.combo_status.setCurrentText("Новый")
            w.edit_order_date.setText("04.02.2026")
            w.edit_issue_date.setText("14.02.2026")
            w.edit_fio.setText("Иванов Александр Иванович")
            w.edit_code.setText("123")

            # Сохраняем заказ
            w.save_and_close()
            QTest.qWait(800)

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Автотест упал", f"{type(e).__name__}: {e}")
            return

        # Проверка в БД
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        SELECT id_order
                        FROM orders
                        WHERE client_fio = 'Иванов Александр Иванович'
                        ORDER BY id_order DESC
                        LIMIT 1
                    """)
                    row = cur.fetchone()

            if row is None:
                QtWidgets.QMessageBox.critical(
                    self,
                    "Результат теста",
                    "Тест не пройден: Заказ не найден в БД.",
                )
                return

            self.load_orders()

            QtWidgets.QMessageBox.information(
                self,
                "Результат теста",
                "Тест пройден: Заказ создан в БД",
            )

        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка БД", str(e))


# ---------- ОКНО ДОБАВЛЕНИЯ / РЕДАКТИРОВАНИЯ ТОВАРА ----------
class AddTovarWindow(QtWidgets.QWidget):
    PLACEHOLDER_PHOTO = "pics/picture.png"

    def __init__(self, parent_window, product_article: str | None = None):
        super().__init__()
        uic.loadUi("ui/addTovar.ui", self)
        self.setFixedSize(self.size())
        self.setWindowIcon(QIcon("pics/icon.ico"))

        self.parent_window = parent_window
        self.product_article = product_article  # None = добавление, not None = редактирование

        self.original_photo_path: str | None = None
        self.saved_photo_path: str | None = None

        # заголовок
        self.header_label: QtWidgets.QLabel = self.label
        if self.product_article is None:
            title_text = "Добавление товара"
        else:
            title_text = "Редактирование товара"
        self.setWindowTitle(title_text)
        self.header_label.setText(title_text)

        # поля формы
        self.edit_article = self.lineEdit_article
        self.edit_name = self.lineEdit_name
        self.combo_category = self.comboBox_category
        self.combo_producer = self.comboBox_producer
        self.edit_supplier = self.lineEdit_supplier
        self.edit_price = self.lineEdit_price
        self.edit_uom = self.lineEdit_uom
        self.edit_amount = self.lineEdit_amount
        self.edit_discount = self.lineEdit_discount
        self.edit_description = self.plainTextEdit_description
        self.label_photo_info = self.label_11

        # превью фото в label_11
        self.photo_preview = self.label_11
        self.photo_preview.setFixedSize(300, 200)
        self.photo_preview.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.photo_preview.setText("")

        # кнопка удаления товара (на форме)
        self.button_delete_item = self.pushButton_delete_item
        if self.product_article is None:
            # В режиме добавления скрываем кнопку
            self.button_delete_item.hide()
        else:
            # В режиме редактирования показываем
            self.button_delete_item.show()
            self.button_delete_item.clicked.connect(self.delete_current_product)

        self.combo_category.setEditable(True)
        self.combo_producer.setEditable(True)
        self.load_categories_and_producers()

        if self.product_article is not None:
            self.load_product_data(self.product_article)

        # показать заглушку / фото
        self.update_photo_preview()

        # кнопки
        self.pushButton_save.clicked.connect(self.save_and_close)
        self.pushButton_cancel.clicked.connect(self.cancel_and_close)
        self.pushButton_add_photo.clicked.connect(self.choose_photo)
        self.pushButton_delete_photo.clicked.connect(self.delete_photo)

    def update_photo_preview(self):
        if self.photo_preview is None:
            return

        if self.saved_photo_path and os.path.exists(self.saved_photo_path):
            path = self.saved_photo_path
        else:
            path = self.PLACEHOLDER_PHOTO

        pixmap = QPixmap(path)
        if pixmap.isNull():
            pixmap = QPixmap(self.PLACEHOLDER_PHOTO)

        pixmap = pixmap.scaled(
            300,
            200,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.photo_preview.setPixmap(pixmap)

    def load_categories_and_producers(self):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT DISTINCT category
                        FROM product
                        WHERE category IS NOT NULL AND category <> ''
                        ORDER BY category
                        """
                    )
                    categories = [r[0] for r in cur.fetchall()]

                    cur.execute(
                        """
                        SELECT DISTINCT manufacturer
                        FROM product
                        WHERE manufacturer IS NOT NULL AND manufacturer <> ''
                        ORDER BY manufacturer
                        """
                    )
                    producers = [r[0] for r in cur.fetchall()]
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка БД", str(e))
            return

        self.combo_category.clear()
        self.combo_category.addItem("")
        for c in categories:
            self.combo_category.addItem(c)

        self.combo_producer.clear()
        self.combo_producer.addItem("")
        for p in producers:
            self.combo_producer.addItem(p)

    def choose_photo(self):
        file_name, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Выбор фотографии товара",
            "",
            "Изображения (*.png *.jpg *.jpeg *.bmp)",
        )
        if not file_name:
            return

        pixmap = QPixmap(file_name)
        if pixmap.isNull():
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка загрузки изображения",
                "Не удалось загрузить выбранный файл. Убедитесь, что загружаемый файл является фотографией.",
            )
            return

        pixmap = pixmap.scaled(
            300,
            200,
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )

        pics_dir = "pics"
        os.makedirs(pics_dir, exist_ok=True)

        if (
            self.saved_photo_path
            and self.saved_photo_path != self.original_photo_path
            and os.path.exists(self.saved_photo_path)
        ):
            try:
                os.remove(self.saved_photo_path)
            except OSError:
                pass

        ext = os.path.splitext(file_name)[1].lower() or ".png"
        new_name = f"prod_{uuid.uuid4().hex}{ext}"
        new_path = os.path.join(pics_dir, new_name)

        if not pixmap.save(new_path):
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка сохранения",
                "Не удалось сохранить изображение в папку приложения.",
            )
            return

        self.saved_photo_path = new_path.replace("\\", "/")
        self.update_photo_preview()

    def delete_photo(self):
        if (
            self.saved_photo_path
            and self.saved_photo_path != self.original_photo_path
            and os.path.exists(self.saved_photo_path)
        ):
            try:
                os.remove(self.saved_photo_path)
            except OSError:
                pass

        self.saved_photo_path = None
        self.update_photo_preview()

    # --- удаление товара из формы редактирования ---
    def delete_current_product(self):
        if self.product_article is None:
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Удаление товара",
            f"Вы действительно хотите удалить товар с артикулом {self.product_article}?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        photo_path = None

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # получаем id_product и путь к фото
                    cur.execute(
                        "SELECT id_product, photo FROM product WHERE article = %s",
                        (self.product_article,),
                    )
                    row = cur.fetchone()
                    if row is None:
                        QtWidgets.QMessageBox.information(
                            self,
                            "Удаление товара",
                            "Товар с таким артикулом не найден в базе данных.",
                        )
                        return

                    id_product, photo_path = row

                    # проверяем, что товар не присутствует в заказах
                    cur.execute(
                        "SELECT 1 FROM order_items WHERE id_product = %s LIMIT 1",
                        (id_product,),
                    )
                    if cur.fetchone() is not None:
                        QtWidgets.QMessageBox.critical(
                            self,
                            "Удаление запрещено",
                            "Нельзя удалить товар, который присутствует в заказах.",
                        )
                        return

                    # удаляем товар
                    cur.execute(
                        "DELETE FROM product WHERE id_product = %s",
                        (id_product,),
                    )

                conn.commit()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось удалить товар:\n{e}",
            )
            return

        # удаляем файл фото
        if photo_path:
            normalized = photo_path.replace("\\", "/")
            if os.path.exists(normalized):
                try:
                    os.remove(normalized)
                except OSError:
                    pass

        QtWidgets.QMessageBox.information(
            self,
            "Удаление товара",
            "Товар успешно удалён.",
        )

        if self.parent_window is not None:
            self.parent_window.load_products()
            self.parent_window.show()

        self.close()

    def save_and_close(self):
        article = self.edit_article.text().strip()
        name = self.edit_name.text().strip()
        category = self.combo_category.currentText().strip() or None
        producer = self.combo_producer.currentText().strip() or None
        supplier = self.edit_supplier.text().strip() or None
        uom = self.edit_uom.text().strip() or None
        description = self.edit_description.toPlainText().strip() or None

        if not article:
            QtWidgets.QMessageBox.warning(
                self,
                "Некорректные данные",
                "Поле «Артикул» обязательно для заполнения.",
            )
            return

        if not name:
            QtWidgets.QMessageBox.warning(
                self,
                "Некорректные данные",
                "Поле «Наименование» обязательно для заполнения.",
            )
            return

        price_text = self.edit_price.text().strip().replace(",", ".")
        price = None
        if price_text:
            try:
                price = float(price_text)
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Некорректные данные",
                    "Поле «Цена» должно содержать число.",
                )
                return
            if price < 0:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Некорректные данные",
                    "Цена не может быть отрицательной.",
                )
                return

        amount_text = self.edit_amount.text().strip()
        amount = 0
        if amount_text:
            try:
                amount = int(amount_text)
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Некорректные данные",
                    "Поле «Кол-во на складе» должно содержать целое число.",
                )
                return
            if amount < 0:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Некорректные данные",
                    "Количество на складе не может быть отрицательным.",
                )
                return

        discount_text = self.edit_discount.text().strip()
        discount = 0
        if discount_text:
            try:
                discount = int(discount_text)
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Некорректные данные",
                    "Поле «Действующая скидка» должно содержать целое число.",
                )
                return
            if discount < 0 or discount > 100:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Некорректные данные",
                    "Скидка должна быть в диапазоне от 0 до 100%.",
                )
                return

        photo_db_path = self.saved_photo_path

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    if self.product_article is None:
                        cur.execute(
                            "SELECT 1 FROM product WHERE article = %s",
                            (article,),
                        )
                        if cur.fetchone() is not None:
                            QtWidgets.QMessageBox.warning(
                                self,
                                "Дублирование артикула",
                                "Товар с таким артикулом уже существует.",
                            )
                            return

                        cur.execute(
                            """
                            INSERT INTO product (
                                article,
                                name,
                                uom,
                                price,
                                supplier,
                                manufacturer,
                                category,
                                discount,
                                amount,
                                description,
                                photo
                            )
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """,
                            (
                                article,
                                name,
                                uom,
                                price,
                                supplier,
                                producer,
                                category,
                                discount,
                                amount,
                                description,
                                photo_db_path,
                            ),
                        )

                        QtWidgets.QMessageBox.information(
                            self,
                            "Товар добавлен",
                            "Новый товар успешно добавлен.",
                        )

                    else:
                        if article != self.product_article:
                            cur.execute(
                                "SELECT 1 FROM product WHERE article = %s",
                                (article,),
                            )
                            if cur.fetchone() is not None:
                                QtWidgets.QMessageBox.warning(
                                    self,
                                    "Дублирование артикула",
                                    "Товар с таким артикулом уже существует.",
                                )
                                return

                        cur.execute(
                            """
                            UPDATE product
                            SET
                                article = %s,
                                name = %s,
                                uom = %s,
                                price = %s,
                                supplier = %s,
                                manufacturer = %s,
                                category = %s,
                                discount = %s,
                                amount = %s,
                                description = %s,
                                photo = %s
                            WHERE article = %s
                            """,
                            (
                                article,
                                name,
                                uom,
                                price,
                                supplier,
                                producer,
                                category,
                                discount,
                                amount,
                                description,
                                photo_db_path,
                                self.product_article,
                            ),
                        )

                        if cur.rowcount == 0:
                            QtWidgets.QMessageBox.warning(
                                self,
                                "Товар не найден",
                                "Не удалось обновить товар (возможно, он был удалён).",
                            )
                            return

                        if (
                            self.original_photo_path
                            and self.original_photo_path != self.saved_photo_path
                            and os.path.exists(self.original_photo_path)
                        ):
                            try:
                                os.remove(self.original_photo_path)
                            except OSError:
                                pass

                        self.product_article = article
                        self.original_photo_path = self.saved_photo_path

                        QtWidgets.QMessageBox.information(
                            self,
                            "Товар обновлён",
                            "Данные товара успешно обновлены.",
                        )

                conn.commit()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось сохранить данные товара:\n{e}",
            )
            return

        if self.parent_window is not None:
            self.parent_window.load_products()
            self.parent_window.show()

        self.close()

    def cancel_and_close(self):
        if (
            self.saved_photo_path
            and self.saved_photo_path != self.original_photo_path
            and os.path.exists(self.saved_photo_path)
        ):
            try:
                os.remove(self.saved_photo_path)
            except OSError:
                pass

        if self.parent_window is not None:
            self.parent_window.show()
        self.close()

    def load_product_data(self, article: str):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            article,
                            name,
                            uom,
                            price,
                            supplier,
                            manufacturer,
                            category,
                            discount,
                            amount,
                            description,
                            photo
                        FROM product
                        WHERE article = %s
                        """,
                        (article,),
                    )
                    row = cur.fetchone()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось загрузить данные товара:\n{e}",
            )
            return

        if row is None:
            QtWidgets.QMessageBox.warning(
                self,
                "Товар не найден",
                "Товар с указанным артикулом не найден в базе данных.",
            )
            return

        (
            article,
            name,
            uom,
            price,
            supplier,
            producer,
            category,
            discount,
            amount,
            description,
            photo,
        ) = row

        self.edit_article.setText(article)
        self.edit_name.setText(name or "")
        self.edit_uom.setText(uom or "")
        self.edit_supplier.setText(supplier or "")
        self.edit_price.setText("" if price is None else str(price))
        self.edit_amount.setText("" if amount is None else str(amount))
        self.edit_discount.setText("" if discount is None else str(discount))
        self.edit_description.setPlainText(description or "")

        if category:
            index = self.combo_category.findText(category)
            if index == -1:
                self.combo_category.addItem(category)
                index = self.combo_category.count() - 1
            self.combo_category.setCurrentIndex(index)

        if producer:
            index = self.combo_producer.findText(producer)
            if index == -1:
                self.combo_producer.addItem(producer)
                index = self.combo_producer.count() - 1
            self.combo_producer.setCurrentIndex(index)

        self.original_photo_path = photo
        self.saved_photo_path = photo
        # превью обновится в __init__ / update_photo_preview


# ---------- ОКНО ДОБАВЛЕНИЯ / РЕДАКТИРОВАНИЯ ЗАКАЗА ----------
class AddZakazWindow(QtWidgets.QWidget):
    def __init__(self, parent_window, order_id: int | None = None):
        super().__init__()
        uic.loadUi("ui/addZakaz.ui", self)
        self.setFixedSize(self.size())
        self.setWindowIcon(QIcon("pics/icon.ico"))

        self.parent_window = parent_window
        self.order_id = order_id  # None = добавление, not None = редактирование

        # заголовок
        self.header_label: QtWidgets.QLabel = self.label
        if self.order_id is None:
            title_text = "Добавление заказа"
        else:
            title_text = "Редактирование заказа"
        self.setWindowTitle(title_text)
        self.header_label.setText(title_text)

        # поля формы
        self.edit_article = self.lineEdit_article
        self.combo_status = self.comboBox_status
        self.combo_pvz = self.comboBox_pvz
        self.edit_order_date = self.lineEdit_order_date
        self.edit_issue_date = self.lineEdit_issue_date
        self.edit_fio = self.lineEdit_fio
        self.edit_code = self.lineEdit_code

        # кнопка удаления заказа (на форме)
        self.button_delete_order = self.pushButton_delete_order
        if self.order_id is None:
            self.button_delete_order.hide()
        else:
            self.button_delete_order.show()
            self.button_delete_order.clicked.connect(self.delete_current_order)

        self.load_pvz_for_combo()
        self.init_status_combo()

        if self.order_id is not None:
            self.load_order_data(self.order_id)

        self.pushButton_save.clicked.connect(self.save_and_close)
        self.pushButton_cancel.clicked.connect(self.cancel_and_close)

    # --- парсинг даты ---
    @staticmethod
    def parse_date(text: str) -> datetime.date | None:
        text = text.strip()
        if not text:
            return None
        try:
            return datetime.datetime.strptime(text, "%d.%m.%Y").date()
        except ValueError:
            pass
        try:
            return datetime.datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            pass
        raise ValueError("Неверный формат даты")

    @staticmethod
    def format_date(d: datetime.date | None) -> str:
        if d is None:
            return ""
        return d.strftime("%d.%m.%Y")

    # --- парсинг строки артикула заказа ---
    def parse_article_string(self, text: str):
        """
        Ожидается строка вида: 'ART1, 2, ART2, 1, ...'
        Возвращает список (article, qty) с суммированием одинаковых артикулов.
        """
        text = text.strip()
        if not text:
            raise ValueError(
                "Поле «Артикул» обязательно. Укажите артикулы и количества через запятую."
            )

        parts = [p.strip() for p in text.split(",") if p.strip()]
        if len(parts) % 2 != 0:
            raise ValueError(
                "Строка артикула заказа должна иметь вид «ART1, 2, ART2, 1»."
            )

        aggregated: dict[str, int] = {}
        for i in range(0, len(parts), 2):
            art = parts[i]
            qty_str = parts[i + 1]
            try:
                qty = int(qty_str)
            except ValueError:
                raise ValueError(
                    f"Количество для артикула «{art}» должно быть целым числом."
                )
            if qty <= 0:
                raise ValueError(
                    f"Количество для артикула «{art}» должно быть больше нуля."
                )

            aggregated[art] = aggregated.get(art, 0) + qty

        return list(aggregated.items())

    def load_pvz_for_combo(self):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id_pvz, address
                        FROM pvz
                        ORDER BY id_pvz
                        """
                    )
                    rows = cur.fetchall()
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Ошибка БД", str(e))
            rows = []

        self.combo_pvz.clear()
        self.combo_pvz.addItem("", userData=None)

        for id_pvz, address in rows:
            self.combo_pvz.addItem(address, userData=id_pvz)

    def init_status_combo(self):
        self.combo_status.clear()
        self.combo_status.addItem("", userData=None)
        self.combo_status.addItem("Новый")
        self.combo_status.addItem("Завершен")

    def load_order_data(self, order_id: int):
        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            id_order,
                            article,
                            order_date,
                            delivery_date,
                            id_pvz,
                            client_fio,
                            pickup_code,
                            status
                        FROM orders
                        WHERE id_order = %s
                        """,
                        (order_id,),
                    )
                    row = cur.fetchone()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось загрузить данные заказа:\n{e}",
            )
            return

        if row is None:
            QtWidgets.QMessageBox.warning(
                self,
                "Заказ не найден",
                "Заказ с указанным номером не найден в базе данных.",
            )
            return

        (
            _id,
            article,
            order_date,
            delivery_date,
            id_pvz,
            client_fio,
            pickup_code,
            status,
        ) = row

        self.edit_article.setText(article or "")
        self.edit_order_date.setText(self.format_date(order_date))
        self.edit_issue_date.setText(self.format_date(delivery_date))
        self.edit_fio.setText(client_fio or "")
        self.edit_code.setText("" if pickup_code is None else str(pickup_code))

        norm_status = (status or "").strip().lower()
        found_index = -1
        for i in range(self.combo_status.count()):
            item_text = self.combo_status.itemText(i).strip().lower()
            if item_text == norm_status:
                found_index = i
                break

        if found_index != -1:
            self.combo_status.setCurrentIndex(found_index)
        elif status:
            self.combo_status.addItem(status)
            self.combo_status.setCurrentIndex(self.combo_status.count() - 1)

        if id_pvz is not None:
            for i in range(self.combo_pvz.count()):
                if self.combo_pvz.itemData(i) == id_pvz:
                    self.combo_pvz.setCurrentIndex(i)
                    break

    # --- удаление заказа из формы редактирования ---
    def delete_current_order(self):
        if self.order_id is None:
            return

        reply = QtWidgets.QMessageBox.question(
            self,
            "Удаление заказа",
            f"Вы действительно хотите удалить заказ №{self.order_id}?",
            QtWidgets.QMessageBox.StandardButton.Yes
            | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No,
        )
        if reply != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    # вернём на склад позиции и удалим записи
                    cur.execute(
                        "SELECT id_product, amount FROM order_items WHERE id_order = %s",
                        (self.order_id,),
                    )
                    old_items = cur.fetchall()
                    for id_prod, amt in old_items:
                        cur.execute(
                            "UPDATE product SET amount = amount + %s WHERE id_product = %s",
                            (amt, id_prod),
                        )

                    cur.execute(
                        "DELETE FROM order_items WHERE id_order = %s",
                        (self.order_id,),
                    )

                    cur.execute(
                        "DELETE FROM orders WHERE id_order = %s",
                        (self.order_id,),
                    )

                    if cur.rowcount == 0:
                        QtWidgets.QMessageBox.information(
                            self,
                            "Удаление заказа",
                            "Заказ с таким номером не найден.",
                        )
                        return

                conn.commit()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось удалить заказ:\n{e}",
            )
            return

        QtWidgets.QMessageBox.information(
            self,
            "Удаление заказа",
            "Заказ успешно удалён.",
        )

        if self.parent_window is not None:
            self.parent_window.load_orders()
            self.parent_window.show()

        self.close()

    def save_and_close(self):
        article_str = self.edit_article.text().strip()
        status = self.combo_status.currentText().strip()
        id_pvz = self.combo_pvz.currentData()
        order_date_text = self.edit_order_date.text()
        issue_date_text = self.edit_issue_date.text()
        client_fio = self.edit_fio.text().strip() or None
        pickup_code_text = self.edit_code.text().strip()

        # парсим строку артикула -> список (art, qty)
        try:
            items = self.parse_article_string(article_str)
        except ValueError as ve:
            QtWidgets.QMessageBox.warning(
                self,
                "Некорректные данные",
                str(ve),
            )
            return

        if not status:
            QtWidgets.QMessageBox.warning(
                self,
                "Некорректные данные",
                "Выберите статус заказа.",
            )
            return

        if id_pvz is None:
            QtWidgets.QMessageBox.warning(
                self,
                "Некорректные данные",
                "Выберите пункт выдачи.",
            )
            return

        try:
            order_date = self.parse_date(order_date_text) if order_date_text else None
        except ValueError:
            QtWidgets.QMessageBox.warning(
                self,
                "Некорректные данные",
                "Неверный формат даты заказа. Используйте ДД.ММ.ГГГГ или ГГГГ-ММ-ДД.",
            )
            return

        try:
            delivery_date = (
                self.parse_date(issue_date_text) if issue_date_text else None
            )
        except ValueError:
            QtWidgets.QMessageBox.warning(
                self,
                "Некорректные данные",
                "Неверный формат даты выдачи. Используйте ДД.ММ.ГГГГ или ГГГГ-ММ-ДД.",
            )
            return

        pickup_code = None
        if pickup_code_text:
            try:
                pickup_code = int(pickup_code_text)
            except ValueError:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Некорректные данные",
                    "Код получения заказа должен быть целым числом.",
                )
                return

        try:
            with get_connection() as conn:
                with conn.cursor() as cur:
                    try:
                        # если редактируем — вернём на склад старые позиции и удалим order_items
                        if self.order_id is not None:
                            cur.execute(
                                """
                                SELECT id_product, amount
                                FROM order_items
                                WHERE id_order = %s
                                """,
                                (self.order_id,),
                            )
                            old_items = cur.fetchall()
                            for id_prod, amt in old_items:
                                cur.execute(
                                    "UPDATE product SET amount = amount + %s WHERE id_product = %s",
                                    (amt, id_prod),
                                )

                            cur.execute(
                                "DELETE FROM order_items WHERE id_order = %s",
                                (self.order_id,),
                            )

                        # проверяем наличие товаров и достаточность остатков
                        new_items: list[tuple[int, int]] = []  # (id_product, qty)
                        for art, qty in items:
                            cur.execute(
                                """
                                SELECT id_product, amount
                                FROM product
                                WHERE article = %s
                                FOR UPDATE
                                """,
                                (art,),
                            )
                            row = cur.fetchone()
                            if row is None:
                                raise ValueError(
                                    f"Товар с артикулом «{art}» не найден в базе данных."
                                )
                            id_prod, stock_amount = row
                            if qty > stock_amount:
                                raise ValueError(
                                    f"Недостаточно товара «{art}». "
                                    f"На складе: {stock_amount}, требуется: {qty}."
                                )
                            new_items.append((id_prod, qty))

                        # добавление / обновление заказа
                        if self.order_id is None:
                            cur.execute(
                                """
                                INSERT INTO orders (
                                    article,
                                    order_date,
                                    delivery_date,
                                    id_pvz,
                                    client_fio,
                                    pickup_code,
                                    status
                                )
                                VALUES (%s, %s, %s, %s, %s, %s, %s)
                                RETURNING id_order
                                """,
                                (
                                    article_str,
                                    order_date,
                                    delivery_date,
                                    id_pvz,
                                    client_fio,
                                    pickup_code,
                                    status,
                                ),
                            )
                            self.order_id = cur.fetchone()[0]
                            msg_title = "Заказ добавлен"
                            msg_text = f"Новый заказ успешно добавлен (№{self.order_id})."
                        else:
                            cur.execute(
                                """
                                UPDATE orders
                                SET
                                    article = %s,
                                    order_date = %s,
                                    delivery_date = %s,
                                    id_pvz = %s,
                                    client_fio = %s,
                                    pickup_code = %s,
                                    status = %s
                                WHERE id_order = %s
                                """,
                                (
                                    article_str,
                                    order_date,
                                    delivery_date,
                                    id_pvz,
                                    client_fio,
                                    pickup_code,
                                    status,
                                    self.order_id,
                                ),
                            )
                            if cur.rowcount == 0:
                                raise RuntimeError(
                                    "Не удалось обновить заказ (возможно, он был удалён)."
                                )
                            msg_title = "Заказ обновлён"
                            msg_text = "Данные заказа успешно обновлены."

                        # записываем позиции заказа + уменьшаем остатки
                        for id_prod, qty in new_items:
                            cur.execute(
                                "UPDATE product SET amount = amount - %s WHERE id_product = %s",
                                (qty, id_prod),
                            )
                            cur.execute(
                                """
                                INSERT INTO order_items (id_order, id_product, amount)
                                VALUES (%s, %s, %s)
                                """,
                                (self.order_id, id_prod, qty),
                            )

                        conn.commit()
                    except ValueError as ve:
                        conn.rollback()
                        QtWidgets.QMessageBox.warning(
                            self,
                            "Некорректные данные",
                            str(ve),
                        )
                        return
                    except Exception as e:
                        conn.rollback()
                        QtWidgets.QMessageBox.critical(
                            self,
                            "Ошибка БД",
                            f"Не удалось сохранить данные заказа:\n{e}",
                        )
                        return

        except Exception as e:
            # сюда попадём только если не смогли вообще подключиться/открыть транзакцию
            QtWidgets.QMessageBox.critical(
                self,
                "Ошибка БД",
                f"Не удалось сохранить данные заказа:\n{e}",
            )
            return

        QtWidgets.QMessageBox.information(self, msg_title, msg_text)

        if self.parent_window is not None:
            self.parent_window.load_orders()
            self.parent_window.show()

        self.close()

    def cancel_and_close(self):
        if self.parent_window is not None:
            self.parent_window.show()
        self.close()


# ---------- ТОЧКА ВХОДА ----------
def main():
    app = QtWidgets.QApplication(sys.argv)
    window = AuthorizeWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
