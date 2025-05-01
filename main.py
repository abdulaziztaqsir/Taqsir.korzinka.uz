import json
import logging
from dataclasses import dataclass
from typing import Dict, List
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# Loggingni yoqish
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Ma'lumotlar fayli
DATA_FILE = "supermarket_data.json"

# Mahsulot va korzinka class'lari
@dataclass
class Product:
    name: str
    price: int
    description: str
    image_url: str
    category: str
    discount: int = 0  # Chegirma foizda

    def discounted_price(self) -> int:
        return int(self.price * (1 - self.discount / 100))

@dataclass
class Order:
    user_id: int
    items: Dict[str, int]
    total_price: int
    user_info: Dict[str, str]

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

# Ma'lumotlarni yuklash va saqlash
def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {
                "products": [Product(**p) for p in data.get("products", [])],
                "orders": [Order(**o) for o in data.get("orders", [])]
            }
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"{DATA_FILE} topilmadi yoki noto‘g‘ri: {e}. Boshlang‘ich ma‘lumotlar ishlatilmoqda.")
        initial_data = {
            "products": [
                {"name": "Olma", "price": 5000, "description": "Yashil va shirin olma", "image_url": "https://example.com/olma.jpg", "category": "Meva", "discount": 10},
                {"name": "Banan", "price": 8000, "description": "Tropik banan", "image_url": "https://example.com/banan.jpg", "category": "Meva", "discount": 0},
                {"name": "Uzum", "price": 10000, "description": "Toza uzum", "image_url": "https://example.com/uzum.jpg", "category": "Meva", "discount": 5},
                {"name": "Anor", "price": 12000, "description": "Qizil va foydali anor", "image_url": "https://example.com/anor.jpg", "category": "Meva", "discount": 0},
                {"name": "Pomidor", "price": 6000, "description": "Yangi va qizil pomidor", "image_url": "https://example.com/pomidor.jpg", "category": "Sabzavot", "discount": 5},
                {"name": "Guruch", "price": 25000, "description": "Yuqori sifatli ozbek guruchi", "image_url": "https://example.com/guruch.jpg", "category": "Don mahsulotlari", "discount": 0},
                {"name": "Go‘sht", "price": 80000, "description": "Taza qo‘y go‘shti", "image_url": "https://example.com/gosht.jpg", "category": "Go‘sht", "discount": 0},
                {"name": "Tuxum", "price": 15000, "description": "10 dona toza tuxum", "image_url": "https://example.com/tuxum.jpg", "category": "Sut mahsulotlari", "discount": 0},
                {"name": "Sut", "price": 12000, "description": "1 litr tabiiy sut", "image_url": "https://example.com/sut.jpg", "category": "Sut mahsulotlari", "discount": 0},
                {"name": "Cola", "price": 12000, "description": "Yaxshi sovutgich Coca-Cola", "image_url": "https://example.com/cola.jpg", "category": "Ichimlik", "discount": 15},
                {"name": "Choy", "price": 10000, "description": "Yashil choy, 100gr", "image_url": "https://example.com/choy.jpg", "category": "Ichimlik", "discount": 0},
                {"name": "Non", "price": 3000, "description": "Yangi pishirilgan ozbek noni", "image_url": "https://example.com/non.jpg", "category": "Nondan tayyor mahsulotlar", "discount": 0},
                {"name": "Shakar", "price": 15000, "description": "1kg oq shakar", "image_url": "https://example.com/shakar.jpg", "category": "Qand va shakar", "discount": 0},
                {"name": "Margarin", "price": 20000, "description": "500gr sifatli margarin", "image_url": "https://example.com/margarin.jpg", "category": "Yog‘ mahsulotlari", "discount": 0},
                {"name": "Qaymoq", "price": 10000, "description": "200gr tabiiy qaymoq", "image_url": "https://example.com/qaymoq.jpg", "category": "Sut mahsulotlari", "discount": 5},
                {"name": "Kartoshka", "price": 5000, "description": "Yangi kartoshka", "image_url": "https://example.com/kartoshka.jpg", "category": "Sabzavot", "discount": 0},
                {"name": "Piyoz", "price": 4000, "description": "Qizil piyoz", "image_url": "https://example.com/piyoz.jpg", "category": "Sabzavot", "discount": 0},
                {"name": "Chips", "price": 15000, "description": "Doritos chips, 100gr", "image_url": "https://example.com/chips.jpg", "category": "Shirinliklar", "discount": 0},
                {"name": "Shokolad", "price": 20000, "description": "Milka shokoladi, 100gr", "image_url": "https://example.com/shokolad.jpg", "category": "Shirinliklar", "discount": 10},
                {"name": "Qatiq", "price": 8000, "description": "300ml tabiiy qatiq", "image_url": "https://example.com/qatiq.jpg", "category": "Sut mahsulotlari", "discount": 0}
            ],
            "orders": []
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(initial_data, f, indent=4, ensure_ascii=False)
        return initial_data

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        logger.info(f"Ma'lumotlar muvaffaqiyatli saqlandi: {DATA_FILE}")
    except Exception as e:
        logger.error(f"Ma'lumotlarni saqlashda xato: {e}")

# Global o'zgaruvchilarni boshqarish uchun class
class SupermarketData:
    def __init__(self):
        self.data = load_data()
        self.product_list = self.data["products"]
        self.product_catalog = {p.name: p for p in self.product_list}
        self.orders = self.data["orders"]
        self.categories = list(set(p.category for p in self.product_list))
        self.user_carts: Dict[int, ShoppingCart] = {}
        self.user_states: Dict[int, str] = {}

    def save(self):
        self.data["products"] = self.product_list
        self.data["orders"] = self.orders
        save_data(self.data)

# Global ma'lumotlar ob'ekti
supermarket = SupermarketData()

# Admin ID
ADMIN_ID = 7000089859  # O'zingizni Telegram ID'ingizga almashtiring

# Kategoriyalar va mahsulotlar ro'yxati
def get_categories_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton(cat, callback_data=f"category_{cat}")]
        for cat in supermarket.categories
    ]
    keyboard.append([InlineKeyboardButton("🛒 Savatni ko'rish", callback_data="show_cart")])
    keyboard.append([InlineKeyboardButton("📜 Buyurtmalar tarixi", callback_data="history")])
    return InlineKeyboardMarkup(keyboard)

