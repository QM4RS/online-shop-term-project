from random import randint
from app.database import engine, Base, SessionLocal
from app.models import Product, User
from app.utils import hash_password

# ساخت جداول (در صورت عدم وجود)
Base.metadata.create_all(bind=engine)

# لیست اولیه محصولات با نام فایل و توضیحات
raw_products = [
    {"file_name": "Nestle-PureLife-1.5L-6pack", "description": "بطری آب آشامیدنی نستله سری پیور لایف بسته ۶ عددی"},
    {"file_name": "Miwa-Water-1.5L-6pack", "description": "آب معدنی میوا بسته ۶ عددی ۱.۵ لیتری"},
    {"file_name": "Frederique-Constant-FC-303N4NH6B", "description": "ساعت مچی اتوماتیک مردانه فردریک کنستانت"},
    {"file_name": "Patek-Philippe-Nautilus-586899NG03", "description": "ساعت مچی کوارتز مردانه مدل پتک فیلیپ ناتیلوس"},
    {"file_name": "Timex-TW2V64700UL", "description": "ساعت مچی کوارتز مردانه تایمکس"},
    {"file_name": "Almas-Daneh-Sugar-1kg", "description": "شکر سفید الماس دانه ۱ کیلوگرم"},
    {"file_name": "Suprabion-Multivitamin-Men-30tab", "description": "قرص مولتی ویتامین مینرال آقایان سوپرابیون"},
    {"file_name": "Acer-Nitro5-AN515-58-RTX4050", "description": "لپ‌تاپ گیمینگ ایسر نیترو 5 با کارت گرافیک RTX 4050"},
    {"file_name": "Asus-VivobookPro15-Q533MJ-RTX3050", "description": "لپ‌تاپ ایسوس ویووبوک پرو ۱۵ با کارت گرافیک RTX 3050"},
    {"file_name": "Monster-NLite-203-AirLinks", "description": "هدفون بلوتوثی مانستر مدل N-Lite 203"},
    {"file_name": "Apovital-VitaminC-1000mg-20tab", "description": "ویتامین C 1000 میلی‌گرم آپوویتال بسته 20 عددی"},
    {"file_name": "XEnergy-Powerbank-X828M-20000mAh", "description": "پاوربانک ایکس انرژی مدل X-828M ظرفیت 20000 میلی‌آمپر"},
    {"file_name": "Softlan-GoldSelection-500g", "description": "پودر ماشین لباسشویی سافتلن سری Gold Selection"},
    {"file_name": "ArtVina-Sunscreen-SPF50-50ml", "description": "کرم ضد آفتاب رنگی آرت وینا SPF 50 مناسب انواع پوست"},
    {"file_name": "Mahfel-Tuna-180g", "description": "کنسرو تن ماهی محفل ۱۸۰ گرمی (در روغن گیاهی)"},
    {"file_name": "Realme-Note50-256GB-4GB", "description": "گوشی موبایل ریلمی Note 50 دو سیم کارت ظرفیت 256 گیگابایت"},
    {"file_name": "Samsung-Galaxy-A06-64GB-4GB", "description": "گوشی موبایل سامسونگ Galaxy A06 دو سیم کارت ظرفیت 64 گیگابایت"},
    {"file_name": "Samsung-Galaxy-A16-128GB-4GB", "description": "گوشی موبایل سامسونگ Galaxy A16 نسخه ویتنام دو سیم کارت ظرفیت 128 گیگابایت"},
    {"file_name": "Nokia-150-2023-Iran", "description": "گوشی موبایل نوکیا مدل 150 نسخه 2023 مونتاژ ایران"},
    {"file_name": "Dell-Inspiron-3520-i5", "description": "لپ‌تاپ دل اینسپایرون 3520 با پردازنده Core i5"},
    {"file_name": "Sony-WF-C500", "description": "هدفون بی‌سیم سونی مدل WF-C500"},
    {"file_name": "Persil-Liquid-3L", "description": "مایع لباسشویی پرسیل ۳ لیتری"},
    {"file_name": "Shir-Dood-Pasteurized-1L", "description": "شیر پاستوریزه دُود ۱ لیتری"},
    {"file_name": "Samsung-Galaxy-A55-128GB-6GB", "description": "گوشی سامسونگ Galaxy A55 نسخه ویتنام (6 / ۱۲۸ GB)"},
    {"file_name": "Apple-iphone-13-promax-128GB-6GB", "description": " گوشی آیفون 13 پرومکس ریجستر شده "},
    {"file_name": "Xiaomi-redmi-note-14-128GB-8GB", "description":  "گوشی شیائومی ردمی نوت14"},
    {"file_name": "Xiaomi-redmi-note-14-128GB-8GB", "description":  "هدفون بلوتوثی انکرمدل مناسب بازی کردن A3946 "},
    {"file_name": "ِDoll-Labobo", "description":  "عروسک لبوبو در انواع رنگ ها (قد = 18سانتی متر)"},
]

