
import json


class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, "to_dict"):
            return obj.to_dict()
        return super().default(obj)


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


class CartItem:
    def __init__(self, product, quantity):
        self.product = product
        self.quantity = quantity

    def to_dict(self):
        return {"product": self.product.to_dict(), "quantity": self.quantity}


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


class User:
    def __init__(self, name, email, phone, address, parking_info=""):  # Parkovka ma'lumoti qo'shildi
        self.name = name
        self.email = email
        self.phone = phone
        self.address = address
        self.parking_info = parking_info  # Parkovka maydonchasi uchun

    def to_dict(self):
        return self.__dict__


class Order:
    def __init__(self, user, cart, status, delivery_address, payment_method=""):  # To'lov usuli qo'shildi
        self.user = user
        self.cart = cart
        self.status = status
        self.delivery_address = delivery_address
        self.payment_method = payment_method

    def to_dict(self):
        return {"user": self.user.to_dict(), "cart": self.cart.to_dict(), "status": self.status,
                "delivery_address": self.delivery_address, "payment_method": self.payment_method}


# JSON saqlash va yuklash

def save_data(filename, data):
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False, cls=CustomEncoder)


def load_data(filename):
    try:
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        return {}


def display_menu():
    print("\nMenyudan birini tanlang:")
    print("1. Mahsulotlar ro'yxatini ko'rish")
    print("2. Savatga mahsulot qo'shish")
    print("3. Buyurtma berish")
    print("4. Tolovlar xizmati")
    print("4. Manzilingizni kiritish")
    print("5. Parkovka xizmati")
    print("6. Tolovlar xizmati")
    print("7. Commentariya yuborish")
    print("8. Chiqish")


def payment_methods():
    print("\nTo'lov usullarini tanlang:")
    print("1. Click")
    print("2. UzCard")
    print("3. Humo")
    print("4. Naqd pul")


# Misollar
products = [
    Product("Non", 5000, "Oziq-ovqat", "Toshkent Bread Factory", "2025-12-31", 50),
    Product("Sut", 12000, "Oziq-ovqat", "Toshkent Milk", "2025-06-15", 30),
    Product("Yog'", 25000, "Oziq-ovqat", "Oltin Yog'", "2025-09-10", 20),
    Product("Shakar", 18000, "Oziq-ovqat", "Shakar Zavodi", "2026-01-01", 40),
    Product("Tuz", 3000, "Oziq-ovqat", "Mahalliy", "2026-12-31", 60),
    Product("Tuxum", 12000, "Oziq-ovqat", "Parrandachilik fabrikasi", "2025-05-20", 100),
    Product("Un", 8000, "Oziq-ovqat", "Toshkent Un", "2026-12-31", 80),
    Product("Kolbasa", 45000, "Oziq-ovqat", "Meat Products", "2025-06-30", 25)
]

user = User("Abdulaziz", "abdulaziz660@gmail.com", "+998332907007", "Toshkent", "Ko'cha nomi, 12, Parkovka mavjud")
cart = ShoppingCart()
order = None

while True:
    display_menu()
    choice = input("Tanlovingizni kiriting: ")

    if choice == "1":
        for index, product in enumerate(products, start=1):
            print(f"{index}. Mahsulot: {product.name}, Narxi: {product.price} so'm, Mavjudligi: {product.stock}")
    elif choice == "2":
        product_index = int(input("Mahsulot raqamini kiriting (1-50): ")) - 1
        if 0 <= product_index < len(products):
            quantity = int(input("Nechta mahsulot qo'shmoqchisiz? "))
            cart.add_item(products[product_index], quantity)
            print(f"{quantity} ta {products[product_index].name} savatga qo'shildi!")
        else:
            print("Noto'g'ri mahsulot raqami!")
    elif choice == "3":
        if not cart.items:
            print("Sizning savatingiz bo'sh! Avval mahsulot qo'shing.")
        else:
            print("Savatdagi mahsulotlar:")
            for item in cart.items:
                print(f"{item.quantity}x {item.product.name} - {item.product.price} so'm")
            payment_methods()
            payment_choice = input("To'lov usulini tanlang: ")
            payment_options = {"1": "Click", "2": "UzCard", "3": "Humo", "4": "Naqd pul"}
            order = Order(user, cart, "Yangi", user.address, payment_options.get(payment_choice, "Noma'lum"))
            print(f"Buyurtma qabul qilindi! Yetkazib berish vaqti: taxminan 20 daqiqa. Manzil: {user.address}, Parkovka: {user.parking_info}, To'lov usuli: {order.payment_method}")
    elif choice == "4":
        payment_methods()
    elif choice == "5":
        print("Dastur tugatildi.")
        break
    else:
        print("Noto'g'ri tanlov. Qaytadan kiriting.")