def get_products_keyboard(category: str) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(f"{p.name} - {p.discounted_price():,} so'm", callback_data=f"view_{p.name}"),
            InlineKeyboardButton("➕", callback_data=f"add_{p.name}_1"),
        ]
        for p in supermarket.product_list if p.category == category
    ]
    keyboard.append([InlineKeyboardButton("🔙 Kategoriyalarga qaytish", callback_data="show_categories")])
    return InlineKeyboardMarkup(keyboard)

def get_cart_keyboard(cart: ShoppingCart) -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton(f"❌ {name}", callback_data=f"remove_{name}"),
            InlineKeyboardButton(f"🔢 {qty}", callback_data=f"edit_qty_{name}"),
        ]
        for name, qty in cart.items.items()
    ]
    keyboard.append([InlineKeyboardButton("🗑 Savatni tozalash", callback_data="clear_cart")])
    keyboard.append([InlineKeyboardButton("✅ Buyurtma berish", callback_data="order")])
    return InlineKeyboardMarkup(keyboard)

# Bot funksiyalari
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = get_categories_keyboard()
    await update.message.reply_text(
        "👋 Assalomu alaykum! 🏪 Korzinka Supermarket botiga xush kelibsiz!\n\n"
        "Kategoriyalardan birini tanlang:",
        reply_markup=keyboard,
    )

async def show_categories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    markup = get_categories_keyboard()
    text = "🛍 Kategoriyalarni tanlang:"
    if query:
        await query.edit_message_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)

