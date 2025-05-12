<<<<<<< HEAD
import json
import logging
import sqlite3
from dataclasses import dataclass
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# Logging sozlamalari
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ma'lumotlar bazasi
DB_FILE = "korzinka.db"

# Admin ID
ADMIN_ID = 7000089859


# Mahsulot va buyurtma sinflari
@dataclass
=======
import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ConversationHandler
from telegram.ext import ContextTypes
from datetime import datetime
# Logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    level=logging.INFO)
logger = logging.getLogger(__name__)

# Fayl nomlari
USERS_FILE = 'users.json'
ORDERS_FILE = 'orders.json'
COMMENTS_FILE = 'comments.json'

# Foydalanuvchi savatlari
user_carts = {}

# States
NAME, EMAIL, PHONE, ADDRESS, PARKING_INFO = range(5)


# Mahsulotlar
>>>>>>> a1142c0474d00fc43c6d8ed478a97b29eaa0bfed
class Product:
    id: int
    name: str
    price: int
    description: str
    image_url: str
    category: str
    discount: int = 0

<<<<<<< HEAD
    def discounted_price(self) -> int:
        return int(self.price * (1 - self.discount / 100))


@dataclass
class Order:
    id: int
    user_id: int
    items: Dict[str, int]
    total_price: int
    user_info: Dict[str, str]
    status: str = "pending"


@dataclass
class ShoppingCart:
    items: Dict[str, int]

    def __init__(self):
        self.items = {}

    def add_item(self, product: Product, quantity: int = 1):
        if product.name in self.items:
            self.items[product.name] += quantity
        else:
            self.items[product.name] = quantity

    def remove_item(self, product_name: str):
        if product_name in self.items:
            del self.items[product_name]

    def update_quantity(self, product_name: str, quantity: int):
        if quantity <= 0:
            self.remove_item(product_name)
        else:
            self.items[product_name] = quantity

    def clear(self):
        self.items.clear()

    def total_price(self, catalog: Dict[str, Product]) -> int:
        return sum(catalog[name].discounted_price() * qty for name, qty in self.items.items() if name in catalog)

    def is_empty(self) -> bool:
        return not bool(self.items)


# Ma'lumotlar bazasi bilan ishlash
class Database:
    def __init__(self):
        self.conn = sqlite3.connect(DB_FILE, check_same_thread=False)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                price INTEGER NOT NULL,
                description TEXT,
                image_url TEXT,
                category TEXT,
                discount INTEGER DEFAULT 0
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                items TEXT NOT NULL,
                total_price INTEGER NOT NULL,
                user_info TEXT NOT NULL,
                status TEXT DEFAULT 'pending'
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS promo_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT NOT NULL UNIQUE,
                discount INTEGER NOT NULL,
                active BOOLEAN DEFAULT 1
            )
        """)
        self.conn.commit()

    def add_product(self, product: Product):
        cursor = self.conn.cursor()
        try:
            cursor.execute(
                "INSERT OR REPLACE INTO products (name, price, description, image_url, category, discount) VALUES (?, ?, ?, ?, ?, ?)",
                (product.name, product.price, product.description, product.image_url, product.category,
                 product.discount)
            )
            self.conn.commit()
        except sqlite3.IntegrityError as e:
            logger.error(f"Mahsulot qo'shishda xato: {e}")

    def get_products(self, category: str = None, sort_by: str = None) -> List[Product]:
        cursor = self.conn.cursor()
        query = "SELECT * FROM products"
        params = ()
        if category:
            query += " WHERE category = ?"
            params = (category,)
        if sort_by == "price_asc":
            query += " ORDER BY price ASC"
        elif sort_by == "price_desc":
            query += " ORDER BY price DESC"
        elif sort_by == "discount":
            query += " ORDER BY discount DESC"
        cursor.execute(query, params)
        return [Product(*row) for row in cursor.fetchall()]

    def search_products(self, query: str) -> List[Product]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE name LIKE ?", (f"%{query}%",))
        return [Product(*row) for row in cursor.fetchall()]

    def get_product_by_name(self, name: str) -> Product:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM products WHERE name = ?", (name,))
        row = cursor.fetchone()
        return Product(*row) if row else None

    def delete_product(self, name: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM products WHERE name = ?", (name,))
        self.conn.commit()

    def add_order(self, order: Order):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO orders (user_id, items, total_price, user_info, status) VALUES (?, ?, ?, ?, ?)",
            (order.user_id, json.dumps(order.items), order.total_price, json.dumps(order.user_info), order.status)
        )
        self.conn.commit()

    def get_orders(self, user_id: int = None) -> List[Order]:
        cursor = self.conn.cursor()
        if user_id:
            cursor.execute("SELECT * FROM orders WHERE user_id = ?", (user_id,))
        else:
            cursor.execute("SELECT * FROM orders")
        return [
            Order(id=row[0], user_id=row[1], items=json.loads(row[2]), total_price=row[3], user_info=json.loads(row[4]),
                  status=row[5]) for row in cursor.fetchall()]

    def add_promo_code(self, code: str, discount: int):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO promo_codes (code, discount, active) VALUES (?, ?, ?)",
                       (code, discount, 1))
        self.conn.commit()

    def validate_promo_code(self, code: str) -> int:
        cursor = self.conn.cursor()
        cursor.execute("SELECT discount FROM promo_codes WHERE code = ? AND active = 1", (code,))
        row = cursor.fetchone()
        return row[0] if row else 0

    def get_top_products(self, limit: int = 5) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT items FROM orders
        """)
        items_count = {}
        for row in cursor.fetchall():
            items = json.loads(row[0])
            for name, qty in items.items():
                items_count[name] = items_count.get(name, 0) + qty
        sorted_items = sorted(items_count.items(), key=lambda x: x[1], reverse=True)[:limit]
        return [{"name": name, "count": count} for name, count in sorted_items]


