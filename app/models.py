from sqlalchemy import Column, Integer, String, Text, Boolean, ForeignKey, DateTime, func, UniqueConstraint
from .database import Base
from sqlalchemy.orm import relationship, selectinload

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    image = Column(String(255))
    description = Column(Text)
    stock = Column(Integer, default=0)
    price = Column(Integer, default=2500)

    # 🔥 اضافه کن
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    seller    = relationship("User", lazy="joined", foreign_keys=[seller_id])



class User(Base):
    __tablename__ = "users"

    id       = Column(Integer, primary_key=True, index=True)
    email    = Column(String(120), unique=True, index=True, nullable=False)
    fname    = Column(String(50))
    lname    = Column(String(50))
    password = Column(String(128))      # هش‌شده
    is_admin = Column(Boolean, default=False)
    balance  = Column(Integer, default=0)
    is_seller = Column(Boolean, default=False)


class CartItem(Base):
    __tablename__ = "cart_items"
    __table_args__ = (                      # جلوگیری از رکورد تکراری
        UniqueConstraint("user_id", "product_id", name="uq_user_product"),
    )

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    qty        = Column(Integer, default=1)
    added_at   = Column(DateTime, server_default=func.now())

    # 🔥 رابطه‌ها
    product = relationship("Product", lazy="joined")
    user    = relationship("User", lazy="joined")

class Order(Base):
    __tablename__ = "orders"

    id        = Column(Integer, primary_key=True, index=True)
    user_id   = Column(Integer, ForeignKey("users.id"))
    total     = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())

    user   = relationship("User", lazy="joined")
    items  = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    __tablename__ = "order_items"

    id         = Column(Integer, primary_key=True, index=True)
    order_id   = Column(Integer, ForeignKey("orders.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    qty        = Column(Integer)
    price      = Column(Integer)   # قیمت لحظهٔ خرید
    seller_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    order   = relationship("Order", back_populates="items")
    product = relationship("Product", lazy="joined")
    seller = relationship("User", lazy="joined", foreign_keys=[seller_id])