# نگاشت نام انگلیسی به نام فارسی
PERSIAN_NAMES = {
    "Nestle-PureLife-1.5L-6pack": "آب معدنی نستله «پیور لایف» بسته ۶ عددی ۱.۵ لیتری",
    "Miwa-Water-1.5L-6pack": "آب معدنی میوا بسته ۶ عددی ۱.۵ لیتری",
    "Frederique-Constant-FC-303N4NH6B": "ساعت مردانه فردریک کنستانت مدل FC-303N4NH6B",
    "Patek-Philippe-Nautilus-586899NG03": "ساعت مردانه پتِک فیلیپ «ناتیلوس» مدل 586899NG03",
    "Timex-TW2V64700UL": "ساعت مردانه تایمکس مدل TW2V64700UL",
    "Almas-Daneh-Sugar-1kg": "شکر سفید الماس دانه ۱ کیلوگرمی",
    "Suprabion-Multivitamin-Men-30tab": "مولتی‌ویتامین مردان سوپرابیون – ۳۰ عددی",
    "Acer-Nitro5-AN515-58-RTX4050": "لپ‌تاپ گیمینگ ایسر نیترو ۵ (RTX 4050)",
    "Asus-VivobookPro15-Q533MJ-RTX3050": "لپ‌تاپ ایسوس ویووبوک پرو ۱۵ (RTX 3050)",
    "Monster-NLite-203-AirLinks": "هدفون بلوتوث مانستر مدل N-Lite 203",
    "Apovital-VitaminC-1000mg-20tab": "قرص ویتامین C آپوویتال ۱۰۰۰ میلی‌گرم – ۲۰ عددی",
    "XEnergy-Powerbank-X828M-20000mAh": "پاوربانک ایکس‌انرژی مدل X-828M ظرفیت ۲۰٬۰۰۰ میلی‌آمپر",
    "Softlan-GoldSelection-500g": "پودر ماشین لباسشویی سافتلن سری Gold Selection – ۵۰۰ گرم",
    "ArtVina-Sunscreen-SPF50-50ml": "کرم ضدآفتاب رنگی آرت‌وینا SPF 50 – ۵۰ میلی‌لیتر",
    "Mahfel-Tuna-180g": "کنسرو تن ماهی محفل ۱۸۰ گرمی (در روغن گیاهی)",
    "Realme-Note50-256GB-4GB": "گوشی ریلمی Note 50 دو سیم‌کارت (۴ / ۲۵۶ GB)",
    "Samsung-Galaxy-A06-64GB-4GB": "گوشی سامسونگ Galaxy A06 دو سیم‌کارت (۴ / ۶۴ GB)",
    "Samsung-Galaxy-A16-128GB-4GB": "گوشی سامسونگ Galaxy A16 نسخه ویتنام (۴ / ۱۲۸ GB)",
    "Nokia-150-2023-Iran": "گوشی کلاسیک نوکیا 150 (ورژن ۲۰۲۳، مونتاژ ایران)",
    "Dell-Inspiron-3520-i5": "لپ‌تاپ دل Inspiron 3520 (Core i5)",
    "Sony-WF-C500": "هدفون بی‌سیم سونی WF-C500",
    "Persil-Liquid-3L": "مایع لباسشویی پرسیل ۳ لیتری",
    "Shir-Dood-Pasteurized-1L": "شیر پاستوریزه دُود – ۱ لیتر",
    "Samsung-Galaxy-A55-128GB-6GB": "گوشی سامسونگ Galaxy A55 نسخه ویتنام (6 / ۱۲۸ GB)",
    "Apple-iphone-13-promax-128GB-6GB": " گوشی آیفون 13 پرومکس ریجستر شده (6 / ۱۲۸ GB)"و
    "Xiaomi-redmi-note-14-128GB-8GB": "گوشی شیائومی ردمی نوت14 (8 / ۱۲۸ GB)",
    "Sound-core-R50i-A3949": "هدفون بلوتوثی انکرمدل A3946",
    "ِDoll-Labobo": "عروسک لبوبو (18سانتی متر)",
}

# تولید فهرست نهایی با استوک تصادفی
sample_products = [
    {
        "name": PERSIAN_NAMES[p["file_name"]],
        "image": f"/static/images/{p['file_name']}.jpg",
        "description": p["description"],
        "stock": randint(5, 15),
    }
    for p in raw_products
]

db = SessionLocal()

# درج محصولات
for prod in sample_products:
    db.add(Product(**prod))

# در صورت نبودن ادمین، بساز
if not db.query(User).filter_by(email="admin@test.local").first():
    admin = User(
        email="admin@test.local",
        fname="ادمین",
        lname="اصلی",
        password=hash_password("admin123"),
        is_admin=True,
        balance=0,
    )
    db.add(admin)

db.commit()
db.close()
print("✅ دیتابیس با محصولات جدید و ادمین ساخته شد")