async def show_products(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    category = query.data.split("_", 1)[1]
    markup = get_products_keyboard(category)
    await query.edit_message_text(f"🛍 {category} kategoriyasi:", reply_markup=markup)

async def show_cart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query if update.callback_query else None
    user_id = query.from_user.id if query else update.message.from_user.id
    cart = supermarket.user_carts.get(user_id)

    if not cart or cart.is_empty():
        text = "🛒 Savatingiz bo‘sh."
        if query:
            await query.edit_message_text(text, reply_markup=get_categories_keyboard())
        else:
            await update.message.reply_text(text, reply_markup=get_categories_keyboard())
        return

    text = "🛒 Sizning savatingiz:\n\n"
    for name, qty in cart.items.items():
        product = supermarket.product_catalog[name]
        price = product.discounted_price()
        text += f"• {name} x {qty} = {price * qty:,} so'm"
        if product.discount > 0:
            text += f" ({product.discount}% chegirma)"
        text += "\n"
    text += f"\n💰 Umumiy: {cart.total_price(supermarket.product_catalog):,} so'm"
    markup = get_cart_keyboard(cart)
    if query:
        await query.edit_message_text(text, reply_markup=markup)
    else:
        await update.message.reply_text(text, reply_markup=markup)

async def view_product(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    product_name = query.data.split("_", 1)[1]
    product = supermarket.product_catalog.get(product_name)
    if not product:
        await query.edit_message_text("❌ Mahsulot topilmadi.")
        return

    text = (
        f"📦 {product.name}\n\n"
        f"💸 Narxi: {product.discounted_price():,} so'm"
    )
    if product.discount > 0:
        text += f" (Asl narx: {product.price:,} so'm, {product.discount}% chegirma)\n"
    else:
        text += "\n"
    text += (
        f"📝 Tavsif: {product.description}\n"
        f"🖼 Rasm: {product.image_url}\n"
        f"🏷 Kategoriya: {product.category}"
    )
    keyboard = [
        [InlineKeyboardButton("➕ Savatga qo‘shish", callback_data=f"add_{product.name}_1")],
        [InlineKeyboardButton("🔙 Orqaga", callback_data=f"category_{product.category}")],
    ]
    markup = InlineKeyboardMarkup(keyboard)
    await query.edit_message_text(text, reply_markup=markup)

async def show_history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id
    user_orders = [o for o in supermarket.orders if o.user_id == user_id]

    if not user_orders:
        await query.edit_message_text("📜 Sizda hali buyurtmalar yo‘q.")
        return

    text = "📜 Sizning buyurtmalaringiz:\n\n"
    for i, order in enumerate(user_orders, 1):
        text += f"Buyurtma #{i}\n"
        text += f"💰 Umumiy: {order.total_price:,} so'm\n"
        text += f"👤 Ism: {order.user_info.get('name', 'Noma’lum')}\n"
        text += f"📞 Telefon: {order.user_info.get('phone', 'Noma’lum')}\n"
        text += f"📍 Manzil: {order.user_info.get('address', 'Noma’lum')}\n"
        text += "📦 Mahsulotlar:\n"
        for name, qty in order.items.items():
            text += f"  • {name} x {qty}\n"
        text += "\n"
    await query.edit_message_text(text)

async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    data = query.data

    if data == "show_categories":
        await show_categories(update, context)

    elif data == "show_cart":
        await show_cart(update, context)

    elif data == "history":
        await show_history(update, context)

    elif data.startswith("category_"):
        await show_products(update, context)

    elif data.startswith("view_"):
        await view_product(update, context)

    elif data.startswith("add_"):
        parts = data.split("_")
        product_name = parts[1]
        quantity = int(parts[2]) if len(parts) > 2 else 1
        product = supermarket.product_catalog.get(product_name)
        if not product:
            await query.edit_message_text("❌ Mahsulot topilmadi.")
            return
        cart = supermarket.user_carts.setdefault(user_id, ShoppingCart())
        cart.add_item(product, quantity)
        await query.edit_message_text(
            f"✅ {product.name} ({quantity} dona) savatga qo‘shildi.",
            reply_markup=get_products_keyboard(product.category),
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
        cart = supermarket.user_carts.get(user_id)
        if not cart or cart.is_empty():
            await query.edit_message_text("🛒 Savatingiz bo‘sh.")
            return
        supermarket.user_states[user_id] = "order_name"
        await query.edit_message_text("👤 Ismingizni kiriting:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    state = supermarket.user_states.get(user_id)

    if state and state.startswith("edit_qty_"):
        product_name = state.split("_", 2)[2]
        try:
            quantity = int(text)
            cart = supermarket.user_carts.get(user_id)
            if cart:
                cart.update_quantity(product_name, quantity)
            del supermarket.user_states[user_id]
            await update.message.reply_text("✅ Miqdor yangilandi.")
            await show_cart(update, context)
        except ValueError:
            await update.message.reply_text("❌ Iltimos, raqam kiriting (masalan, 2).")

    elif state == "order_name":
        context.user_data["order_name"] = text
        supermarket.user_states[user_id] = "order_phone"
        await update.message.reply_text("📞 Telefon raqamingizni kiriting (masalan, +998901234567):")

    elif state == "order_phone":
        context.user_data["order_phone"] = text
        supermarket.user_states[user_id] = "order_address"
        await update.message.reply_text("📍 Yetkazib berish manzilini kiriting:")

    elif state == "order_address":
        cart = supermarket.user_carts.get(user_id)
        if not cart:
            await update.message.reply_text("❌ Savat bo‘sh.")
            return
        user_info = {
            "name": context.user_data["order_name"],
            "phone": context.user_data["order_phone"],
            "address": text,
        }
        order = Order(
            user_id=user_id,
            items=cart.items.copy(),
            total_price=cart.total_price(supermarket.product_catalog),
            user_info=user_info,
        )
        supermarket.orders.append(order)
        supermarket.save()
        cart.clear()
        del supermarket.user_states[user_id]
        await update.message.reply_text(
            "✅ Buyurtmangiz qabul qilindi! Tez orada siz bilan bog‘lanamiz."
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
        supermarket.product_list = [p for p in supermarket.product_list if p.name != product_name]
        supermarket.product_catalog = {p.name: p for p in supermarket.product_list}
        supermarket.categories = list(set(p.category for p in supermarket.product_list))
        supermarket.save()
        await query.edit_message_text(f"✅ {product_name} o‘chirildi.")

    elif data == "admin_orders":
        if not supermarket.orders:
            await query.edit_message_text("📜 Hali buyurtmalar yo‘q.")
            return
        text = "📜 Buyurtmalar:\n\n"
        for i, order in enumerate(supermarket.orders, 1):
            text += f"Buyurtma #{i}\n"
            text += f"👤 User ID: {order.user_id}\n"
            text += f"💰 Umumiy: {order.total_price:,} so'm\n"
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
        await update.message.reply_text("💸 Mahsulot narxini kiriting (so'mda):")

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
            name=context.user_data["add_name"],
            price=context.user_data["add_price"],
            description=context.user_data["add_description"],
            image_url=context.user_data["add_image"],
            category=text,
            discount=0,
        )
        supermarket.product_list.append(product)
        supermarket.product_catalog[product.name] = product
        supermarket.categories = list(set(p.category for p in supermarket.product_list))
        supermarket.save()
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
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_admin_message))

    print("✅ Bot ishga tushdi...")
    app.run_polling()

if __name__ == "__main__":
    main()