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
class Product:
    def __init__(self, name, price, category, manufacturer, expiry_date, stock):
        self.name = name
        self.price = price
        self.category = category
        self.manufacturer = manufacturer
        self.expiry_date = expiry_date
        self.stock = stock

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
    main()