# Global ma'lumotlar
class SupermarketData:
    def __init__(self):
        self.db = Database()
        self.product_list = self.db.get_products()
        self.product_catalog = {p.name: p for p in self.product_list}
        self.categories = sorted(list(set(p.category for p in self.product_list)))
        self.user_carts: Dict[int, ShoppingCart] = {}
        self.user_states: Dict[int, str] = {}
        self.initialize_data()

    def initialize_data(self):
        if not self.product_list:
            initial_products = [
                Product(1, "Olma", 5000, "Yashil va shirin olma", "https://example.com/olma.jpg", "Meva", 10),
                Product(2, "Banan", 8000, "Tropik banan", "https://example.com/banan.jpg", "Meva", 0),
                Product(3, "Uzum", 10000, "Toza uzum", "https://example.com/uzum.jpg", "Meva", 5),
                Product(4, "Anor", 12000, "Qizil va foydali anor", "https://example.com/anor.jpg", "Meva", 0),
                Product(5, "Pomidor", 6000, "Yangi va qizil pomidor", "https://example.com/pomidor.jpg", "Sabzavot", 5),
                Product(6, "Guruch", 25000, "Yuqori sifatli ozbek guruchi", "https://example.com/guruch.jpg",
                        "Don mahsulotlari", 0),
                Product(7, "Go‘sht", 80000, "Taza qo‘y go‘shti", "https://example.com/gosht.jpg", "Go‘sht", 0),
                Product(8, "Tuxum", 15000, "10 dona toza tuxum", "https://example.com/tuxum.jpg", "Sut mahsulotlari",
                        0),
                Product(9, "Sut", 12000, "1 litr tabiiy sut", "https://example.com/sut.jpg", "Sut mahsulotlari", 0),
                Product(10, "Cola", 12000, "Yaxshi sovutgich Coca-Cola", "https://example.com/cola.jpg", "Ichimlik",
                        15),
                Product(11, "Choy", 10000, "Yashil choy, 100gr", "https://example.com/choy.jpg", "Ichimlik", 0),
                Product(12, "Non", 3000, "Yangi pishirilgan ozbek noni", "https://example.com/non.jpg",
                        "Nondan tayyor mahsulotlar", 0),
                Product(13, "Shakar", 15000, "1kg oq shakar", "https://example.com/shakar.jpg", "Qand va shakar", 0),
                Product(14, "Margarin", 20000, "500gr sifatli margarin", "https://example.com/margarin.jpg",
                        "Yog‘ mahsulotlari", 0),
                Product(15, "Qaymoq", 10000, "200gr tabiiy qaymoq", "https://example.com/qaymoq.jpg",
                        "Sut mahsulotlari", 5),
                Product(16, "Kartoshka", 5000, "Yangi kartoshka", "https://example.com/kartoshka.jpg", "Sabzavot", 0),
                Product(17, "Piyoz", 4000, "Qizil piyoz", "https://example.com/piyoz.jpg", "Sabzavot", 0),
                Product(18, "Chips", 15000, "Doritos chips, 100gr", "https://example.com/chips.jpg", "Shirinliklar", 0),
                Product(19, "Shokolad", 20000, "Milka shokoladi, 100gr", "https://example.com/shokolad.jpg",
                        "Shirinliklar", 10),
                Product(20, "Qatiq", 8000, "300ml tabiiy qatiq", "https://example.com/qatiq.jpg", "Sut mahsulotlari",
                        0),
            ]
            for p in initial_products:
                self.db.add_product(p)
            self.db.add_promo_code("KORZINKA10", 10)
            self.db.add_promo_code("YANGI2025", 15)
            self.product_list = self.db.get_products()
            self.product_catalog = {p.name: p for p in self.product_list}
            self.categories = sorted(list(set(p.category for p in self.product_list)))


