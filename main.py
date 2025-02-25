import json


class Korzinka:
    def __init__(self, name, location, working_hours, branches, services, discounts):
        self.name = name  # Do'kon nomi
        self.location = location  # Bosh ofis manzili
        self.working_hours = working_hours  # Ish vaqtlari
        self.branches = branches  # Filiallar ro'yxati
        self.services = services  # Xizmatlar (yetkazib berish, keshbek, sodiqlik kartasi)
        self.discounts = discounts  # Chegirmalar va aksiyalar
        self.products = []  # Mahsulotlar ro'yxati
        self.customers = {}  # Mijozlar va ularning bonus ballari

    def add_product(self, product_name, price, category):
        """Mahsulot qo'shish"""
        self.products.append({"name": product_name, "price": price, "category": category})

    def add_customer(self, customer_name):
        """Yangi mijoz qo'shish"""
        if customer_name not in self.customers:
            self.customers[customer_name] = 0

    def add_bonus(self, customer_name, amount):
        """Mijozga bonus qo'shish"""
        if customer_name in self.customers:
            self.customers[customer_name] += amount

    def get_info(self):
        """Supermarket haqida umumiy ma'lumot"""
        return {
            "Nomi": self.name,
            "Manzil": self.location,
            "Ish vaqti": self.working_hours,
            "Filiallar soni": len(self.branches),
            "Xizmatlar": self.services,
            "Chegirmalar": self.discounts,
        }

    def list_products(self):
        """Barcha mahsulotlarni chiqarish"""
        return self.products

    def list_customers(self):
        """Barcha mijozlar va ularning bonuslari"""
        return self.customers


# Misol sifatida supermarket yaratish
korzinka_market = Korzinka(
    name="Taqsir.Korzinka.uz",
    location="Toshkent, O'zbekiston",
    working_hours="08:00 - 23:00",
    branches=["Toshkent", "Samarqand", "Buxoro", "Farg'ona", "Andijon", "Guliston"],
    services=["Yetkazib berish", "Keshbek", "Sodiqlik kartasi"],
    discounts=["Haftalik chegirmalar", "Bayram aksiyalari"]
)

# Mahsulot qo'shish
korzinka_market.add_product("Non", 5000, "Oziq-ovqat")
korzinka_market.add_product("Sut", 12000, "Ichimlik")
korzinka_market.add_product("Shakar", 15000, "Oziq-ovqat")

# Mijoz qo'shish va bonus berish
korzinka_market.add_customer("Abdulaziz")
korzinka_market.add_bonus("Abdulaziz", 1000)


# Ma'lumotlarni chiqarish
def print_beautiful_data():
    print(json.dumps(korzinka_market.get_info(), indent=4, ensure_ascii=False))
    print("\nMahsulotlar:")
    for product in korzinka_market.list_products():
        print(f"- {product['name']} ({product['category']}): {product['price']} so'm")
    print("\nMijozlar va bonuslari:")
    for customer, bonus in korzinka_market.list_customers().items():
        print(f"- {customer}: {bonus} bonus ball")


print_beautiful_data()