# Kategoriyalar va mahsulotlar menyusi
def get_categories_keyboard(page: int = 0, per_page: int = 5) -> InlineKeyboardMarkup:
    start = page * per_page
    end = start + per_page
    categories = supermarket.categories[start:end]
    keyboard = [[InlineKeyboardButton(cat, callback_data=f"category_{cat}")] for cat in categories]

    nav_buttons = []
    if start > 0:
        nav_buttons.append(InlineKeyboardButton("⬅️ Oldingi", callback_data=f"cat_page_{page - 1}"))
    if end < len(supermarket.categories):
        nav_buttons.append(InlineKeyboardButton("Keyingi ➡️", callback_data=f"cat_page_{page + 1}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([
        InlineKeyboardButton("🛒 Savatni ko'rish", callback_data="show_cart"),
        InlineKeyboardButton("🔍 Qidiruv", callback_data="search")
    ])
    keyboard.append([
        InlineKeyboardButton("📜 Buyurtmalar tarixi", callback_data="history"),
        InlineKeyboardButton("🔥 Chegirmalar", callback_data="discounts")
    ])
    return InlineKeyboardMarkup(keyboard)


def get_products_keyboard(category: str, page: int = 0, per_page: int = 5, sort_by: str = None) -> InlineKeyboardMarkup:
    products = supermarket.db.get_products(category, sort_by)
    start = page * per_page
    end = start + per_page
    products = products[start:end]

    keyboard = [
        [
            InlineKeyboardButton(f"{p.name} - {p.discounted_price():,} so'm", callback_data=f"view_{p.name}"),
            InlineKeyboardButton("➕", callback_data=f"add_{p.name}_1"),
        ] for p in products
    ]

    nav_buttons = []
    if start > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Oldingi", callback_data=f"prod_page_{category}_{page - 1}_{sort_by or ''}"))
    if end < len(products):
        nav_buttons.append(
            InlineKeyboardButton("Keyingi ➡️", callback_data=f"prod_page_{category}_{page + 1}_{sort_by or ''}"))
    if nav_buttons:
        keyboard.append(nav_buttons)

    keyboard.append([
        InlineKeyboardButton("🔙 Kategoriyalarga qaytish", callback_data="show_categories"),
        InlineKeyboardButton("📈 Narx bo'yicha", callback_data=f"sort_{category}_price_asc")
    ])
    return InlineKeyboardMarkup(keyboard)


def get_cart_keyboard(cart: ShoppingCart) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(f"❌ {name}", callback_data=f"remove_{name}"),
            InlineKeyboardButton(f"🔢 {qty}", callback_data=f"edit_qty_{name}"),
        ] for name, qty in cart.items.items()
    ]
    keyboard.append([InlineKeyboardButton("🗑 Savatni tozalash", callback_data="clear_cart")])
    keyboard.append([InlineKeyboardButton("✅ Buyurtma berish", callback_data="order")])
    keyboard.append([InlineKeyboardButton("🎟 Promo-kod kiritish", callback_data="promo_code")])
    return InlineKeyboardMarkup(keyboard)


def get_order_submit_keyboard(user_info: Dict[str, str]) -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("📤 Ma'lumotlarni jo'natish", callback_data="submit_order")],
        [InlineKeyboardButton("👤 Ismni kiritish", callback_data="request_name")],
        [InlineKeyboardButton("📍 Lokatsiya yuborish", callback_data="send_location")],
        [InlineKeyboardButton("📞 Kontakt yuborish", callback_data="send_contact")],
        [InlineKeyboardButton("🆔 Telegram ID ni jo'natish", callback_data="send_telegram_id")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("✅ Ha", callback_data="confirm_order_yes")],
        [InlineKeyboardButton("❌ Yo'q", callback_data="confirm_order_no")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_location_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("📍 Lokatsiyani yuborish", request_location=True)],
        [KeyboardButton("🔙 Orqaga")]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


def get_contact_keyboard() -> ReplyKeyboardMarkup:
    keyboard = [
        [KeyboardButton("📞 Kontaktni yuborish", request_contact=True)],
        [KeyboardButton("🔙 Orqaga")]
    ]
    return ReplyKeyboardMarkup(keyboard, one_time_keyboard=True, resize_keyboard=True)


# Bot funksiyalari
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 Assalomu alaykum! 🏪 Korzinka Supermarket botiga xush kelibsiz!\n"
        "💚 O‘zbekistonning eng yirik supermarket tarmog‘ida xarid qiling.\n"
        "🔥 Haftalik chegirmalar va Korzinka Club ballarini yig‘ing!\n\n"
        "Kategoriyalardan birini tanlang yoki qidiruvdan foydalaning:"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_categories_keyboard())


async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    page = int(query.data.split("_")[-1]) if query.data.startswith("cat_page_") else 0
    markup = get_categories_keyboard(page)
    text = "🛍 Kategoriyalarni tanlang:"
    await (query.edit_message_text(text, reply_markup=markup) if query else update.message.reply_text(text,
                                                                                                      reply_markup=markup))


async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    if data.startswith("prod_page_"):
        category, page, sort_by = data.split("_")[2], int(data.split("_")[3]), data.split("_")[4] or None
    else:
        category, page, sort_by = data.split("_", 1)[1], 0, None
    markup = get_products_keyboard(category, page, sort_by=sort_by)
    await query.edit_message_text(f"🛍 {category} kategoriyasi:", reply_markup=markup)


async def view_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_name = query.data.split("_", 1)[1]
    product = supermarket.product_catalog.get(product_name)
    if not product:
        await query.edit_message_text("❌ Mahsulot topilmadi.")
        return

    text = (
        f"📦 {product.name}\n\n"
        f"💸 Narxi: {product.discounted_price():,} so‘m"
    )
    if product.discount > 0:
        text += f" (Asl narx: {product.price:,} so‘m, {product.discount}% chegirma)\n"
    else:
        text += "\n"
    text += (
        f"📝 Tavsif: {product.description}\n"
        f"🖼 Rasm: {product.image_url}\n"
        f"🏷 Kategoriya: {product.category}"
    )
    if product.image_url:
        await query.message.reply_photo(product.image_url, caption=text)
    else:
        await query.edit_message_text(text)
    await query.message.reply_text(
        text,
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Savatga qo‘shish", callback_data=f"add_{product.name}_1")],
            [InlineKeyboardButton("🔙 Orqaga", callback_data=f"category_{product.category}")]
        ])
    )


async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user_id = query.from_user.id if query else update.message.from_user.id
    cart = supermarket.user_carts.get(user_id)

    if not cart or cart.is_empty():
        text = "🛒 Savatingiz bo‘sh. 🛍 Xaridni boshlang!"
        markup = get_categories_keyboard()
    else:
        text = "🛒 Sizning savatingiz:\n\n"
        for name, qty in cart.items.items():
            product = supermarket.product_catalog.get(name)
            price = product.discounted_price()
            text += f"• {name} x {qty} = {price * qty:,} so‘m"
            if product.discount > 0:
                text += f" ({product.discount}% chegirma)"
            text += "\n"
        text += f"\n💰 Umumiy: {cart.total_price(supermarket.product_catalog):,} so‘m"
        markup = get_cart_keyboard(cart)

    if query:
        await query.edit_message_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)


async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_orders = supermarket.db.get_orders(user_id)

    if not user_orders:
        await query.edit_message_text("📜 Sizda hali buyurtmalar yo‘q.")
        return

    text = "📜 Sizning buyurtmalaringiz:\n\n"
    for i, order in enumerate(user_orders, 1):
        text += f"Buyurtma #{i}\n"
        text += f"💰 Umumiy: {order.total_price:,} so‘m\n"
        text += f"👤 Ism: {order.user_info.get('name', 'Noma’lum')}\n"
        text += f"📞 Telefon: {order.user_info.get('phone', 'Noma’lum')}\n"
        text += f"📍 Lokatsiya: {order.user_info.get('location', 'Noma’lum')}\n"
        text += f"🆔 Telegram ID: {order.user_info.get('telegram_id', 'Noma’lum')}\n"
        text += f"📦 Mahsulotlar:\n"
        for name, qty in order.items.items():
            text += f"  • {name} x {qty}\n"
        text += "\n"
    await query.edit_message_text(text)


async def show_discounts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    products = supermarket.db.get_products(sort_by="discount")
    if not products:
        await query.edit_message_text("🔥 Hozirda chegirmali mahsulotlar yo‘q.")
        return
    text = "🔥 Chegirmali mahsulotlar:\n\n"
    for p in products[:5]:
        if p.discount > 0:
            text += f"• {p.name} - {p.discounted_price():,} so‘m ({p.discount}% chegirma)\n"
    keyboard = [[InlineKeyboardButton(p.name, callback_data=f"view_{p.name}")] for p in products[:5] if p.discount > 0]
    keyboard.append([InlineKeyboardButton("🔙 Kategoriyalarga qaytish", callback_data="show_categories")])
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    supermarket.user_states[query.from_user.id] = "search"
    await query.edit_message_text("🔍 Mahsulot nomini kiriting (masalan, Olma):")


async def handle_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if supermarket.user_states.get(user_id) == "search":
        text = update.message.text.lower()
        results = supermarket.db.search_products(text)
        if not results:
            await update.message.reply_text("❌ Mahsulot topilmadi.", reply_markup=get_categories_keyboard())
            return
        keyboard = [[InlineKeyboardButton(f"{p.name} - {p.discounted_price():,} so‘m", callback_data=f"view_{p.name}")]
                    for p in results]
        await update.message.reply_text("🔍 Topilgan mahsulotlar:", reply_markup=InlineKeyboardMarkup(keyboard))
        del supermarket.user_states[user_id]


async def handle_promo_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    supermarket.user_states[query.from_user.id] = "promo_code"
    await query.edit_message_text("🎟 Promo-kodni kiriting (masalan, KORZINKA10):")


async def apply_promo_code(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if supermarket.user_states.get(user_id) == "promo_code":
        code = update.message.text.strip()
        discount = supermarket.db.validate_promo_code(code)
        if discount > 0:
            context.user_data["promo_discount"] = discount
            await update.message.reply_text(f"✅ Promo-kod qo‘llanildi! {discount}% chegirma.")
        else:
            await update.message.reply_text("❌ Noto‘g‘ri yoki faol bo‘lmagan promo-kod.")
        del supermarket.user_states[user_id]
        await show_cart(update, context)


async def order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    cart = supermarket.user_carts.get(user_id)

    if not cart or cart.is_empty():
        await query.edit_message_text("🛒 Savatingiz bo‘sh.")
        return

    supermarket.user_states[user_id] = "order_name"
    await query.edit_message_text("👤 Ismingizni kiriting:", reply_markup=InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 Orqaga", callback_data="show_cart")]]))


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    state = supermarket.user_states.get(user_id)

    if text == "🔙 Orqaga":
        await show_cart(update, context)
        del supermarket.user_states[user_id]
        return

    if state == "order_name":
        context.user_data["order_name"] = text
        supermarket.user_states[user_id] = "order_phone"
        await update.message.reply_text("📞 Telefon raqamingizni kiriting (masalan, +998901234567):",
                                        reply_markup=InlineKeyboardMarkup(
                                            [[InlineKeyboardButton("🔙 Orqaga", callback_data="show_cart")]]))
    elif state == "order_phone":
        context.user_data["order_phone"] = text
        supermarket.user_states[user_id] = "order_location"
        await update.message.reply_text("📍 Lokatsiyangizni yuboring yoki manzilni kiriting:",
                                        reply_markup=InlineKeyboardMarkup([
                                            [InlineKeyboardButton("📍 Lokatsiya yuborish",
                                                                  callback_data="send_location")],
                                            [InlineKeyboardButton("📞 Kontakt yuborish", callback_data="send_contact")],
                                            [InlineKeyboardButton("🔙 Orqaga", callback_data="show_cart")]
                                        ]))
    elif state == "order_location" and not update.message.location and not update.message.contact:
        context.user_data["order_location"] = text
        context.user_data["telegram_id"] = str(user_id)
        await process_order_submit(update, context)
    elif state == "order_location" and update.message.location:
        context.user_data[
            "order_location"] = f"Lat: {update.message.location.latitude}, Lon: {update.message.location.longitude}"
        context.user_data["telegram_id"] = str(user_id)
        await update.message.reply_text("✅ Lokatsiya saqlandi.",
                                        reply_markup=get_order_submit_keyboard(context.user_data))
        del supermarket.user_states[user_id]
    elif state == "order_location" and update.message.contact:
        context.user_data["order_phone"] = update.message.contact.phone_number
        context.user_data["telegram_id"] = str(user_id)
        await update.message.reply_text("✅ Kontakt saqlandi.",
                                        reply_markup=get_order_submit_keyboard(context.user_data))
        del supermarket.user_states[user_id]
    elif state == "request_name":
        context.user_data["order_name"] = text
        del supermarket.user_states[user_id]
        await update.message.reply_text("✅ Ism saqlandi.", reply_markup=get_order_submit_keyboard(context.user_data))


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "show_categories":
        await show_categories(update, context)
    elif data.startswith("cat_page_"):
        await show_categories(update, context)
    elif data.startswith("category_") or data.startswith("prod_page_") or data.startswith("sort_"):
        await show_products(update, context)
    elif data.startswith("view_"):
        await view_product(update, context)
    elif data == "show_cart":
        await show_cart(update, context)
    elif data == "history":
        await show_history(update, context)
    elif data == "discounts":
        await show_discounts(update, context)
    elif data == "search":
        await search(update, context)
    elif data == "promo_code":
        await handle_promo_code(update, context)
    elif data.startswith("add_"):
        parts = data.split("_")
        product_name, quantity = parts[1], int(parts[2]) if len(parts) > 2 else 1
        product = supermarket.product_catalog.get(product_name)
        if not product:
            await query.edit_message_text("❌ Mahsulot topilmadi.")
            return
        cart = supermarket.user_carts.setdefault(user_id, ShoppingCart())
        cart.add_item(product, quantity)
        await query.edit_message_text(
            f"✅ {product.name} ({quantity} dona) savatga qo‘shildi.",
            reply_markup=get_products_keyboard(product.category)
        )
    elif data.startswith("remove_"):
        product_name = data.split("_", 1)[1]
        cart = supermarket.user_carts.get(user_id)
        if cart:
            cart.remove_item(product_name)
        await show_cart(update, context)
    elif data.startswith("edit_qty_"):
        product_name = data.split("_", 2)[2]
        supermarket.user_states[user_id] = f"edit_qty_{product_name}"
        await query.edit_message_text(f"🔢 {product_name} uchun yangi miqdorni kiriting (masalan, 2):")
    elif data == "clear_cart":
        cart = supermarket.user_carts.get(user_id)
        if cart:
            cart.clear()
        await query.edit_message_text("🗑 Savat tozalandi.", reply_markup=get_categories_keyboard())
    elif data == "order":
        await order(update, context)
    elif data == "submit_order":
        if "order_name" not in context.user_data or "order_phone" not in context.user_data or "order_location" not in context.user_data or "telegram_id" not in context.user_data:
            await query.edit_message_text(
                "❌ Iltimos, barcha ma'lumotlarni to'ldiring.",
                reply_markup=get_order_submit_keyboard(context.user_data)
            )
            return
        await query.edit_message_text(
            "📤 Ma'lumotlarni yuborishni xohlaysizmi?",
            reply_markup=get_confirmation_keyboard()
        )
    elif data == "confirm_order_yes":
        await confirm_order(update, context)
    elif data == "confirm_order_no":
        await query.edit_message_text(
            "❌ Buyurtma bekor qilindi.",
            reply_markup=get_order_submit_keyboard(context.user_data)
        )
    elif data == "request_name":
        supermarket.user_states[user_id] = "request_name"
        await query.edit_message_text("👤 Ismingizni kiriting:")
    elif data == "send_location":
        supermarket.user_states[user_id] = "order_location"
        await query.edit_message_text("📍 Iltimos, lokatsiyangizni yuboring:", reply_markup=get_location_keyboard())
    elif data == "send_contact":
        supermarket.user_states[user_id] = "order_location"
        await query.edit_message_text("📞 Iltimos, kontaktni yuboring:", reply_markup=get_contact_keyboard())
    elif data == "send_telegram_id":
        context.user_data["telegram_id"] = str(user_id)
        await query.edit_message_text("✅ Telegram ID saqlandi.",
                                      reply_markup=get_order_submit_keyboard(context.user_data))


async def confirm_order(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    cart = supermarket.user_carts.get(user_id)

    if not cart or cart.is_empty():
        await query.edit_message_text("🛒 Savatingiz bo‘sh.")
        return

    user_info = {
        "name": context.user_data.get("order_name", "Noma'lum"),
        "phone": context.user_data.get("order_phone", "Noma'lum"),
        "location": context.user_data.get("order_location", "Noma'lum"),
        "telegram_id": context.user_data.get("telegram_id", "Noma'lum")
    }
    total_price = cart.total_price(supermarket.product_catalog)
    promo_discount = context.user_data.get("promo_discount", 0)
    if promo_discount:
        total_price = int(total_price * (1 - promo_discount / 100))

    order = Order(
        id=0,
        user_id=user_id,
        items=cart.items.copy(),
        total_price=total_price,
        user_info=user_info,
        status="pending"
    )
    supermarket.db.add_order(order)
    cart.clear()
    context.user_data.pop("promo_discount", None)
    del supermarket.user_states[user_id]
    await query.edit_message_text(
        "✅ Buyurtmangiz qabul qilindi! 📦 Korzinka jamoasi 1-2 soat ichida yetkazib beradi.\n"
        "💚 Korzinka Club ballari uchun rahmat!",
        reply_markup=get_categories_keyboard()
    )


async def process_order_submit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id if query else update.message.from_user.id

    await update.message.reply_text(
        "Ma'lumotlarni kiritdingiz. Quyidagi tugmalardan birini tanlang:",
        reply_markup=get_order_submit_keyboard(context.user_data)
    )


async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ Siz admin emassiz.")
        return
    keyboard = [
        [InlineKeyboardButton("➕ Yangi mahsulot qo‘shish", callback_data="admin_add_product")],
        [InlineKeyboardButton("🗑 Mahsulot o‘chirish", callback_data="admin_delete_product")],
        [InlineKeyboardButton("📜 Buyurtmalarni ko‘rish", callback_data="admin_orders")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("🛠 Admin panel:", reply_markup=markup)


async def handle_admin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if user_id != ADMIN_ID:
        await query.edit_message_text("❌ Siz admin emassiz.")
        return
    data = query.data

    if data == "admin_add_product":
        supermarket.user_states[user_id] = "admin_add_name"
        await query.edit_message_text("📦 Mahsulot nomini kiriting:")
    elif data == "admin_delete_product":
        keyboard = [
            [InlineKeyboardButton(p.name, callback_data=f"admin_delete_{p.name}")]
            for p in supermarket.product_list
        ]
        markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("🗑 O‘chiriladigan mahsulotni tanlang:", reply_markup=markup)
    elif data.startswith("admin_delete_"):
        product_name = data.split("_", 2)[2]
        supermarket.db.delete_product(product_name)
        supermarket.product_list = supermarket.db.get_products()
        supermarket.product_catalog = {p.name: p for p in supermarket.product_list}
        supermarket.categories = sorted(list(set(p.category for p in supermarket.product_list)))
        await query.edit_message_text(f"✅ {product_name} o‘chirildi.")
    elif data == "admin_orders":
        orders = supermarket.db.get_orders()
        if not orders:
            await query.edit_message_text("📜 Hali buyurtmalar yo‘q.")
            return
        text = "📜 Buyurtmalar:\n\n"
        for i, order in enumerate(orders, 1):
            text += f"Buyurtma #{i}\n"
            text += f"👤 User ID: {order.user_id}\n"
            text += f"💰 Umumiy: {order.total_price:,} so‘m\n"
            text += f"📦 Mahsulotlar:\n"
            for name, qty in order.items.items():
                text += f"  • {name} x {qty}\n"
            text += "\n"
        await query.edit_message_text(text)


async def handle_admin_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id != ADMIN_ID:
        return
    text = update.message.text
    state = supermarket.user_states.get(user_id)

    if state == "admin_add_name":
        context.user_data["add_name"] = text
        supermarket.user_states[user_id] = "admin_add_price"
        await update.message.reply_text("💸 Mahsulot narxini kiriting (so‘mda):")
    elif state == "admin_add_price":
        try:
            price = int(text)
            context.user_data["add_price"] = price
            supermarket.user_states[user_id] = "admin_add_description"
            await update.message.reply_text("📝 Mahsulot tavsifini kiriting:")
        except ValueError:
            await update.message.reply_text("❌ Iltimos, raqam kiriting.")
    elif state == "admin_add_description":
        context.user_data["add_description"] = text
        supermarket.user_states[user_id] = "admin_add_image"
        await update.message.reply_text("🖼 Mahsulot rasm URL’sini kiriting (yoki 'yoq' deb yozing):")
    elif state == "admin_add_image":
        context.user_data["add_image"] = text if text != "yoq" else ""
        supermarket.user_states[user_id] = "admin_add_category"
        await update.message.reply_text("🏷 Mahsulot kategoriyasini kiriting (masalan, Meva):")
    elif state == "admin_add_category":
        product = Product(
            id=0,
            name=context.user_data["add_name"],
            price=context.user_data["add_price"],
            description=context.user_data["add_description"],
            image_url=context.user_data["add_image"],
            category=text,
            discount=0,
        )
        supermarket.db.add_product(product)
        supermarket.product_list = supermarket.db.get_products()
        supermarket.product_catalog = {p.name: p for p in supermarket.product_list}
        supermarket.categories = sorted(list(set(p.category for p in supermarket.product_list)))
        del supermarket.user_states[user_id]
        await update.message.reply_text(f"✅ {product.name} qo‘shildi.")


# Botni ishga tushurish
def main():
    app = ApplicationBuilder().token("7636929381:AAGXe7Vahyt8xILu0V5DLgcZmaK7Oh98RFQ").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("admin", admin_panel))
    app.add_handler(CallbackQueryHandler(handle_callback))
    app.add_handler(CallbackQueryHandler(handle_admin_callback, pattern="^admin_"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.LOCATION, handle_message))
    app.add_handler(MessageHandler(filters.CONTACT, handle_message))

    print("✅ Korzinka Supermarket boti ishga tushdi...")
    app.run_polling()


if __name__ == "__main__":
    supermarket = SupermarketData()
=======
    def to_dict(self):
        return self.__dict__


# Savatdagi mahsulotlar
class CartItem:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity

    def to_dict(self):
        return {"product": self.product.to_dict(), "quantity": self.quantity}


# Savat
class ShoppingCart:
    def __init__(self):
        self.items = []

    def add_item(self, product, quantity):
        if product.stock >= quantity:
            self.items.append(CartItem(product, quantity))
            product.stock -= quantity
        else:
            print(f"{product.name} uchun yetarli miqdor yo'q!")

    def total_price(self):
        return sum(item.product.price * item.quantity for item in self.items)

    def to_dict(self):
        return {"items": [item.to_dict() for item in self.items]}


# Foydalanuvchi ma'lumotlari
class User:
    def __init__(self, name, email, phone, address, parking_info=""):
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        self.parking_info = parking_info

    def to_dict(self):
        return self.__dict__


# Buyurtma
class Order:
    def __init__(self, user, cart, status, delivery_address, payment_method=""):
        self.user = user
        self.cart = cart
        self.status = status
        self.delivery_address = delivery_address
        self.payment_method = payment_method

    def to_dict(self):
        return {"user": self.user.to_dict(), "cart": self.cart.to_dict(), "status": self.status,
                "delivery_address": self.delivery_address, "payment_method": self.payment_method}


# Faylga saqlash va yuklash
def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def load_json(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


# Mahsulotlar ro'yxati
products = [
    Product("Non", 5000, "Oziq-ovqat", "Toshkent Bread Factory", "2025-12-31", 50),
    Product("Sut", 12000, "Oziq-ovqat", "Toshkent Milk", "2025-06-15", 30),
    Product("Yog'", 25000, "Oziq-ovqat", "Oltin Yog'", "2025-09-10", 20),
    Product("Shakar", 18000, "Oziq-ovqat", "Shakar Zavodi", "2026-01-01", 40),
    Product("Tuz", 3000, "Oziq-ovqat", "Mahalliy", "2026-12-31", 60),
    Product("Tuxum", 12000, "Oziq-ovqat", "Parrandachilik fabrikasi", "2025-05-20", 100),
    Product("Un", 8000, "Oziq-ovqat", "Toshkent Un", "2026-12-31", 80),
    Product("Kolbasa", 45000, "Oziq-ovqat", "Meat Products", "2025-06-30", 25),
    Product("Gosht", 50000, "Oziq-ovqat", "Taqsir Qassob", "2025-12-25", 50)
]


# Maxsus chegirma
def apply_discount(user_id, total_price):
    users = load_json(USERS_FILE)
    if user_id not in users:
        return total_price  # Yangi foydalanuvchi uchun chegirma yo'q

    discount = 0.1
    discounted_price = total_price * (1 - discount)
    return discounted_price


# --- STATEFUL functions ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salom! Iltimos, ismingizni kiriting:")
    return NAME

async def get_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["name"] = update.message.text
    await update.message.reply_text("Email manzilingizni kiriting:")
    return EMAIL

async def get_email(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["email"] = update.message.text
    await update.message.reply_text("Telefon raqamingizni kiriting:")
    return PHONE

async def get_phone(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["phone"] = update.message.text
    await update.message.reply_text("Manzilingizni kiriting:")
    return ADDRESS

async def get_address(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["address"] = update.message.text
    await update.message.reply_text("Parking joyingiz haqida ma'lumot kiriting (yoki 'yo'q' deb yozing):")
    return PARKING_INFO

async def get_parking_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["parking_info"] = update.message.text

    user_id = str(update.effective_user.id)
    user = User(
        name=context.user_data["name"],
        email=context.user_data["email"],
        phone=context.user_data["phone"],
        address=context.user_data["address"],
        parking_info=context.user_data["parking_info"]
    )
    users = load_json(USERS_FILE)
    users[user_id] = user.to_dict()
    save_json(USERS_FILE, users)

    await update.message.reply_text("✅ Ma'lumotlaringiz saqlandi! Endi buyurtma berishingiz mumkin.")
    return ConversationHandler.END


# To'lov usullarini tanlash
async def payment_methods(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Click", callback_data="pay_Click")],
        [InlineKeyboardButton("UzCard", callback_data="pay_UzCard")],
        [InlineKeyboardButton("Humo", callback_data="pay_Humo")],
        [InlineKeyboardButton("Naqd pul", callback_data="pay_Cash")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("To'lov usullarini tanlang:", reply_markup=reply_markup)


# Buyurtma qabul qilish va statusini yangilash
async def payment_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = str(query.from_user.id)

    if data.startswith("pay_"):
        payment_method = data.split("_")[1]
        cart = user_carts.get(user_id, [])
        users = load_json(USERS_FILE)

        order_data = {
            "user": users.get(user_id, {}),
            "cart": cart,
            "payment_method": payment_method,
            "status": "Tasdiqlangan"
        }

        orders = load_json(ORDERS_FILE)
        orders[user_id] = orders.get(user_id, [])
        orders[user_id].append(order_data)
        save_json(ORDERS_FILE, orders)

        user_carts[user_id] = []

        await query.edit_message_text("✅ Buyurtma qabul qilindi! Rahmat!")
        await query.message.reply_text("Buyurtmaning holati: **Tasdiqlangan**")


# Buyurtma holatini tekshirish
async def check_order_status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    orders = load_json(ORDERS_FILE)

    if user_id not in orders or not orders[user_id]:
        await update.message.reply_text("Sizda hech qanday buyurtma yo'q.")
    else:
        last_order = orders[user_id][-1]
        status = last_order['status']
        await update.message.reply_text(f"Sizning so‘nggi buyurtmangiz holati: {status}")


# Fikrlar va reytinglar
async def leave_review(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    product_name = "Non"  # Mahsulot nomi uchun misol
    review = update.message.text

    reviews = load_json(COMMENTS_FILE)
    if product_name not in reviews:
        reviews[product_name] = []

    reviews[product_name].append(review)
    save_json(COMMENTS_FILE, reviews)

    await update.message.reply_text(f"Sizning fikringiz qabul qilindi. Rahmat!")


# Maxsus takliflar va reklama
async def send_special_offer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    today = datetime.today().strftime('%Y-%m-%d')

    if today == "2025-04-28":
        offer = "🎉 Bugun maxsus 20% chegirma! Faqat bugun!"
        await update.message.reply_text(offer)
    else:
        await update.message.reply_text("Bugungi maxsus taklifimiz: Hech qanday taklif mavjud emas.")


# Botga buyruqlar
def main():
    application = Application.builder().token("7869848901:AAFNM-a-egIAsoWuQYR4PuGOPEoHRPaRCvc").build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_name)],
            EMAIL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_email)],
            PHONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_phone)],
            ADDRESS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_address)],
            PARKING_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_parking_info)],
        },
        fallbacks=[]
    )

    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("check_order", check_order_status))
    application.add_handler(CommandHandler("special_offer", send_special_offer))
    application.add_handler(MessageHandler(filters.TEXT, leave_review))
    application.add_handler(CallbackQueryHandler(payment_handler))

    application.run_polling()


if __name__ == "__main__":
>>>>>>> a1142c0474d00fc43c6d8ed478a97b29eaa0bfed
    main()